import great_expectations as gx
import sys
sys.path.insert(0, "/workspaces/Test_Automation_Fincore_Backup/tests/dq/great_expectations/gx/plugins")
import expect_end_date_after_start_date

GX_ROOT = "/workspaces/Test_Automation_Fincore_Backup/tests/dq/great_expectations/gx"

context = gx.get_context(context_root_dir=GX_ROOT)

def run_validation():
    result = context.run_checkpoint(checkpoint_name="fincore_checkpoint")
    # temporary — show which expectations fail
    for run_result in result.run_results.values():
        validation_result = run_result.get("validation_result")
        if validation_result:
            for r in validation_result.results:
                if not r.success:
                    print(f"FAILED: {r.expectation_config.expectation_type} | column: {r.expectation_config.kwargs.get('column', 'table-level')}")
    if not result.success:
        context.build_data_docs(site_names=["dq_bad_site"])
        print("Validation FAILED")
        sys.exit(1)
    else:
        context.build_data_docs(site_names=["dq_good_site"])
        print("Validation PASSED")
        sys.exit(0)

run_validation()