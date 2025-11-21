import requests
import pandas as pd
from bs4 import BeautifulSoup
from src.common.logger import logger
from src.common.file_handler import save_df_to_parquet
from src.common.config import LOL_CHAMP_PERF_FILE_DIR
import time


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
            data.append({
                "rank": rank,
                "champion": champion,
                "win_rate": win_rate,
                "pick_rate": pick_rate,
                "ban_rate": ban_rate,
                "weak_against": weak_list
            })

        except Exception as e:
            logger.warning(f"Failed to parse row {idx}: {e}")
            continue  # Skip problematic row

    # Step 4: Convert to DataFrame
    df = pd.DataFrame(data)
    logger.info(f"Extracted {len(df)} champions from the page")

    # Step 5: Save raw data to parquet for later GE validation
    try:
        save_df_to_parquet(df, LOL_CHAMP_PERF_FILE_DIR, f"champion_perf_{tier}_{position}_{region}.parquet")
        logger.info("Saved raw champion data for GE validation")
    except Exception as e:
        logger.error(f"Failed to save DataFrame: {e}")

    return df