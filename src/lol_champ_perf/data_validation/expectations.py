"""
Great Expectations validation logic for lol_champ_perf domain (GX 1.10+ compatible)

GE Objects Description

1. DataContext: The main interface to a Great Expectations project.
    - It manages configuration, datasources, expectation suites, validations, and stores. Essentially, it “knows” where to find and save expectations, validations, and data docs.
2. BatchDefinition: Represents a concrete batch of data that will be validated.
    - For Pandas, this typically wraps the DataFrame and metadata required to run validations.
3. ExpectationSuite: A collection of expectations (rules) that describe the expected schema, values, or properties of data.
    - Each suite can be applied to one or more batches of data.
4. ValidationDefinition: Links a batch of data to an expectation suite and stores the configuration for running a validation.
- It is essentially a blueprint to execute validation on a specific dataset.

Valudation Rules
- Schema validation
    - Certain columns values must be unique and not null
- Rate value validation
    - columns with suffix _rate value must be between 0 and 100
- Count value validation
    - columns with suffix _count value must be greater than 0
"""

from pathlib import Path

import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite

from src.common.logger import logger
from src.lol_champ_perf.data_validation.metadata import (
    COUNT_RANGE,
    COUNT_SUFFIX,
    RATE_RANGE,
    RATE_SUFFIX,
    REQUIRED_AND_NOT_NULL_COLUMNS,
)

# ========================================================================================
# Helper Functions
# ========================================================================================


# get rate columns based on suffix
def get_rate_columns(df_columns):
    """Extract columns that end with _rate suffix"""
    return [column for column in df_columns if column.endswith(RATE_SUFFIX)]


# get count columns based on suffix
def get_count_columns(df_columns):
    """Extract columns that end with _count suffix"""
    return [column for column in df_columns if column.endswith(COUNT_SUFFIX)]


# ========================================================================================
# Validation Functions
# ========================================================================================


def add_schema_expectations(suite, df_columns):
    """
    Add basic schema validations:
    - Ensure required columns exist
    - Ensure NOT NULL constraints on required columns
    """
    for col in REQUIRED_AND_NOT_NULL_COLUMNS:
        suite.add_expectation(gx.expectations.ExpectColumnToExist(column=col))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column=col))


def add_rate_expectations(suite, df_columns):
    """
    Add rate value validations:
    - Ensure numeric rate columns fall within RATE_RANGE
    """
    rate_columns = get_rate_columns(df_columns)

    for col in rate_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=col, min_value=RATE_RANGE[0], max_value=RATE_RANGE[1]
            )
        )


def add_count_expectations(suite, df_columns):
    """
    Add count value validations:
    - Ensure numeric count columns fall within COUNT_RANGE
    """
    count_columns = get_count_columns(df_columns)

    for col in count_columns:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=col, min_value=COUNT_RANGE[0], max_value=COUNT_RANGE[1]
            )
        )


def add_primary_key_expectations(suite, df_columns):
    """
    Add uniqueness validation for primary key columns:
    - Ensures the combination of ['std_date', 'champion_name'] is unique
    """
    suite.add_expectation(
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=REQUIRED_AND_NOT_NULL_COLUMNS
        )
    )


# ========================================================================================
# Validation Rules
# ========================================================================================

# Hard Rules: Pipeline fails if any rule fails
HARD_RULES = [
    add_schema_expectations,
    add_rate_expectations,
    add_count_expectations,
    add_primary_key_expectations,
]

# Soft Rules: Pipeline continues with warnings
SOFT_RULES = [
    # Future soft rules
]

# All Rules
ALL_RULES = HARD_RULES + SOFT_RULES


# ========================================================================================
# DataContext Setup
# ========================================================================================


# Get or create DataContext
def get_or_create_context(context_root_dir="../../../gx"):
    """
    Retrieve or create a GE DataContext.
    - Provides the entry point to access datasources, suites, and stores.
    """
    context_path = Path(context_root_dir)

    context = gx.get_context(context_root_dir=str(context_path))
    logger.info("Using DataContext at %s", context_path.resolve())

    return context


# Setup Pandas Datasource and Data Asset
def setup_pandas_datasource(context, datasource_name="lol_champ_perf_source"):
    """
    Setup a Pandas Datasource and a Data Asset (runtime dataframe)
    - Datasource: abstraction over data (CSV, Pandas, SQL, etc.)
    - Asset: logical representation of a dataset to validate
    - BatchDefinition: defines which batch (slice) of data to validate
    """
    asset_name = "runtime_dataframe"

    try:
        datasource = context.data_sources.get(datasource_name)
        logger.info("Using existing datasource '%s'", datasource_name)
    except LookupError:
        datasource = context.data_sources.add_pandas(datasource_name)
        logger.info("Created datasource '%s'", datasource_name)

    try:
        asset = datasource.get_asset(asset_name)
    except LookupError:
        asset = datasource.add_dataframe_asset(name=asset_name)
        asset.add_batch_definition_whole_dataframe("default")
        logger.info("Created runtime dataframe asset")

    batch_definition = asset.get_batch_definition("default")
    return batch_definition


def get_or_create_validation_definition(context, suite, batch_definition, name):
    """
    Setup or retrieve a ValidationDefinition
    - Links the batch of data to the expectation suite
    - Stores the validation configuration for execution
    """
    validation_definition = gx.ValidationDefinition(
        name=name,
        data=batch_definition,
        suite=suite,
    )
    context.validation_definitions.add_or_update(validation_definition)
    logger.info("ValidationDefinition '%s' ready", name)
    return validation_definition


# ========================================================================================
# Main Validation Function
# ========================================================================================


def validate_dataframe(
    df: pd.DataFrame,
    suite_name: str = "lol_champ_perf_suite",
    context_root_dir: str = "../../../gx",
    rules: list = None,
    fail_on_error: bool = True,
):
    """
    Validate a DataFrame using Great Expectations (GX 1.10+)

    Args:
        df: Pandas DataFrame to validate
        suite_name: Name of the expectation suite
        context_root_dir: Path to GX context directory
        rules: List of expectation functions (default: HARD_RULES)
        fail_on_error: If False, continues on validation failure

    Returns:
        Validation result

    Main function to validate a Pandas DataFrame using GE.

    Steps:
    1. Get or create DataContext
    2. Setup Datasource and BatchDefinition for the DataFrame
    3. Get or create an ExpectationSuite
    4. Apply expectation rules (schema, rate, count, primary key)
    5. Save suite
    6. Setup ValidationDefinition
    7. Run validation and log results using logger
    """
    if rules is None:
        rules = HARD_RULES

    logger.info("\n" + "=" * 80)
    logger.info("STARTING DATA VALIDATION")
    logger.info(f"Rules: {'HARD' if fail_on_error else 'SOFT'} ({len(rules)} checks)")
    logger.info("=" * 80 + "\n")

    # 1) Setup DataContext
    logger.info("1. Setting up DataContext...")
    context = get_or_create_context(context_root_dir)

    # 2) Setup Datasource
    logger.info("\n2. Setting up Datasource...")
    batch_definition = setup_pandas_datasource(context)

    # 3) Create or get Expectation Suite and add expectations
    logger.info("\n3. Setting up Expectation Suite...")
    try:
        suite = context.suites.get(suite_name)
        logger.info(f"✓ Using existing suite '{suite_name}'")
        # Clear existing expectations to add fresh ones
        suite.expectations = []
    except:
        logger.info(f"Creating new suite '{suite_name}'...")
        suite = context.suites.add(ExpectationSuite(name=suite_name))

    # Add expectations to suite
    logger.info("\n4. Adding Expectations to Suite...")
    for rule_func in rules:
        rule_func(suite, df.columns)
        logger.info(f"✓ Applied: {rule_func.__name__}")

    # Save suite
    context.suites.add_or_update(suite)
    logger.info(f"✓ Suite saved with {len(suite.expectations)} expectations")

    # 5) Create Validation Definition
    logger.info("\n5. Setting up Validation Definition...")
    validation_def_name = f"{suite_name}_validation"
    validation_definition = get_or_create_validation_definition(
        context, suite, batch_definition, validation_def_name
    )
    logger.info(f"✓ Validation definition created")

    # 6) Run Validation
    logger.info("\n6. Running Validation...")
    logger.info("-" * 80)
    result = validation_definition.run(
        batch_parameters={"dataframe": df}, result_format={"result_format": "SUMMARY"}
    )
    logger.info(f"✓ Validation run completed")

    # 7) Print Results
    _print_validation_results(result, fail_on_error)

    # 8) Handle failure if hard rules and validation failed
    if fail_on_error and not result.success:
        raise RuntimeError(
            f"Great Expectations validation for {df['champion_name'].unique()} failed"
        )

    return result


def _print_validation_results(result, fail_on_error=True):
    logger.info("=" * 80)
    logger.info("VALIDATION RESULTS")
    logger.info("=" * 80)

    logger.info("Success: %s", result.success)

    stats = getattr(result, "statistics", {})
    logger.info(
        "Evaluated=%s | Passed=%s | Failed=%s | SuccessRate=%.2f%%",
        stats.get("evaluated_expectations"),
        stats.get("successful_expectations"),
        stats.get("unsuccessful_expectations"),
        stats.get("success_percent", 0.0),
    )

    if result.success:
        logger.info("✓ All validations passed")
        logger.info("=" * 80)
        return

    severity_logger = logger.error if fail_on_error else logger.warning
    severity_logger("Validation failed – detailed failed expectations below")

    for r in result.results:
        if r.success:
            continue

        config = r.expectation_config
        kwargs = config.kwargs

        severity_logger("-" * 80)
        severity_logger("Expectation Type : %s", config.expectation_context)
        severity_logger("Column           : %s", kwargs.get("column"))

        # Expected condition
        severity_logger("Expected:")
        for k, v in kwargs.items():
            severity_logger("  - %s: %s", k, v)

        # Observed result
        severity_logger("Observed:")
        for k, v in r.result.items():
            if k == "partial_unexpected_counts":
                severity_logger("  - %s: %s", k, v)

    logger.info("=" * 80)
