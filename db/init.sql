-- FinCore Bank Database Schema
-- PostgreSQL 15+

-- Drop existing tables if they exist
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Create customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    date_of_birth DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'blocked')),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kyc_verified BOOLEAN DEFAULT FALSE
);

-- Create accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    account_type VARCHAR(20) NOT NULL,
    --  CHECK (account_type IN ('savings', 'current', 'fixed_deposit')),
    balance DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'dormant', 'closed')),
    opened_date DATE NOT NULL,
    CONSTRAINT positive_balance_for_savings CHECK (
        account_type != 'savings' OR balance >= 0
    )
);

-- Create transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('credit', 'debit', 'transfer')),
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_date TIMESTAMP NOT NULL CHECK (transaction_date <= CURRENT_TIMESTAMP),
    description VARCHAR(255),
    status VARCHAR(20) NOT NULL CHECK (status IN ('completed', 'pending', 'failed', 'reversed')),
    reference_id VARCHAR(50) UNIQUE
);

-- Create loans table
CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    loan_type VARCHAR(30) NOT NULL CHECK (loan_type IN ('home', 'personal', 'auto', 'education')),
    principal_amount DECIMAL(15,2) NOT NULL CHECK (principal_amount > 0),
    outstanding_amount DECIMAL(15,2) NOT NULL CHECK (outstanding_amount >= 0),
    interest_rate DECIMAL(5,2) NOT NULL CHECK (interest_rate >= 1 AND interest_rate <= 30),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL CHECK (end_date > start_date),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'closed', 'defaulted', 'restructured')),
    loan_duration_days INTEGER,
    emi_amount DECIMAL(15,2)
);

-- Create indexes for performance
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_created_date ON customers(created_date);

CREATE INDEX idx_accounts_customer ON accounts(customer_id);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_account_number ON accounts(account_number);

CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_reference ON transactions(reference_id);

CREATE INDEX idx_loans_customer ON loans(customer_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_loans_type ON loans(loan_type);

-- Create view for customer summary
CREATE OR REPLACE VIEW customer_summary AS
SELECT 
    c.id,
    c.name,
    c.email,
    c.status,
    COUNT(DISTINCT a.id) as total_accounts,
    COUNT(DISTINCT l.id) as total_loans,
    COALESCE(SUM(a.balance), 0) as total_balance
FROM customers c
LEFT JOIN accounts a ON c.id = a.customer_id
LEFT JOIN loans l ON c.id = l.customer_id
GROUP BY c.id, c.name, c.email, c.status;

-- Create view for account transactions summary
CREATE OR REPLACE VIEW account_transaction_summary AS
SELECT 
    a.id as account_id,
    a.account_number,
    a.customer_id,
    COUNT(t.id) as transaction_count,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'credit' THEN t.amount ELSE 0 END), 0) as total_credits,
    COALESCE(SUM(CASE WHEN t.transaction_type = 'debit' THEN t.amount ELSE 0 END), 0) as total_debits,
    MAX(t.transaction_date) as last_transaction_date
FROM accounts a
LEFT JOIN transactions t ON a.id = t.account_id
GROUP BY a.id, a.account_number, a.customer_id;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO admin;

-- Insert test user for authentication (password: Admin@123, hashed with bcrypt)
-- This will be handled by the application seed script

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'FinCore Bank database schema initialized successfully!';
    RAISE NOTICE 'Tables created: customers, accounts, transactions, loans';
    RAISE NOTICE 'Indexes created for optimal query performance';
    RAISE NOTICE 'Views created: customer_summary, account_transaction_summary';
END $$;
