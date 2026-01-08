"""
Metadata for lol_champ_perf domain

- Suffix-based semantic contracts
- Pattern-based NOT NULL enforcement for build columns
"""

# ==================================================
# Required/Not Null Columns
# ==================================================
# these columns must be present in the dataset and values must not be null
NOT_NULL_COLUMNS = [
    # primary keys (std_date, champion_name)
    "std_date",
    "champion_name",
]

# ==================================================
# Column Naming Contracts
# ==================================================

RATE_SUFFIX = "_rate"
COUNT_SUFFIX = "_count"

# ==================================================
# Build-related Naming Contracts
# ==================================================

# build1 ~ build3
# at least 3 builds value must be present
BUILD_ITEM_IDEXES = [1, 2, 3]

# ==================================================
# Value Ranges
# ==================================================

RATE_RANGE = (0.0, 100.0)
COUNT_RANGE = (0, None)  # >= 0


# ==================================================
# Derived NOT NULL Rules (Pattern-based)
# ==================================================
def get_build_not_null_columns():
    """
    buildX_itemY
    buildX_pick_rate
    buildX_game_count
    buildX_win_rate
    """
    cols = []

    for index in BUILD_ITEM_IDEXES:
        # metric columns
        cols.extend(
            [
                f"build{index}_item{index}",
                f"build{index}_pick_rate",
                f"build{index}_game_count",
                f"build{index}_win_rate",
            ]
        )

    return cols


# Final NOT NULL column list (single source of truth)
REQUIRED_AND_NOT_NULL_COLUMNS = NOT_NULL_COLUMNS + get_build_not_null_columns()
