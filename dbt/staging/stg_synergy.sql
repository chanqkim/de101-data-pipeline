{{ config(materialized='view') }}

SELECT
    LOWER(champion) AS champion,
    LOWER(partner) AS partner,
    CAST(win_rate AS DOUBLE) AS win_rate,
    CAST(date AS DATE) AS date
FROM read_parquet(
    's3://your-bucket/synergy/*/*.parquet',
    hive_partitioning = true
)