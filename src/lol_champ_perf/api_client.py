import requests
import pandas as pd 
import logging
from src.common.file_handler import save_df_to_parquet
from src.common.config import LOL_CHAMP_PERF_FILE_DIR
logger = logging.getLogger()


def fetch_json_from_url(url: str):
    """
    Fetch JSON data from the given URL.
    Returns None if the request fails, and logs the error.

    Args:
        url (str): The URL to fetch JSON from.

    Returns:
        dict/list/None: JSON data if successful, None if failed.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JSON from {url}: {e}")
        return None

def get_lol_champ_data():
    
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    
    # get version_lists:  ['15.23.1', '15.22.1', ...]
    versions_list = fetch_json_from_url(versions_url)
    
    
    # first item is the recent version
    latest_version = versions_list[0]  
    logger.info(f'Retrived lol latest version: {latest_version}')
    

    recent_champions_url = f"http://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
    champions_data = fetch_json_from_url(recent_champions_url)

    # create dataframe from champions data
    champ_df = pd.DataFrame(champions_data['data']).T
    champ_df.index = champ_df['name']
    champ_df = champ_df.drop(columns=['name'])

    # saving file to parquet
    file_name = f"{latest_version.replace('.','_')}_lol_champion.parquet"
    save_df_to_parquet(champ_df, path = LOL_CHAMP_PERF_FILE_DIR, file_name = file_name)
    logger.info(f"champion file saved! path: {LOL_CHAMP_PERF_FILE_DIR}/{file_name}")

get_lol_champ_data()