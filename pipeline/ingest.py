"""
FinCore Bank - PySpark Data Pipeline
Main ingestion script that reads CSVs, applies transformations, and loads to PostgreSQL.
"""

import os
import sys
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_date, current_timestamp
from dotenv import load_dotenv
import logging
import psycopg2

# Import transformation functions
from transformations import (
    standardise_name,
    standardise_date,
    compute_loan_duration,
    compute_emi,
    map_status_code,
    fill_default_currency,
    filter_zero_amounts,
    trim_all_strings,
    remove_duplicates
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FincorePipeline:
    """Main pipeline class for FinCore Bank data ingestion."""
    
    def __init__(self, data_folder: str):
        """
        Initialize the pipeline.
        
        Args:
            data_folder: Name of the data folder (good_data or bad_data)
        """
        self.data_folder = data_folder
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', data_folder)
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'fincore'),
            'user': os.getenv('DB_USER', 'admin'),
            'password': os.getenv('DB_PASSWORD', 'fincore123')
        }
        
        # JDBC URL
        self.jdbc_url = f"jdbc:postgresql://{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        
        # Initialize Spark session
        self.spark = self._create_spark_session()
        
        logger.info(f"Pipeline initialized for data folder: {data_folder}")
        logger.info(f"Data path: {self.data_path}")
    
    def _create_spark_session(self) -> SparkSession:
        """Create and configure Spark session."""
        spark_builder = SparkSession.builder \
            .appName(os.getenv('SPARK_APP_NAME', 'FinCore_Pipeline')) \
            .config("spark.driver.memory", os.getenv('SPARK_DRIVER_MEMORY', '4g')) \
            .config("spark.executor.memory", os.getenv('SPARK_EXECUTOR_MEMORY', '4g'))

        postgres_jar = self._get_postgres_jar()
        if postgres_jar.endswith('.jar'):
            spark_builder = spark_builder \
                .config("spark.driver.extraClassPath", postgres_jar) \
                .config("spark.executor.extraClassPath", postgres_jar)
        else:
            spark_builder = spark_builder.config("spark.jars.packages", postgres_jar)

        spark = spark_builder.getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        return spark
    
    def _get_postgres_jar(self) -> str:
        """Get PostgreSQL JDBC driver path."""
        # Try to find the jar in common locations
        possible_paths = [
            os.path.expanduser("~/.ivy2/jars/org.postgresql_postgresql-42.6.0.jar"),
            "/usr/share/java/postgresql.jar",
            "/usr/local/share/java/postgresql.jar",
            os.path.expanduser("~/.m2/repository/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # If not found, return a default path (will be downloaded by Spark if needed)
        return "org.postgresql:postgresql:42.6.0"
    
    def read_csv(self, filename: str) -> 'DataFrame':
        """
        Read CSV file into DataFrame.
        
        Args:
            filename: Name of the CSV file
        
        Returns:
            Spark DataFrame
        """
        file_path = os.path.join(self.data_path, filename)
        logger.info(f"Reading CSV: {file_path}")
        
        df = self.spark.read \
            .option("header", "true") \
            .option("inferSchema", "true") \
            .option("encoding", "UTF-8") \
            .csv(file_path)
        
        logger.info(f"Loaded {df.count()} rows from {filename}")
        return df
    
    def transform_customers(self, df: 'DataFrame') -> 'DataFrame':
        """
        Apply transformations to customers data.
        
        Args:
            df: Raw customers DataFrame
        
        Returns:
            Transformed DataFrame
        """
        logger.info("Transforming customers data...")
        
        # Trim all string columns
        df = trim_all_strings(df)
        
        # Standardize name to UPPERCASE
        df = standardise_name(df, 'name')
        
        # Parse date_of_birth
        df = standardise_date(df, 'date_of_birth', 'dd/MM/yyyy')

        # Drop customer rows that would violate the email constraint
        df = df.filter(col('email').isNotNull() & (col('email') != ''))
        
        # Map status codes to labels
        status_mapping = {1: 'active', 2: 'inactive', 3: 'blocked'}
        df = map_status_code(df, 'status_code', status_mapping)
        
        # Rename status_code to status
        df = df.withColumnRenamed('status_code', 'status')

        # Drop customer rows that would violate table constraints
        df = df.filter(
            col('email').isNotNull()
            & (col('email') != '')
            & col('date_of_birth').isNotNull()
            & (col('date_of_birth') < current_date())
            & col('status').isin('active', 'inactive', 'blocked')
        )
        
        # Remove duplicates based on email
        df = remove_duplicates(df, ['email'])
        
        # Select final columns
        df = df.select(
            'id', 'name', 'email', 'phone', 'address',
            'date_of_birth', 'status', 'created_date', 'kyc_verified'
        )
        
        logger.info(f"Customers transformation complete: {df.count()} rows")
        return df
    
    def transform_accounts(self, df: 'DataFrame') -> 'DataFrame':
        """
        Apply transformations to accounts data.
        
        Args:
            df: Raw accounts DataFrame
        
        Returns:
            Transformed DataFrame
        """
        logger.info("Transforming accounts data...")
        
        # Trim all string columns
        df = trim_all_strings(df)
        
        # Fill default currency
        df = fill_default_currency(df, 'currency', 'USD')

        # Drop rows that would violate table constraints
        df = df.filter(
            # col('account_type').isin('savings', 'current', 'fixed_deposit')
            # & 
            col('status').isin('active', 'dormant', 'closed')
            & (
                (col('account_type') != 'savings')
                | (col('balance') >= 0)
            )
        )
        
        # Remove duplicates based on account_number
        df = remove_duplicates(df, ['account_number'])
        
        # Select final columns
        df = df.select(
            'id', 'customer_id', 'account_number', 'account_type',
            'balance', 'currency', 'status', 'opened_date'
        )
        
        logger.info(f"Accounts transformation complete: {df.count()} rows")
        return df
    
    def transform_transactions(self, df: 'DataFrame') -> 'DataFrame':
        """
        Apply transformations to transactions data.
        
        Args:
            df: Raw transactions DataFrame
        
        Returns:
            Transformed DataFrame
        """
        logger.info("Transforming transactions data...")
        
        # Trim all string columns
        df = trim_all_strings(df)
        
        # Filter out zero or negative amounts
        df = filter_zero_amounts(df, 'amount')
        
        # Fill default currency
        df = fill_default_currency(df, 'currency', 'USD')

        # Drop rows that would violate table constraints
        df = df.filter(
            (col('amount') > 0)
            & col('transaction_date').isNotNull()
            & (col('transaction_date') <= current_timestamp())
            & col('status').isin('completed', 'pending', 'failed', 'reversed')
        )
        
        # Remove duplicates based on reference_id
        df = remove_duplicates(df, ['reference_id'])
        
        # Select final columns
        df = df.select(
            'id', 'account_id', 'transaction_type', 'amount', 'currency',
            'transaction_date', 'description', 'status', 'reference_id'
        )
        
        logger.info(f"Transactions transformation complete: {df.count()} rows")
        return df
    
    def transform_loans(self, df: 'DataFrame') -> 'DataFrame':
        """
        Apply transformations to loans data.
        
        Args:
            df: Raw loans DataFrame
        
        Returns:
            Transformed DataFrame
        """
        logger.info("Transforming loans data...")
        
        # Trim all string columns
        df = trim_all_strings(df)
        
        # Parse dates
        df = standardise_date(df, 'start_date', 'dd/MM/yyyy')
        df = standardise_date(df, 'end_date', 'dd/MM/yyyy')
        
        # Compute loan duration in days
        df = compute_loan_duration(df)
        
        # Compute EMI amount
        df = compute_emi(df)

        # Drop rows that would violate table constraints
        df = df.filter(
            col('loan_type').isin('home', 'personal', 'auto', 'education')
            & col('outstanding_amount').isNotNull()
            & col('interest_rate').isNotNull()
            & (col('interest_rate') >= 1)
            & (col('interest_rate') <= 30)
            & col('start_date').isNotNull()
            & col('end_date').isNotNull()
            & (col('end_date') > col('start_date'))
            & col('status').isin('active', 'closed', 'defaulted', 'restructured')
        )
        
        # Select final columns
        df = df.select(
            'id', 'customer_id', 'loan_type', 'principal_amount',
            'outstanding_amount', 'interest_rate', 'start_date', 'end_date',
            'status', 'loan_duration_days', 'emi_amount'
        )
        
        logger.info(f"Loans transformation complete: {df.count()} rows")
        return df
    
    def truncate_target_tables(self):
        """Truncate target tables before loading to avoid drop/FK conflicts."""
        conn = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "TRUNCATE TABLE transactions, accounts, loans, customers RESTART IDENTITY CASCADE"
                )
            logger.info("Target tables truncated successfully")
        finally:
            conn.close()

    def write_to_postgres(self, df: 'DataFrame', table_name: str, mode: str = 'append'):
        """
        Write DataFrame to PostgreSQL table.
        
        Args:
            df: DataFrame to write
            table_name: Target table name
            mode: Write mode (append)
        """
        logger.info(f"Writing {df.count()} rows to table: {table_name}")
        
        df.write \
            .format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", table_name) \
            .option("user", self.db_config['user']) \
            .option("password", self.db_config['password']) \
            .option("driver", "org.postgresql.Driver") \
            .mode(mode) \
            .save()
        
        logger.info(f"✓ {table_name}: {df.count()} rows loaded")
    
    def run(self):
        """Execute the complete pipeline."""
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("Starting FinCore Bank Data Pipeline")
        logger.info(f"Data folder: {self.data_folder}")
        logger.info("="*60)
        
        try:
            # Read CSVs
            logger.info("\n[1/3] Reading CSV files...")
            customers_df = self.read_csv('customers.csv')
            accounts_df = self.read_csv('accounts.csv')
            transactions_df = self.read_csv('transactions.csv')
            loans_df = self.read_csv('loans.csv')
            
            # Transform data
            logger.info("\n[2/3] Applying transformations...")
            customers_transformed = self.transform_customers(customers_df)
            accounts_transformed = self.transform_accounts(accounts_df)
            transactions_transformed = self.transform_transactions(transactions_df)
            loans_transformed = self.transform_loans(loans_df)

            # Keep only child rows that reference existing parent keys.
            valid_customer_ids = customers_transformed.select(col('id').alias('customer_id_ref')).distinct()
            accounts_transformed = accounts_transformed \
                .join(valid_customer_ids, accounts_transformed.customer_id == valid_customer_ids.customer_id_ref, 'inner') \
                .drop('customer_id_ref')
            loans_transformed = loans_transformed \
                .join(valid_customer_ids, loans_transformed.customer_id == valid_customer_ids.customer_id_ref, 'inner') \
                .drop('customer_id_ref')

            valid_account_ids = accounts_transformed.select(col('id').alias('account_id_ref')).distinct()
            transactions_transformed = transactions_transformed \
                .join(valid_account_ids, transactions_transformed.account_id == valid_account_ids.account_id_ref, 'inner') \
                .drop('account_id_ref')

            logger.info(
                "Post-FK filter counts -> customers: %s, accounts: %s, transactions: %s, loans: %s",
                customers_transformed.count(),
                accounts_transformed.count(),
                transactions_transformed.count(),
                loans_transformed.count(),
            )
            
            # Load to PostgreSQL
            logger.info("\n[3/3] Loading to PostgreSQL...")
            self.truncate_target_tables()
            self.write_to_postgres(customers_transformed, 'customers')
            self.write_to_postgres(accounts_transformed, 'accounts')
            self.write_to_postgres(transactions_transformed, 'transactions')
            self.write_to_postgres(loans_transformed, 'loans')
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "="*60)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info("="*60)
            
            return 0
            
        except Exception as e:
            logger.error(f"\n❌ Pipeline failed: {str(e)}", exc_info=True)
            return 1
        
        finally:
            self.spark.stop()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <data_folder>")
        print("Example: python ingest.py good_data")
        print("         python ingest.py bad_data")
        sys.exit(1)
    
    data_folder = sys.argv[1]
    
    if data_folder not in ['good_data', 'bad_data']:
        print(f"Error: Invalid data folder '{data_folder}'")
        print("Valid options: good_data, bad_data")
        sys.exit(1)
    
    pipeline = FincorePipeline(data_folder)
    exit_code = pipeline.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
