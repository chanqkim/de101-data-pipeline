import time

import pandas as pd
import requests
from airflow.decorators import dag, task
from bs4 import BeautifulSoup

from src.common.config import LOL_CHAMP_PERF_FILE_DIR
from src.common.file_handler import save_df_to_parquet
from src.common.logger import logger


# extract champion pick rate, ban rate, and win rate
def fetch_champ_win_ban_pic_rate(soup: BeautifulSoup) -> dict:
    """
    Extract champion pick rate, ban rate, and win rate from the BeautifulSoup object.
    Returns a dictionary with keys: 'pick_rate', 'ban_rate', 'win_rate'.
    """
    result = {}
    try:
        ul_element = soup.select_one(
            "#content-header > div.min-h-\\[225px\\].bg-gray-0 > div > "
            "div.w-full.content-center.p-\\[12px\\].md\\:w-\\[651px\\].md\\:p-0 > ul"
        )

        if ul_element:
            li_elements = ul_element.select("li")
            for li in li_elements:
                em = li.select_one("em")
                if em:
                    label_text = em.get_text(strip=True)  # "51.2%"
                    value_text = li.get_text(strip=True).replace(label_text, "").strip()
                    # convert label to snake_case
                    label = label_text.lower().replace(" ", "_")
                    result[label] = value_text

        logger.info(f"Extracted champ rates: {result}")
    except Exception as e:
        logger.error(f"Failed to extract champ rates: {e}")

    return result


# extract detailed champion build data
def fetch_champion_item_builds(soup: BeautifulSoup, chamption_name: str) -> list:
    """
    Fetch detailed champion build data from OP.GG in long format:
    - Each item in each build = 1 row
    - Columns: champion, build_index, item_index, item_name, pick_rate, game_count, win_rate
    """

    records = []

    try:
        table = soup.select_one(
            "#content-container > div > div.gap-2.md\\:mx-auto.md\\:w-width-limit.flex.flex-col.md\\:flex-row > "
            "div.flex.flex-1.flex-col.gap-2.md\\:w-\\[740px\\] > "
            "div.md\\:flex.md\\:flex-col.md\\:gap-2 > section:nth-child(3) > div.flex.items-center.justify-between > div > table"
        )

        records = []

        if table:
            rows = table.select("tbody tr")
            record = {"champion_name": chamption_name}

            for build_index, row in enumerate(rows, start=1):
                # get item names
                item_imgs = row.select("td:nth-of-type(1) img")
                items = [img.get("alt") for img in item_imgs]
                while len(items) < 3:  # get 3 items maximum
                    items.append(None)

                # pick_rate, game_count, win_rate
                pick_rate_text = row.select_one("td:nth-of-type(2) strong").get_text(
                    strip=True
                )
                pick_rate = float(pick_rate_text.replace("%", ""))
                game_count_text = row.select_one("td:nth-of-type(2) span").get_text(
                    strip=True
                )
                game_count = int(
                    game_count_text.replace("Games", "").replace(",", "").strip()
                )
                win_rate_text = row.select_one("td:nth-of-type(3) strong").get_text(
                    strip=True
                )
                win_rate = float(win_rate_text.replace("%", ""))

                # widen the item builds to keep one champion per row
                for idx, item_name in enumerate(items, start=1):
                    record[f"build{build_index}_item{idx}"] = item_name

                record[f"build{build_index}_pick_rate"] = pick_rate
                record[f"build{build_index}_game_count"] = game_count
                record[f"build{build_index}_win_rate"] = win_rate

            records.append(record)

    except Exception as e:
        logger.error(f"Failed to fetch champion builds for {chamption_name}: {e}")

    logger.info(f"Fetched {len(records)} rows of champion item builds")
    return records


# get weak and strong champion counters
def fetch_champ_counters_to_df(
    soup: BeautifulSoup, dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Extract weak and strong champion counters from the BeautifulSoup object.
    Returns a dictionary with weak and strong champions along with their win rates and game counts.
    """

    try:
        weak_strong_section = soup.select_one(
            "#content-container > div > div.gap-2.md\\:mx-auto.md\\:w-width-limit.flex.flex-col.md\\:flex-row > "
            "div.flex.flex-col.gap-2.md\\:basis-\\[332px\\] > section:nth-child(1)"
        )

        weak_champs = []
        strong_champs = []

        if weak_strong_section:
            ul_list = weak_strong_section.select("ul")

            # get weak champion: first ul
            if len(ul_list) >= 1:
                for li in ul_list[0].select("li"):
                    img = li.select_one("img")
                    strong_tag = li.select_one("strong")
                    span_game = li.select(
                        "span.flex.flex-col.items-center.justify-center.text-gray-500 span"
                    )
                    if img and strong_tag and span_game:
                        champ_name = img.get("alt")
                        win_rate = float(
                            strong_tag.get_text(strip=True).replace("%", "")
                        )
                        game_count = int(
                            span_game[0].get_text(strip=True).replace(",", "")
                        )
                        weak_champs.append((champ_name, win_rate, game_count))

            # strong chamption: 2nd ul
            if len(ul_list) >= 2:
                for li in ul_list[1].select("li"):
                    img = li.select_one("img")
                    strong_tag = li.select_one("strong")
                    span_game = li.select(
                        "span.flex.flex-col.items-center.justify-center.text-gray-500 span"
                    )
                    if img and strong_tag and span_game:
                        champ_name = img.get("alt")
                        win_rate = float(
                            strong_tag.get_text(strip=True).replace("%", "")
                        )
                        game_count = int(
                            span_game[0].get_text(strip=True).replace(",", "")
                        )
                        strong_champs.append((champ_name, win_rate, game_count))

        # add weak, strong champion data to the dataframe(maximum 5 champs, if not exist, None)
        for i in range(5):
            if i < len(weak_champs):
                dataframe[f"weak_champ_name{i + 1}"] = [weak_champs[i][0]] * len(
                    dataframe
                )
                dataframe[f"weak_champ{i + 1}_winrate"] = [weak_champs[i][1]] * len(
                    dataframe
                )
                dataframe[f"weak_champ{i + 1}_gamecount"] = [weak_champs[i][2]] * len(
                    dataframe
                )
            else:
                dataframe[f"weak_champ_name{i + 1}"] = [None] * len(dataframe)
                dataframe[f"weak_champ{i + 1}_winrate"] = [None] * len(dataframe)
                dataframe[f"weak_champ{i + 1}_gamecount"] = [None] * len(dataframe)

        for i in range(5):
            if i < len(strong_champs):
                dataframe[f"strong_champ_name{i + 1}"] = [strong_champs[i][0]] * len(
                    dataframe
                )
                dataframe[f"strong_champ{i + 1}_winrate"] = [strong_champs[i][1]] * len(
                    dataframe
                )
                dataframe[f"strong_champ{i + 1}_gamecount"] = [
                    strong_champs[i][2]
                ] * len(dataframe)
            else:
                dataframe[f"strong_champ_name{i + 1}"] = [None] * len(dataframe)
                dataframe[f"strong_champ{i + 1}_winrate"] = [None] * len(dataframe)
                dataframe[f"strong_champ{i + 1}_gamecount"] = [None] * len(dataframe)
        return dataframe

    except Exception as e:
        logger.error(f"Failed to extract champ counters: {e}")


# spilit champion build data into fact tables
def split_fetch_champion_build_data_into_fact_tables(df: pd.DataFrame):
    """
    Split the champion build data DataFrame into multiple fact tables for star schema.

    Fact 1: Champion daily meta statistics
        Table: fact_lol_champion_meta_daily
        Columns: std_date, champion_name, overall_pick_rate, overall_ban_rate, overall_win_rate

    Fact 2: Champion daily top 5 item builds
        Table: fact_lol_champion_top5_builds_daily
        Columns: std_date, champion_name, build_rank (1~5), build_item1~3, build_pick_rate, build_win_rate, build_game_count

    Fact 3: Champion daily top 5 easy/hard matchups
        Table: fact_lol_champion_daily_top5_easy_hard_matchups
        Columns: std_date, champion_name,
                 weak_champ_name1~5, weak_champ1~5_winrate, weak_champ1~5_gamecount,
                 strong_champ_name1~5, strong_champ1~5_winrate, strong_champ1~5_gamecount
    """

    champion_name = df["champion_name"].iloc[0]

    df_list = []

    # Fact 1: Daily champion meta statistics
    fact_df1 = df[
        [
            "std_date",
            "champion_name",
            "overall_pick_rate",
            "overall_ban_rate",
            "overall_win_rate",
        ]
    ]
    df_list.append(fact_df1)

    # Fact 2: Top 5 item builds
    fact_df2 = df[
        [
            "std_date",
            "champion_name",
            "build1_item1",
            "build1_item2",
            "build1_item3",
            "build1_game_count",
            "build1_pick_rate",
            "build1_win_rate",
            "build2_item1",
            "build2_item2",
            "build2_item3",
            "build2_game_count",
            "build2_pick_rate",
            "build2_win_rate",
            "build3_item1",
            "build3_item2",
            "build3_item3",
            "build3_game_count",
            "build3_pick_rate",
            "build3_win_rate",
            "build4_item1",
            "build4_item2",
            "build4_item3",
            "build4_game_count",
            "build4_pick_rate",
            "build4_win_rate",
            "build5_item1",
            "build5_item2",
            "build5_item3",
            "build5_game_count",
            "build5_pick_rate",
            "build5_win_rate",
        ]
    ]
    df_list.append(fact_df2)

    # Fact 3: Top 5 easy/hard matchups
    fact_df3 = df[
        [
            "std_date",
            "champion_name",
            "weak_champ_name1",
            "weak_champ1_winrate",
            "weak_champ1_gamecount",
            "weak_champ_name2",
            "weak_champ2_winrate",
            "weak_champ2_gamecount",
            "weak_champ_name3",
            "weak_champ3_winrate",
            "weak_champ3_gamecount",
            "weak_champ_name4",
            "weak_champ4_winrate",
            "weak_champ4_gamecount",
            "weak_champ_name5",
            "weak_champ5_winrate",
            "weak_champ5_gamecount",
            "strong_champ_name1",
            "strong_champ1_winrate",
            "strong_champ1_gamecount",
            "strong_champ_name2",
            "strong_champ2_winrate",
            "strong_champ2_gamecount",
            "strong_champ_name3",
            "strong_champ3_winrate",
            "strong_champ3_gamecount",
            "strong_champ_name4",
            "strong_champ4_winrate",
            "strong_champ4_gamecount",
            "strong_champ_name5",
            "strong_champ5_winrate",
            "strong_champ5_gamecount",
        ]
    ]
    df_list.append(fact_df3)

    table_name_list = [
        "fact_lol_champion_meta_daily",
        "fact_lol_champion_top5_builds_daily",
        "fact_lol_champion_daily_top5_easy_hard_matchups",
    ]

    # Save each fact table to parquet with std_date in the filename
    for i, fact_df in enumerate(df_list):
        table_name = table_name_list[i]

        try:
            # If std_date column exists, get first value (assumes all rows same date)
            std_date_str = (
                fact_df["std_date"].iloc[0]
                if "std_date" in fact_df.columns
                else "unknown_date"
            )
            file_name = f"{table_name}_{champion_name}_{std_date_str}.parquet"

            save_df_to_parquet(fact_df, LOL_CHAMP_PERF_FILE_DIR, file_name)
            logger.info(f"Saved fact table {table_name} to {file_name}")
        except Exception as e:
            logger.error(f"Failed to save fact table {table_name}: {e}")


def fetch_champion_synergies(
    champion: str, tier: str = "all", region: str = "global", std_date: str = "unknown"
):
    """
    Fetch champion synergies from OP.GG and an save wide format parquet file.
    """
    url = (
        f"https://op.gg/lol/champions/{champion}/synergies?tier={tier}&region={region}"
    )
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    # select entire section containing position synergy information
    sections = soup.select("#content-container > div > section")

    # loop through sections to extract synergy data
    for sec in sections:
        # get position name
        header_div = sec.select_one(
            "div.relative.flex.items-center.justify-between > div.px-3.py-2"
        )
        pos_name = (
            header_div.text.strip().replace("Synergies with ", "").lower()
            if header_div
            else "unknown"
        )

        # select tbody containing synergy champion data
        tbody = sec.select_one("table > tbody")
        if not tbody:
            continue

        # loop through each row to extract synergy champion data
        for row in tbody.select("tr"):
            synergy_champion_name = row.select_one("td a strong").text.strip()
            pick_rate = row.select("td")[1].select_one("strong").text.strip()
            pick_count = row.select("td")[1].select_one("div").text.strip()
            win_rate = row.select("td")[2].select_one("strong").text.strip()

            results.append(
                {
                    "position": pos_name,
                    "synergy_champion_name": synergy_champion_name,
                    "pick_rate": pick_rate,
                    "pick_count": pick_count,
                    "win_rate": win_rate,
                }
            )

    # create dataframe from results
    df = pd.DataFrame(results)

    # create champion_name column for merging later
    df["champion_name"] = champion

    # sort chamption list with pick rate descending order and assign rank
    df["pick_rate_float"] = df["pick_rate"].str.rstrip("%").astype(float)

    df["rank"] = (
        df.sort_values(
            ["champion_name", "position", "pick_rate_float"],
            ascending=[True, True, False],
        )
        .groupby(["champion_name", "position"])
        .cumcount()
        + 1
    )

    # use pivot table to transform long dataframe to wide format
    df_wide = df.pivot_table(
        index="champion_name",
        columns=["position", "rank"],
        values=["synergy_champion_name", "pick_rate", "pick_count", "win_rate"],
        aggfunc="first",
    )

    # flatten columns
    df_wide.columns = [f"{pos}_rank{rank}_{val}" for val, pos, rank in df_wide.columns]
    df_wide.reset_index(inplace=True)

    # add std_date column
    df_wide["std_date"] = std_date
    file_name = f"fact_lol_{champion}_synergies_daily_{std_date}.parquet"

    # save to parquet
    try:
        save_df_to_parquet(df_wide, LOL_CHAMP_PERF_FILE_DIR, file_name)
        logger.info(f"Saved {file_name}")
    except Exception as e:
        logger.error(f"Failed to save {file_name}: {e}")


# python operator to fetch all tier data
@task
def fetch_all_champion_tier(
    tier: str = "all", position: str = "all", region: str = "global"
) -> pd.DataFrame:
    """
    Crawl OP.GG to fetch champion data for a specific tier, position, and region.

    Data includes:
        - Rank
        - Champion name
        - Win rate
        - Pick rate
        - Ban rate
        - Weak against champions (list)

    Returns:
        pd.DataFrame: Raw champion performance data suitable for later
        Great Expectations quality checks.
    """

    # target url
    url = f"https://op.gg/lol/champions?tier={tier}&position={position}&region={region}"
    logger.info(f"Requesting page: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Step 1: Fetch HTML and parse
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logger.error(f"Failed to fetch or parse page: {e}")
        return pd.DataFrame()

    # Step 2: Extract table rows
    rows = soup.select("table tbody tr")
    data = []

    # Step 3: Loop over each row and extract data with row-level try-except
    for idx, row in enumerate(rows, 1):
        try:
            tds = row.find_all("td")
            if len(tds) < 8:
                logger.warning(f"Skipping row {idx} due to insufficient columns")
                continue

            # Extract Rank
            rank = tds[0].get_text(strip=True)

            # Extract Champion name
            champion = tds[1].select_one("strong").get_text(strip=True)

            # Extract Win, Pick, Ban rates (remove %)
            win_rate = tds[4].get_text(strip=True).replace("%", "")
            pick_rate = tds[5].get_text(strip=True).replace("%", "")
            ban_rate = tds[6].get_text(strip=True).replace("%", "")

            # Extract Weak Against champions
            weak_list = []
            weak_items = tds[7].select("li img")
            for img in weak_items:
                weak_list.append(img.get("alt"))

            # Append extracted data
            data.append(
                {
                    "rank": rank,
                    "champion": champion,
                    "win_rate": win_rate,
                    "pick_rate": pick_rate,
                    "ban_rate": ban_rate,
                    "weak_against": weak_list,
                }
            )

        except Exception as e:
            logger.warning(f"Failed to parse row {idx}: {e}")
            continue  # Skip problematic row

    # Step 4: Convert to DataFrame
    df = pd.DataFrame(data)
    logger.info(f"Extracted {len(df)} champions from the page")

    # Step 5: Save raw data to parquet for later GE validation
    try:
        save_df_to_parquet(
            df,
            LOL_CHAMP_PERF_FILE_DIR,
            f"champion_perf_{tier}_{position}_{region}.parquet",
        )
        logger.info("Saved raw champion data for GE validation")
    except Exception as e:
        logger.error(f"Failed to save DataFrame: {e}")

    return df


# python operator to fetch champion build data in wide format
@task
def fetch_champion_build_data(
    champion: str, tier: str = "all", region: str = "all"
) -> pd.DataFrame:
    """
    Fetch detailed champion build data from OP.GG in wide format:
    - Each champion = 1 row
    - Data includes:
        - Champion name
        - Win rate
        - Pick rate
        - Ban rate
        - Item builds (up to 3 items per build, multiple builds)
        - Weak / Strong champions (list)

    """

    url = f"https://op.gg/lol/champions/{champion}/build?tier={tier}&region={region}"
    logger.info(f"Requesting champion build page: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # pic, win rate, game count
        champ_pic_ban_win_data = fetch_champ_win_ban_pic_rate(soup)

        print(
            f"Fetched {champion} build data - Pick Rate: {champ_pic_ban_win_data['pick_rate']}, Ban Rate: {champ_pic_ban_win_data['ban_rate']}, Win Rate: {champ_pic_ban_win_data['win_rate']}"
        )

        # --- Core Builds table ---
        champion_records = fetch_champion_item_builds(soup, champion)

        # add strong, weak champions
        champion_df = pd.DataFrame(champion_records)
        champion_df = fetch_champ_counters_to_df(soup=soup, dataframe=champion_df)

        # add overall pick, win rate, game count
        champion_df["overall_pick_rate"] = champ_pic_ban_win_data.get("pick_rate")
        champion_df["overall_ban_rate"] = champ_pic_ban_win_data.get("ban_rate")
        champion_df["overall_win_rate"] = champ_pic_ban_win_data.get("win_rate")

        # add std_date: crawl date
        std_date = pd.to_datetime("today").strftime("%Y-%m-%d")
        champion_df["std_date"] = std_date

        # split dataframe into fact table dataframes
        split_fetch_champion_build_data_into_fact_tables(champion_df)

        # crawll champion synergies and save wide format parquet
        fetch_champion_synergies(
            champion=champion, tier=tier, region=region, std_date=std_date
        )

        return champion_df
    except Exception as e:
        logger.error(f"Failed to fetch page for {champion}: {e}")
        return pd.DataFrame()
