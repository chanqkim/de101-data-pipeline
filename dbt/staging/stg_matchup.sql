{{ config(materialized='view') }}

SELECT
    LOWER(champion) AS champion,
    LOWER(opponent) AS opponent,
    CAST(difficulty AS DOUBLE) AS difficulty,
    CAST(std_date AS DATE) AS std_date
FROM read_parquet(
    's3://your-bucket/matchup/*/*.parquet',
    hive_partitioning = true
)