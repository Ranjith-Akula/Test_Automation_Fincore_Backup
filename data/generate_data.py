"""
FinCore Bank - Dataset Generator
Generates good_data (clean) and bad_data (with violations) CSV files.
"""

import csv
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# Output directories
GOOD_DATA_DIR = os.path.join(os.path.dirname(__file__), 'good_data')
BAD_DATA_DIR = os.path.join(os.path.dirname(__file__), 'bad_data')

# Create directories
os.makedirs(GOOD_DATA_DIR, exist_ok=True)
os.makedirs(BAD_DATA_DIR, exist_ok=True)

# Configuration
NUM_CUSTOMERS = 10000
NUM_ACCOUNTS = 25000
NUM_TRANSACTIONS = 500000
NUM_LOANS = 8000

# Status mappings
CUSTOMER_STATUSES = ['active', 'inactive', 'blocked']
ACCOUNT_STATUSES = ['active', 'dormant', 'closed']
ACCOUNT_TYPES = ['savings', 'current', 'fixed_deposit']
TRANSACTION_TYPES = ['credit', 'debit', 'transfer']
TRANSACTION_STATUSES = ['completed', 'pending', 'failed', 'reversed']
LOAN_TYPES = ['home', 'personal', 'auto', 'education']
LOAN_STATUSES = ['active', 'closed', 'defaulted', 'restructured']

print("="*60)
print("FinCore Bank - Dataset Generator")
print("="*60)
print()


def generate_customers(is_good=True):
    """Generate customers data."""
    filename = 'customers.csv'
    filepath = os.path.join(GOOD_DATA_DIR if is_good else BAD_DATA_DIR, filename)
    
    print(f"Generating {filename} ({'good' if is_good else 'bad'} data)...")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'name', 'email', 'phone', 'address', 'date_of_birth',
            'status_code', 'created_date', 'kyc_verified'
        ])
        
        for i in range(1, NUM_CUSTOMERS + 1):
            name = fake.name()
            email = fake.email()
            phone = fake.phone_number()[:20]
            address = fake.address().replace('\n', ', ')
            
            # Date of birth (18-80 years ago)
            dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
            dob_str = dob.strftime('%d/%m/%Y')
            
            # Status code (1=active, 2=inactive, 3=blocked)
            status_code = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            
            # Created date (within last 5 years)
            created_date = fake.date_time_between(start_date='-5y', end_date='now')
            created_date_str = created_date.strftime('%Y-%m-%d %H:%M:%S')
            
            kyc_verified = random.choice([True, False])
            
            # Introduce violations for bad data
            if not is_good:
                # 50 NULL emails
                if i <= 50:
                    email = ''
                
                # 30 invalid status codes
                if 51 <= i <= 80:
                    status_code = random.choice([4, 5, 99])
                
                # 20 future date of birth
                if 81 <= i <= 100:
                    future_date = datetime.now() + timedelta(days=random.randint(1, 365))
                    dob_str = future_date.strftime('%d/%m/%Y')
            
            writer.writerow([
                i, name, email, phone, address, dob_str,
                status_code, created_date_str, kyc_verified
            ])
    
    print(f"  [OK] Generated {NUM_CUSTOMERS} customers")


def generate_accounts(is_good=True):
    """Generate accounts data."""
    filename = 'accounts.csv'
    filepath = os.path.join(GOOD_DATA_DIR if is_good else BAD_DATA_DIR, filename)
    
    print(f"Generating {filename} ({'good' if is_good else 'bad'} data)...")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'customer_id', 'account_number', 'account_type',
            'balance', 'currency', 'status', 'opened_date'
        ])
        
        for i in range(1, NUM_ACCOUNTS + 1):
            customer_id = random.randint(1, NUM_CUSTOMERS)
            account_number = f"ACC{str(i).zfill(10)}"
            account_type = random.choice(ACCOUNT_TYPES)
            
            # Balance
            if account_type == 'savings':
                balance = round(random.uniform(100, 50000), 2)
            elif account_type == 'current':
                balance = round(random.uniform(-10000, 100000), 2)
            else:  # fixed_deposit
                balance = round(random.uniform(10000, 500000), 2)
            
            currency = random.choices(['USD', 'EUR', 'GBP', None], weights=[85, 5, 5, 5])[0]
            status = random.choices(ACCOUNT_STATUSES, weights=[75, 15, 10])[0]
            
            # Opened date (within last 10 years)
            opened_date = fake.date_between(start_date='-10y', end_date='today')
            opened_date_str = opened_date.strftime('%Y-%m-%d')
            
            # Introduce violations for bad data
            if not is_good:
                # 40 negative balances on savings accounts
                if i <= 40 and account_type == 'savings':
                    balance = round(random.uniform(-5000, -100), 2)
                
                # 25 invalid account types
                if 41 <= i <= 65:
                    account_type = random.choice(['checking', 'investment', 'loan'])
            
            writer.writerow([
                i, customer_id, account_number, account_type,
                balance, currency or '', status, opened_date_str
            ])
    
    print(f"  [OK] Generated {NUM_ACCOUNTS} accounts")


def generate_transactions(is_good=True):
    """Generate transactions data."""
    filename = 'transactions.csv'
    filepath = os.path.join(GOOD_DATA_DIR if is_good else BAD_DATA_DIR, filename)
    
    print(f"Generating {filename} ({'good' if is_good else 'bad'} data)...")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'account_id', 'transaction_type', 'amount', 'currency',
            'transaction_date', 'description', 'status', 'reference_id'
        ])
        
        for i in range(1, NUM_TRANSACTIONS + 1):
            account_id = random.randint(1, NUM_ACCOUNTS)
            transaction_type = random.choice(TRANSACTION_TYPES)
            
            # Amount
            amount = round(random.uniform(10, 10000), 2)
            
            currency = random.choices(['USD', 'EUR', 'GBP'], weights=[90, 5, 5])[0]
            
            # Transaction date (within last 2 years)
            transaction_date = fake.date_time_between(start_date='-2y', end_date='now')
            transaction_date_str = transaction_date.strftime('%Y-%m-%d %H:%M:%S')
            
            description = fake.sentence(nb_words=6)
            status = random.choices(TRANSACTION_STATUSES, weights=[85, 8, 5, 2])[0]
            reference_id = f"TXN{str(i).zfill(12)}"
            
            # Introduce violations for bad data
            if not is_good:
                # 200 negative amounts
                if i <= 200:
                    amount = round(random.uniform(-1000, -10), 2)
                
                # 150 future dates
                if 201 <= i <= 350:
                    future_date = datetime.now() + timedelta(days=random.randint(1, 365))
                    transaction_date_str = future_date.strftime('%Y-%m-%d %H:%M:%S')
                
                # 100 orphaned account_ids
                if 351 <= i <= 450:
                    account_id = random.randint(NUM_ACCOUNTS + 1, NUM_ACCOUNTS + 1000)
                
                # 80 duplicate reference_ids
                if 451 <= i <= 530:
                    reference_id = "TXN000000000001"  # Duplicate
            
            writer.writerow([
                i, account_id, transaction_type, amount, currency,
                transaction_date_str, description, status, reference_id
            ])
    
    print(f"  [OK] Generated {NUM_TRANSACTIONS} transactions")


def generate_loans(is_good=True):
    """Generate loans data."""
    filename = 'loans.csv'
    filepath = os.path.join(GOOD_DATA_DIR if is_good else BAD_DATA_DIR, filename)
    
    print(f"Generating {filename} ({'good' if is_good else 'bad'} data)...")
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'customer_id', 'loan_type', 'principal_amount',
            'outstanding_amount', 'interest_rate', 'start_date',
            'end_date', 'status'
        ])
        
        for i in range(1, NUM_LOANS + 1):
            customer_id = random.randint(1, NUM_CUSTOMERS)
            loan_type = random.choice(LOAN_TYPES)
            
            # Principal amount based on loan type
            if loan_type == 'home':
                principal = round(random.uniform(100000, 500000), 2)
            elif loan_type == 'auto':
                principal = round(random.uniform(10000, 50000), 2)
            elif loan_type == 'education':
                principal = round(random.uniform(5000, 100000), 2)
            else:  # personal
                principal = round(random.uniform(1000, 50000), 2)
            
            # Outstanding amount (0% to 100% of principal)
            outstanding = round(principal * random.uniform(0, 1), 2)
            
            # Interest rate (3% to 15%)
            interest_rate = round(random.uniform(3, 15), 2)
            
            # Start date (within last 10 years)
            start_date = fake.date_between(start_date='-10y', end_date='today')
            
            # End date (5 to 30 years from start)
            years_duration = random.randint(5, 30)
            end_date = start_date + timedelta(days=years_duration * 365)
            
            start_date_str = start_date.strftime('%d/%m/%Y')
            end_date_str = end_date.strftime('%d/%m/%Y')
            
            status = random.choices(LOAN_STATUSES, weights=[70, 20, 5, 5])[0]
            
            # Introduce violations for bad data
            if not is_good:
                # 35 invalid interest rates (>30%)
                if i <= 35:
                    interest_rate = round(random.uniform(95, 99), 2)
                
                # 25 end_date before start_date
                if 36 <= i <= 60:
                    end_date = start_date - timedelta(days=random.randint(1, 365))
                    end_date_str = end_date.strftime('%d/%m/%Y')
                
                # 45 NULL outstanding_amount
                if 61 <= i <= 105:
                    outstanding = ''
            
            writer.writerow([
                i, customer_id, loan_type, principal,
                outstanding, interest_rate, start_date_str,
                end_date_str, status
            ])
    
    print(f"  [OK] Generated {NUM_LOANS} loans")


def main():
    """Generate all datasets."""
    print("Generating GOOD DATA (clean)...")
    print("-" * 60)
    generate_customers(is_good=True)
    generate_accounts(is_good=True)
    generate_transactions(is_good=True)
    generate_loans(is_good=True)
    print()
    
    print("Generating BAD DATA (with violations)...")
    print("-" * 60)
    generate_customers(is_good=False)
    generate_accounts(is_good=False)
    generate_transactions(is_good=False)
    generate_loans(is_good=False)
    print()
    
    print("="*60)
    print("Dataset generation complete!")
    print("="*60)
    print()
    print(f"Good data location: {GOOD_DATA_DIR}")
    print(f"Bad data location: {BAD_DATA_DIR}")
    print()
    print("Summary:")
    print(f"  - Customers: {NUM_CUSTOMERS:,}")
    print(f"  - Accounts: {NUM_ACCOUNTS:,}")
    print(f"  - Transactions: {NUM_TRANSACTIONS:,}")
    print(f"  - Loans: {NUM_LOANS:,}")
    print(f"  - Total records: {NUM_CUSTOMERS + NUM_ACCOUNTS + NUM_TRANSACTIONS + NUM_LOANS:,}")
    print()
    print("Next steps:")
    print("  1. Run pipeline: bash pipeline/run_pipeline.sh good_data")
    print("  2. Test with bad data: bash pipeline/run_pipeline.sh bad_data")
    print()


if __name__ == '__main__':
    main()
