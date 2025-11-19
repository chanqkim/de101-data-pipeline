from src.common.logger import logger
import os 

def save_df_to_parquet(df, path: str, file_name: str):

    # create new path for saving file if path does not exist
    os.makedirs(path, exist_ok=True)
    print(f"{path}/{file_name}")
    try:
        df.to_parquet(f"{path}/{file_name}", engine="pyarrow", index=False)
        logger.info(f"Parquet saved to {path}")
    except Exception as e:
        logger.error(f"Failed to save Parquet to {path}: {e}")
        raise