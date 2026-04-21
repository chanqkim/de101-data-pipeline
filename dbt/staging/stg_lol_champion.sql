{{ config(materialized='view') }}

SELECT
    LOWER(champion) AS champion,
    CAST(date AS DATE) AS date,
    CAST(win_rate AS DOUBLE) AS win_rate
FROM read_parquet(
    's3://your-bucket/lol_champion/*.parquet'
)