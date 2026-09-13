import json
import great_expectations as gx
from great_expectations.core.batch import BatchRequest
from datetime import datetime
from config import GX_ROOT, RULES_CONFIG_PATH, PLUGINS_DIR
import sys
sys.path.insert(0, PLUGINS_DIR)
import expect_end_date_after_start_date

with open(RULES_CONFIG_PATH) as f:
    config = json.load(f)

context = gx.get_context(context_root_dir=GX_ROOT)

DATE_AND_TIMESTAMP_COLUMNS = {
    "transaction_date",
    "date_of_birth",
    "start_date",
    "end_date",
    "created_at",
    "updated_at",
}


def normalize_expectation(expectation):
    """Use the supported timestamp-aware expectation for date columns instead of regex on a timestamp type."""
    if expectation.get("type") == "expect_column_values_to_match_regex":
        column_name = expectation.get("column")
        if column_name in DATE_AND_TIMESTAMP_COLUMNS:
            regex_value = expectation.get("regex")
            if regex_value and regex_value.startswith("^") and "\\d{4}-\\d{2}-\\d{2}" in regex_value:
                return {
                    "type": "expect_column_values_to_match_strftime_format",
                    "column": column_name,
                    "strftime_format": "%Y-%m-%d",
                }
    return expectation


for table in config["tables"]:
    suite_name = table["suite_name"]
    table_name = table["table_name"]

    suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)

    # get validator
    batch_request = BatchRequest(
    datasource_name=config["datasource_name"],
    data_connector_name=config["data_connector_name"],
    data_asset_name=table_name
    )

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name
    )

    print(f"Validator ready for: {table_name}")
    
    for expectations in table["expectations"]:
        expectation = normalize_expectation(expectations)

        if expectation["type"] == "SKIP_custom":
            print(f"Skipping: {expectation.get('comment', '')}")
            continue

        if expectation.get("max_value") == "today":
            expectation["max_value"] = datetime.now().isoformat()
        if expectation.get("min_value") == "today":
            expectation["min_value"] = datetime.now().isoformat()

        params = {k: v for k, v in expectation.items() if k != "type"}
        expectation_fn = getattr(validator, expectation["type"])
        expectation_fn(**params)

    validator.save_expectation_suite(discard_failed_expectations=False)
    print(f"Suite saved: {suite_name}")
	