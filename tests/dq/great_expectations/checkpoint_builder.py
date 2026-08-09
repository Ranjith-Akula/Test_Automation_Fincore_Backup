import great_expectations as gx
from great_expectations.core.batch import BatchRequest
import json
from config import GX_ROOT, RULES_CONFIG_PATH

with open(RULES_CONFIG_PATH) as f:
    config = json.load(f)

context = gx.get_context(context_root_dir=GX_ROOT)

# build validations list first
validations = []

for table in config["tables"]:
    validations.append({
        "batch_request": {
            "datasource_name": config["datasource_name"],
            "data_connector_name": config["data_connector_name"],
            "data_asset_name": table["table_name"]
        },
        "expectation_suite_name": table["suite_name"]
    })

# create checkpoint once with all validations
checkpoint = context.add_or_update_checkpoint(
    name="fincore_checkpoint",
    validations=validations
)

print(f"Checkpoint created with {len(validations)} validations")