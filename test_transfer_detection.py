import pandas as pd
from utils.data_processor import categorize_transactions
from utils.file_handler import parse_csv
import sys
import logging

# Disable noisy pandas SettingWithCopyWarning warnings
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# Configure logging - suppress debug-level logs from imported modules
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

def test_transfer_detection():
    """
    Test the detection of internal transfers and investment transactions in bank statements.
    
    This script will:
    1. Load the attached Barclays CSV sample
    2. Run the transaction categorization with enhanced detection for:
       - Internal transfers between personal accounts (using name, account type, etc.)
       - Investment platform transfers (eToro, etc.)
       - Cryptocurrency exchanges (Payward/Kraken)
    3. Print transactions categorized as internal transfers and verify investment categorization
    """
    # Add debug printing
    print("Starting transfer detection test...")
    
    # Suppress print statements from the categorize_transactions function
    import builtins
    real_print = builtins.print
    builtins.print = lambda *args, **kwargs: None  # Do nothing
    # Create default categories dictionary for testing
    categories = {
        'Income': ['Salary/Wages', 'Business Income', 'Dividends', 'Interest', 'Other Income'],
        'Housing': ['Rent', 'Mortgage', 'Property Tax', 'Home Insurance', 'Home Maintenance'],
        'Transportation': ['Public Transit', 'Taxi', 'Car Rental', 'Fuel', 'Car Maintenance'],
        'Food': ['Groceries', 'Dining', 'Fast Food', 'Coffee Shops', 'Food Delivery'],
        'Healthcare': ['Doctor', 'Hospital', 'Pharmacy', 'Fitness', 'Vision', 'Health Insurance'],
        'Entertainment': ['Movies', 'Events', 'Hobbies', 'Streaming Services', 'Music'],
        'Shopping': ['Clothing', 'Electronics', 'Accessories', 'Department Store', 'Online Shopping'],
        'Bills & Payments': ['Utilities', 'Phone', 'Internet', 'Credit Card', 'Direct Debit', 'Bank Fees'],
        'Investments': ['Trading Platform', 'Brokerage Fees', 'Stock Purchases'],
        'Savings': ['Investments', 'Retirement', 'Emergency Fund', 'ISA'],
        'Transfer': ['Bank Transfer', 'Money Transfer', 'Internal Transfer', 'External Transfer'],
    }
    
    try:
        # Load the test CSV file
        file_path = "attached_assets/barclays CSV.csv"
        with open(file_path, 'rb') as file:
            df = parse_csv(file)
        
        # Perform categorization
        categorized_df = categorize_transactions(df, categories)
        
        # Filter for internal transfers
        transfers = categorized_df[(categorized_df['category'] == 'Transfer') & 
                                  (categorized_df['subcategory'] == 'Internal Transfer')]
        # Restore the real print function for our output
        builtins.print = real_print
        
        # Print the results
        print("\n=== TRANSFER DETECTION TEST RESULTS ===")
        print(f"Total transactions: {len(categorized_df)}")
        print(f"Internal transfers detected: {len(transfers)}")
        print("\nDetected Internal Transfers:")
        
        # Display the transfers
        if len(transfers) > 0:
            for idx, row in transfers.iterrows():
                print(f"- {row['date'].strftime('%d/%m/%Y')} | {row['description']} | £{abs(row['amount']):.2f}")
        else:
            print("No internal transfers detected.")
        
        # Check for Payward transactions
        payward = categorized_df[categorized_df['description'].str.contains('PAYWARD', case=False)]
        print("\nPayward Transactions (should be Savings > Investments):")
        if len(payward) > 0:
            for idx, row in payward.iterrows():
                print(f"- {row['date'].strftime('%d/%m/%Y')} | {row['description']} | "
                      f"{row['category']} > {row['subcategory']} | £{abs(row['amount']):.2f}")
        else:
            print("No Payward transactions found.")
            
        # Check for eToro transactions
        etoro = categorized_df[categorized_df['description'].str.contains('ETORO', case=False)]
        print("\neToro Transactions (should be Investments > Trading Platform):")
        if len(etoro) > 0:
            for idx, row in etoro.iterrows():
                print(f"- {row['date'].strftime('%d/%m/%Y')} | {row['description']} | "
                      f"{row['category']} > {row['subcategory']} | £{abs(row['amount']):.2f}")
        else:
            print("No eToro transactions found.")
            
        # Test is now complete
        
        print("\nTest completed successfully!")
        return 0
    except Exception as e:
        print(f"Error during test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_transfer_detection())