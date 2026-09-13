"""
FinCore Bank - PySpark Transformation Functions
All transformation functions for the data pipeline.
Trainees will unit test these functions in UC4.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    upper, trim, col, to_date, datediff, when, lit, regexp_replace
)
from pyspark.sql.types import StringType
from decimal import Decimal
import math


def standardise_name(df: DataFrame, column_name: str) -> DataFrame:
    """
    Convert name column to UPPERCASE.
    
    Args:
        df: Input DataFrame
        column_name: Name of the column to standardize
    
    Returns:
        DataFrame with standardized name column
    
    Example:
        >>> standardise_name(df, 'name')
        # 'John Doe' -> 'JOHN DOE'
    """
    return df.withColumn(column_name, upper(col(column_name)))


def standardise_date(df: DataFrame, column_name: str, input_format: str = "dd/MM/yyyy") -> DataFrame:
    """
    Parse date strings and convert to date type.
    
    Args:
        df: Input DataFrame
        column_name: Name of the date column
        input_format: Input date format (default: dd/MM/yyyy)
    
    Returns:
        DataFrame with standardized date column
    
    Example:
        >>> standardise_date(df, 'date_of_birth', 'dd/MM/yyyy')
        # '15/06/1985' -> date(1985-06-15)
    """
    return df.withColumn(column_name, to_date(col(column_name), input_format))


def compute_loan_duration(df: DataFrame) -> DataFrame:
    """
    Calculate loan duration in days from start_date and end_date.
    
    Args:
        df: Input DataFrame with start_date and end_date columns
    
    Returns:
        DataFrame with loan_duration_days column added
    
    Example:
        >>> compute_loan_duration(df)
        # start_date: 2023-01-01, end_date: 2043-01-01
        # loan_duration_days: 7305
    """
    df = df.withColumn(
        "loan_duration_days",
        datediff(col("end_date"), col("start_date"))
    )
    return df.withColumn("loan_duration", col("loan_duration_days"))


def compute_emi(df: DataFrame) -> DataFrame:
    """
    Calculate EMI (Equated Monthly Installment) using standard formula.
    Formula: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    where:
        P = principal_amount
        r = monthly interest rate (annual_rate / 12 / 100)
        n = number of months (loan_duration_days / 30)
    
    Args:
        df: Input DataFrame with principal_amount, interest_rate, loan_duration_days
    
    Returns:
        DataFrame with emi_amount column added
    
    Example:
        >>> compute_emi(df)
        # principal: 250000, rate: 8.5%, duration: 7305 days
        # emi_amount: 2152.39
    """
    # Calculate monthly interest rate
    df = df.withColumn(
        "monthly_rate",
        (col("interest_rate") / lit(12) / lit(100))
    )
    
    # Calculate number of months
    df = df.withColumn(
        "num_months",
        (col("loan_duration_days") / lit(30)).cast("integer")
    )
    
    # Calculate (1 + r)^n
    df = df.withColumn(
        "power_term",
        (lit(1) + col("monthly_rate")) ** col("num_months")
    )
    
    # Calculate EMI: P * r * (1+r)^n / ((1+r)^n - 1)
    df = df.withColumn(
        "emi_amount",
        when(
            col("num_months") > 0,
            (col("principal_amount") * col("monthly_rate") * col("power_term")) /
            (col("power_term") - lit(1))
        ).otherwise(lit(0))
    )
    
    # Round to 2 decimal places
    df = df.withColumn("emi_amount", col("emi_amount").cast("decimal(15,2)"))
    
    # Drop temporary columns
    df = df.drop("monthly_rate", "num_months", "power_term")
    
    return df


def map_status_code(df: DataFrame, column_name: str, code_mapping: dict) -> DataFrame:
    """
    Replace numeric status codes with string labels.
    
    Args:
        df: Input DataFrame
        column_name: Name of the status code column
        code_mapping: Dictionary mapping codes to labels
    
    Returns:
        DataFrame with mapped status values
    
    Example:
        >>> mapping = {1: 'active', 2: 'inactive', 3: 'blocked'}
        >>> map_status_code(df, 'status_code', mapping)
        # 1 -> 'active', 2 -> 'inactive', 3 -> 'blocked'
    """
    # Create when-otherwise chain for mapping
    mapping_expr = None
    for code, label in code_mapping.items():
        if mapping_expr is None:
            mapping_expr = when(col(column_name) == code, lit(label))
        else:
            mapping_expr = mapping_expr.when(col(column_name) == code, lit(label))
    
    # Add otherwise clause for unmapped values
    mapping_expr = mapping_expr.otherwise(col(column_name))
    
    # Replace the column
    return df.withColumn(column_name, mapping_expr)


def fill_default_currency(df: DataFrame, column_name: str = "currency", default_value: str = "USD") -> DataFrame:
    """
    Fill NULL currency values with default currency.
    
    Args:
        df: Input DataFrame
        column_name: Name of the currency column
        default_value: Default currency code (default: USD)
    
    Returns:
        DataFrame with filled currency values
    
    Example:
        >>> fill_default_currency(df, 'currency', 'USD')
        # NULL -> 'USD'
    """
    return df.fillna({column_name: default_value})


def filter_zero_amounts(df: DataFrame, amount_column: str = "amount") -> DataFrame:
    """
    Remove rows where amount is zero or negative.
    
    Args:
        df: Input DataFrame
        amount_column: Name of the amount column
    
    Returns:
        DataFrame with zero/negative amounts filtered out
    
    Example:
        >>> filter_zero_amounts(df, 'amount')
        # Removes rows where amount <= 0
    """
    return df.filter(col(amount_column) > 0)


def trim_all_strings(df: DataFrame) -> DataFrame:
    """
    Apply trim() to all StringType columns to remove leading/trailing whitespace.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with all string columns trimmed
    
    Example:
        >>> trim_all_strings(df)
        # '  John Doe  ' -> 'John Doe'
    """
    string_columns = [field.name for field in df.schema.fields if isinstance(field.dataType, StringType)]
    
    for col_name in string_columns:
        df = df.withColumn(col_name, trim(col(col_name)))
    
    return df


def validate_email_format(df: DataFrame, email_column: str = "email") -> DataFrame:
    """
    Add a column indicating if email format is valid.
    
    Args:
        df: Input DataFrame
        email_column: Name of the email column
    
    Returns:
        DataFrame with email_valid boolean column added
    
    Example:
        >>> validate_email_format(df, 'email')
        # Adds 'email_valid' column: True/False
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return df.withColumn(
        "email_valid",
        col(email_column).rlike(email_pattern)
    )


def remove_duplicates(df: DataFrame, subset_columns: list = None) -> DataFrame:
    """
    Remove duplicate rows based on specified columns.
    
    Args:
        df: Input DataFrame
        subset_columns: List of columns to check for duplicates (None = all columns)
    
    Returns:
        DataFrame with duplicates removed
    
    Example:
        >>> remove_duplicates(df, ['email'])
        # Removes rows with duplicate emails
    """
    if subset_columns:
        return df.dropDuplicates(subset_columns)
    else:
        return df.dropDuplicates()


def add_audit_columns(df: DataFrame) -> DataFrame:
    """
    Add audit columns: loaded_at timestamp.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with audit columns added
    
    Example:
        >>> add_audit_columns(df)
        # Adds 'loaded_at' with current timestamp
    """
    from pyspark.sql.functions import current_timestamp
    
    return df.withColumn("loaded_at", current_timestamp())
