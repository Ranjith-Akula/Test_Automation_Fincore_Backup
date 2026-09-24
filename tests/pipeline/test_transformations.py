import pytest
from pipeline.transformations import standardise_name,standardise_date,fill_default_currency,trim_all_strings,map_status_code,compute_loan_duration,compute_emi,filter_zero_amounts,remove_duplicates,validate_email_format,add_audit_columns
from pyspark.sql.types import StructType, StructField, StringType
from datetime import date
from decimal import Decimal


def test_standardise_name_converts_lowercase_to_uppercase(spark):
    # Arrange: input with a lowercase name
    input_df = spark.createDataFrame(
        [("john doe",)],
        ["name"]
    )

    # Act
    result_df = standardise_name(input_df, "name")

    # Assert
    result = result_df.collect()
    assert result[0]["name"] == "JOHN DOE"


def test_standardise_name_leaves_already_uppercase_unchanged(spark):
    # Arrange: input already in uppercase
    input_df = spark.createDataFrame(
        [("JANE SMITH",)],
        ["name"]
    )

    # Act
    result_df = standardise_name(input_df, "name")

    # Assert
    result = result_df.collect()
    assert result[0]["name"] == "JANE SMITH"


def test_standardise_date_formats_correctly(spark):
    # Arrange: input with a date in DD/MM/YYYY format
    input_df = spark.createDataFrame(
        [("25/12/2023",)],
        ["date"]
    )

    # Act
    result_df = standardise_date(input_df, "date")

    # Assert
    result = result_df.collect()
    assert result[0]["date"] == date(2023, 12, 25)


def test_standardise_date_leaves_already_standardised_date_unchanged(spark):
    # Arrange: input with a date already in YYYY-MM-DD format
    input_df = spark.createDataFrame(
        [("2023-12-25",)],
        ["date"]
    )

    # Act
    result_df = standardise_date(input_df, "date")

    # Assert
    result = result_df.collect()
    assert result[0]["date"] == date(2023, 12, 25)


def test_standardise_date_handles_invalid_date_format(spark):
    # Arrange: input with an invalid date format
    input_df = spark.createDataFrame(
        [("25122023",)],
        ["date"]
    )

    # Act
    result_df = standardise_date(input_df, "date")

    # Assert
    result = result_df.collect()
    assert result[0]["date"] is None


def test_fill_default_currency_applies_default_when_missing(spark):
    # Arrange: input with a missing currency
    schema = StructType([StructField("currency", StringType(), True)])
    input_df = spark.createDataFrame(
        [(None,)],
        schema=schema
    )

    # Act
    result_df = fill_default_currency(input_df, "currency", "USD")

    # Assert
    result = result_df.collect()
    assert result[0]["currency"] == "USD"

def test_fill_default_currency_leaves_existing_currency_unchanged(spark):
    # Arrange: input with an existing currency
    input_df = spark.createDataFrame(
        [("EUR",)],
        ["currency"]
    )

    # Act
    result_df = fill_default_currency(input_df, "currency", "USD")

    # Assert
    result = result_df.collect()
    assert result[0]["currency"] == "EUR"

def test_trim_all_strings_trims_whitespace(spark):
    # Arrange: input with leading and trailing whitespace
    input_df = spark.createDataFrame(
        [("  hello  ","world  "," ","check ",25.00)],
        ["text", "text2", "text3", "text4", "amount"]
    )

    # Act
    result_df = trim_all_strings(input_df)

    # Assert
    result = result_df.collect()
    assert result[0]["text"] == "hello"
    assert result[0]["text2"] == "world"
    assert result[0]["text3"] == ""
    assert result[0]["text4"] == "check"
    assert result[0]["amount"] == 25.00

def test_trim_all_strings_leaves_string_without_whitespace_unchanged(spark):
    # Arrange: input with no leading or trailing whitespace
    input_df = spark.createDataFrame(
        [("hello",)],
        ["text"]
    )

    # Act
    result_df = trim_all_strings(input_df)

    # Assert
    result = result_df.collect()
    assert result[0]["text"] == "hello"


def test_map_status_code_maps_known_status_code(spark):
    # Arrange: input with a known status code
    input_df = spark.createDataFrame(
        [(1, 1, 0), (0, 0, 1), (0, 2, 3)],
        ["flag_column", "country_code", "status_code"]
    )

    # Act
    status_code_mapping = {1: 'active', 2: 'inactive', 3: 'blocked', 0: 'unknown'}
    flag_mapping = {1: 'true', 0: 'false'}
    country_mapping = {1: 'US', 0: 'CN', 2: 'IN'}
    result_df = map_status_code(input_df, "status_code", status_code_mapping)
    result_df = map_status_code(result_df, "flag_column", flag_mapping)
    result_df = map_status_code(result_df, "country_code", country_mapping)

    # Assert
    result = result_df.collect()
    assert result[0]["status_code"] == "unknown"
    assert result[0]["flag_column"] == "true"
    assert result[0]["country_code"] == "US"
    assert result[1]["status_code"] == "active"
    assert result[1]["flag_column"] == "false"
    assert result[1]["country_code"] == "CN"
    assert result[2]["status_code"] == "blocked"
    assert result[2]["flag_column"] == "false"
    assert result[2]["country_code"] == "IN"


def test_compute_loan_duration_computes_correct_duration(spark):
    # Arrange: input with start and end dates
    input_df = spark.createDataFrame(
        [("2023-01-01", "2023-12-31"), ("2022-06-15", "2023-06-14")],
        ["start_date", "end_date"]
    )

    # Act
    result_df = compute_loan_duration(input_df)

    # Assert
    result = result_df.collect()
    assert result[0]["loan_duration"] == 364  # Assuming duration is in days
    assert result[1]["loan_duration"] == 364  # Assuming duration is in days


def test_compute_loan_duration_with_incorrect_dates(spark):
    # Arrange: input with incorrect date formats
    input_df = spark.createDataFrame(
        [("2023-01-01", "2020-12-31"), ("2022-06-15", "invalid_date")],
        ["start_date", "end_date"]
    )

    # Act
    result_df = compute_loan_duration(input_df)

    # Assert
    result = result_df.collect()
    assert result[0]["loan_duration"] is None  # Assuming duration is in days
    assert result[1]["loan_duration"] is None  # Assuming incorrect dates result in None 


def test_compute_emi_computes_correct_emi(spark):
    # Arrange: input with principal, rate, and duration
    input_df = spark.createDataFrame(
        [(1000, 5, 360), (2000, 7, 720)],
        ["principal_amount", "interest_rate", "loan_duration_days"]
    )

    # Act
    # with pytest.raises(TypeError):
    #     compute_emi(input_df)
    result_df = compute_emi(input_df)

    # Assert
    result = result_df.collect()
    assert result[0]["emi_amount"] == Decimal("85.61")
    assert result[1]["emi_amount"] == Decimal("89.55")


def test_filter_zero_amounts_filters_correctly(spark):
    # Arrange: input with various amounts
    input_df = spark.createDataFrame(
        [(100, ), (0, ), (50, ), (0, )],
        ["amount"]
    )

    # Act
    result_df = filter_zero_amounts(input_df)

    # Assert
    result = result_df.collect()
    assert len(result) == 2
    assert result[0]["amount"] == 100
    assert result[1]["amount"] == 50


def test_remove_duplicates_removes_correctly(spark):
    # Arrange: input with duplicate rows
    input_df = spark.createDataFrame(
        [(1, "Alice"), (2, "Bob"), (1, "Alice")],
        ["id", "name"]
    )

    # Act
    result_df = remove_duplicates(input_df)

    # Assert
    result = result_df.collect()
    result = result_df.orderBy("id").collect()
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["name"] == "Alice"
    assert result[1]["id"] == 2
    assert result[1]["name"] == "Bob"


def test_validate_email_format_validates_correctly(spark):
    # Arrange: input with various email formats
    input_df = spark.createDataFrame(
        [("alice@example.com", ), ("invalid_email", ), ("bob@example.com", )],
        ["email"]
    )

    # Act
    result_df = validate_email_format(input_df)

    # Assert
    result = result_df.collect()
    assert result[0]["email_valid"] is True
    assert result[1]["email_valid"] is False
    assert result[2]["email_valid"] is True


def test_add_audit_columns_adds_correctly(spark):
    # Arrange: input with some data
    input_df = spark.createDataFrame(
        [(1, "Alice"), (2, "Bob")],
        ["id", "name"]
    )

    # Act
    result_df = add_audit_columns(input_df)

    # Assert
    result = result_df.collect()
    assert "loaded_at" in result_df.columns

