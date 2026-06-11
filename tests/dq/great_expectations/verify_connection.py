from config import GX_ROOT
import great_expectations as gx
import os

context = gx.get_context(context_root_dir=GX_ROOT)

# Step 1 - confirm datasource is registered
datasources = context.list_datasources()
print("Datasources found:", datasources)

# Step 2 - confirm GX can actually reach PostgreSQL
datasource = context.get_datasource("fincore_pg")
print("Datasource object:", datasource)

# list all available data assets GX can see
connector = datasource.get_available_data_asset_names()
print("Available assets:", connector)