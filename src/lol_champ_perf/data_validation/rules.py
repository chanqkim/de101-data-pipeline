from expectations import (
    add_rate_expectations,
    add_schema_expectations,
)

"""
Hard validation rules for lol_champ_perf domain.

- if any hard rule fails, the pipeline should fail
- requirements are based on metadata
"""
HARD_RULES = [
    add_schema_expectations,
    add_rate_expectations,
]

# Not Used Yet
SOFT_RULES = [
    # distribution checks later
]
