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


# python operator to fetch all tier data
@task
def fetch_all_champion_tier(tier: str, position: str, region: str) -> pd.DataFrame:
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

        return champion_df
    except Exception as e:
        logger.error(f"Failed to fetch page for {champion}: {e}")
        return pd.DataFrame()
