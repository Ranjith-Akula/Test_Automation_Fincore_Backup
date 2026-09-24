import json
import great_expectations as gx
from great_expectations.core.batch import BatchRequest
from config import GX_ROOT, RULES_CONFIG_PATH, PLUGINS_DIR
import sys
sys.path.insert(0, PLUGINS_DIR)
import expect_end_date_after_start_date

with open(RULES_CONFIG_PATH) as f:
    config = json.load(f)

context = gx.get_context(context_root_dir=GX_ROOT)
has_validation_failures = False

for table in config["tables"]:
    suite_name = table["suite_name"]
    table_name = table["table_name"]

    batch_request = BatchRequest(
        datasource_name=config["datasource_name"],
        data_connector_name=config["data_connector_name"],
        data_asset_name=table_name
    )

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name
    )

    results = validator.validate()
    has_validation_failures = has_validation_failures or (not results.success)

    # print summary
    print(f"\nTable: {table_name}")
    print(f"  Success: {results.success}")
    print(f"  Total expectations: {results.statistics['evaluated_expectations']}")
    print(f"  Passed: {results.statistics['successful_expectations']}")
    print(f"  Failed: {results.statistics['unsuccessful_expectations']}")

    for result in results.results:
        if not result.success:
            print(f"  FAILED: {result.expectation_config.expectation_type}")
            print(f"  Column: {result.expectation_config.kwargs.get('column', 'table-level')}")
            print(f"  Details: {result.result}")

if has_validation_failures:
    sys.exit(1)