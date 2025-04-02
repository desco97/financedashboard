import pandas as pd
import sys
from utils.vendor_database import match_vendor
from utils.file_handler import parse_csv
from utils.data_processor import categorize_transactions

# Print individual vendor matches for testing
print('Checking basic vendor matching:')
print('Checking vendor match for: BUPA')
print(match_vendor('BUPA'))
print('\nChecking vendor match for: BUPA Central')
print(match_vendor('BUPA Central'))
print('\nChecking vendor match for: Direct Debit to BUPA Central')
print(match_vendor('Direct Debit to BUPA Central'))

# Run tests on a CSV file if provided
if len(sys.argv) > 1:
    csv_file = sys.argv[1]
    print(f"\nTesting CSV parsing for: {csv_file}")
    
    # Open the file
    with open(csv_file, 'rb') as file:
        try:
            # Parse the CSV file
            df = parse_csv(file)
            
            # Print the basic info about the parsed DataFrame
            print(f"\nParsed CSV with {len(df)} rows and columns: {df.columns.tolist()}")
            print("\nSample of parsed data:")
            print(df.head(3))
            
            # Print sample of raw transaction data
            print("\nSample transaction descriptions for matching:")
            for desc in df['description'].head(10):
                print(f"- '{desc}'")
                
            # Print full dataframe sample with all columns
            print("\nFull dataframe sample:")
            pd.set_option('display.max_columns', None)
            print(df.head(10))
                
            # Test categorization
            categories = {
                'Income': ['Salary', 'Dividends', 'Interest', 'Refund', 'Tax Refund'],
                'Bills & Payments': ['Utilities', 'Rent', 'Mortgage', 'Direct Debit', 'Credit Card'],
                'Food': ['Groceries', 'Dining', 'Fast Food', 'Coffee Shops'],
                'Healthcare': ['Medical', 'Pharmacy', 'Health Insurance', 'Vision', 'Dental'],
                'Insurance': ['Life Insurance', 'Auto Insurance', 'Home Insurance', 'Property Insurance'],
                'Shopping': ['Clothing', 'Electronics', 'Home Furnishings', 'Online Shopping'],
                'Entertainment': ['Movies', 'Streaming Services', 'Music', 'Events'],
                'Transportation': ['Public Transit', 'Taxi', 'Fuel', 'Parking'],
                'Travel': ['Flights', 'Accommodation', 'Car Rental'],
                'Investments': ['Brokerage', 'Trading Platform', 'Cryptocurrency'],
                'Transfer': ['Bank Transfer', 'Money Transfer', 'Internal Transfer']
            }
            
            # Print if the dataframe has a subcategory column
            if 'subcategory' in df.columns:
                print("\nDetected 'subcategory' column in dataframe with values:")
                for subcat in df['subcategory'].unique():
                    count = df[df['subcategory'] == subcat].shape[0]
                    print(f"- '{subcat}': {count} transactions")
                    
            # Categorize the transactions
            categorized_df = categorize_transactions(df, categories)
            
            # Print a few categorized transactions with detailed information
            print("\nSample of categorized transactions:")
            for idx, row in categorized_df.head(15).iterrows():
                # Make a separate match_vendor call to show the matching process
                from utils.vendor_database import match_vendor
                original_subcategory = row.get('raw_subcategory', 'N/A')
                match_result = match_vendor(row['description'], original_subcategory, row['amount'])
                
                match_status = "MATCHED" if match_result else "NO MATCH"
                
                print(f"Transaction #{idx}:")
                print(f"  Date: {row['date'].strftime('%Y-%m-%d')}")
                print(f"  Description: {row['description']}")
                print(f"  Amount: £{row['amount']:.2f}")
                print(f"  Original Subcategory: {original_subcategory}")
                print(f"  Final Category: {row['category']}")
                print(f"  Final Subcategory: {row['subcategory']}")
                print(f"  Match Status: {match_status}")
                if match_result:
                    print(f"  Vendor Match: {match_result.get('category')}/{match_result.get('subcategory')}")
                print("")
            
            # Calculate income/expense breakdown
            income_df = categorized_df[categorized_df['category'] == 'Income']
            expense_df = categorized_df[categorized_df['category'] != 'Income']
            
            total_income = income_df['amount'].sum()
            total_expenses = abs(expense_df['amount'].sum())
            net_savings = total_income - total_expenses
            
            print(f"\nFinancial Summary:")
            print(f"Total Income: £{total_income:.2f}")
            print(f"Total Expenses: £{total_expenses:.2f}")
            print(f"Net Savings: £{net_savings:.2f}")
            print(f"Savings Rate: {(net_savings/total_income*100):.1f}% of income")
            
            # Print expense breakdown by category
            print("\nExpense Breakdown by Category:")
            for category, amount in expense_df.groupby('category')['amount'].sum().items():
                print(f"  {category}: £{abs(amount):.2f}")
            
            # Print income breakdown by subcategory
            print("\nIncome Breakdown by Subcategory:")
            for subcategory, amount in income_df.groupby('subcategory')['amount'].sum().items():
                print(f"  {subcategory}: £{amount:.2f}")
                
        except Exception as e:
            print(f"Error processing CSV file: {e}")
