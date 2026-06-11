from great_expectations.expectations.expectation import QueryExpectation


class ExpectEndDateAfterStartDate(QueryExpectation):
    """end_date must always be after start_date"""

    query = """
        SELECT 
            COUNT(CASE WHEN end_date <= start_date THEN 1 END) as unexpected_count,
            COUNT(*) as total_count
        FROM {active_batch}
        WHERE end_date IS NOT NULL 
        AND start_date IS NOT NULL
    """

    metric_dependencies = ("query.template_values",)
    success_keys = ("query", "template_dict")

    default_kwarg_values = {
        "query": query,
        "template_dict": {},
        "result_format": "BASIC",
        "catch_exceptions": True
    }

    def _validate(self, configuration, metrics, runtime_configuration=None, execution_engine=None):
        query_result = list(metrics.get("query.template_values"))
        unexpected_count = query_result[0]["unexpected_count"]
        total_count = query_result[0].get("total_count", 0) or 1
        success = unexpected_count == 0
        unexpected_percent = (unexpected_count / total_count * 100) if total_count > 0 else 0
        return {
            "success": success,
            "result": {
                "unexpected_count": unexpected_count,
                "unexpected_percent": round(unexpected_percent, 4),
                "element_count": total_count
            }
        }

    @classmethod
    def _prescriptive_renderer(cls, configuration=None, result=None, **kwargs):
        return []
    
    @classmethod  
    def _diagnostic_unexpected_statement_renderer(cls, result=None, **kwargs):
        return []