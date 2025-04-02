import pandas as pd
import re
from datetime import datetime
import json
from utils.vendor_database import match_vendor, VENDOR_DATABASE

def categorize_transactions(df, categories):
    """
    Categorize transactions based on transaction description and provided categories.
    
    Args:
        df: DataFrame containing transactions
        categories: Dictionary mapping categories to lists of keywords/subcategories
    
    Returns:
        DataFrame with added 'category' and 'subcategory' columns
    """
    if df.empty:
        return df
    
    # Create copies to avoid SettingWithCopyWarning
    result_df = df.copy()
    
    # Initialize default categories
    result_df['category'] = 'Uncategorized'
    result_df['subcategory'] = 'Other'
    
    # Don't immediately categorize all positive amounts as income
    # We'll use vendor matching first, and only use this as a fallback
    # Only set positive amounts as Income after vendor matching, not before
    
    # Define income-related keywords
    income_keywords = [
        'salary', 'wage', 'payroll', 'direct deposit', 'payment received', 
        'dividend', 'interest', 'refund', 'cashback', 'tax return', 'tax refund',
        'deposit', 'credit', 'income', 'bonus', 'commission', 'pension', 'benefit',
        'incoming', 'credit in', 'paid in', 'payment in', 'transfer in'
    ]
    
    # Scan descriptions for income keywords
    descriptions_lower = result_df['description'].str.lower()
    
    # Find transactions that are negative but contain income keywords (incorrect sign)
    incorrect_income = (result_df['amount'] < 0) & descriptions_lower.apply(
        lambda desc: any(keyword in desc for keyword in income_keywords)
    )
    
    # Special case for Payward/cryptocurrency investments
    payward_transactions = descriptions_lower.apply(lambda desc: 'payward' in desc)
    
    # Check for internal transfers between accounts
    transfer_keywords = ['saver', 'saving', 'transfer to', 'transfer from', 'instant saver', 'instant access']
    internal_transfer_mask = descriptions_lower.apply(
        lambda desc: any(keyword in desc for keyword in transfer_keywords)
    )
    
    # Find transactions that are positive but don't look like income
    expense_keywords = [
        'payment to', 'purchase', 'fee', 'charge', 'bill', 'debit', 'withdrawal',
        'card payment', 'subscription', 'order', 'uber', 'lyft', 'online payment',
        'direct debit', 'transfer to', 'payment out', 'paid out'
    ]
    
    incorrect_expense = (result_df['amount'] > 0) & descriptions_lower.apply(
        lambda desc: any(keyword in desc for keyword in expense_keywords)
    )
    
    # Apply corrections based on keywords
    result_df.loc[incorrect_income & ~payward_transactions, 'category'] = 'Income'
    result_df.loc[payward_transactions, 'category'] = 'Savings'
    result_df.loc[payward_transactions, 'subcategory'] = 'Investments'
    
    # Mark internal transfers
    result_df.loc[internal_transfer_mask, 'category'] = 'Transfer'
    result_df.loc[internal_transfer_mask, 'subcategory'] = 'Internal Transfer'
    
    result_df.loc[incorrect_expense, 'category'] = 'Uncategorized'  # Will be categorized in next step
    
    # Create a description lowercase column for matching purposes
    descriptions = result_df['description'].str.lower()
    
    # Print sample transactions for debugging
    print("\nSample transaction descriptions for matching:")
    sample_descriptions = descriptions.head(10).tolist()
    for desc in sample_descriptions:
        print(f"- '{desc}'")
        
    # Print full dataframe for debugging
    print("\nFull dataframe sample:")
    print(result_df.head(10).to_string())
    
    # Define keywords for common categories
    category_keywords = {
        'Housing': [
            'rent', 'mortgage', 'home', 'apartment', 'electric', 'water', 'gas', 'utility',
            'utilities', 'internet', 'sewage', 'waste', 'homeowner', 'hoa', 'maintenance',
            'repair', 'lawn', 'garden'
        ],
        'Transportation': [
            'gas', 'gasoline', 'fuel', 'uber', 'lyft', 'taxi', 'car', 'auto', 'vehicle',
            'public transit', 'bus', 'train', 'subway', 'metro', 'parking', 'toll',
            'maintenance', 'repair', 'insurance', 'dmv', 'registration'
        ],
        'Food': [
            'grocery', 'groceries', 'supermarket', 'market', 'food', 'restaurant', 'cafe',
            'coffee', 'diner', 'dinner', 'lunch', 'breakfast', 'take-out', 'takeout',
            'delivery', 'grubhub', 'doordash', 'ubereats', 'bakery', 'pizza'
        ],
        'Healthcare': [
            'doctor', 'hospital', 'medical', 'dental', 'dentist', 'pharmacy', 'prescription',
            'drug', 'health', 'insurance', 'therapy', 'gym', 'fitness', 'vitamin', 'eyecare',
            'optometrist', 'eyeglasses', 'contacts'
        ],
        'Entertainment': [
            'movie', 'theatre', 'theater', 'concert', 'music', 'spotify', 'netflix',
            'hulu', 'disney', 'amazon prime', 'streaming', 'game', 'book', 'hobby',
            'ticket', 'event', 'sports', 'subscription'
        ],
        'Shopping': [
            'amazon', 'walmart', 'target', 'clothing', 'apparel', 'department', 'store',
            'mall', 'retail', 'electronics', 'computer', 'phone', 'merchandise', 'ebay',
            'online', 'purchase', 'shop'
        ],
        'Education': [
            'school', 'university', 'college', 'tuition', 'education', 'student', 'loan',
            'book', 'course', 'class', 'degree', 'training'
        ],
        'Travel': [
            'hotel', 'airbnb', 'airline', 'flight', 'travel', 'trip', 'vacation',
            'rental car', 'cruise', 'tour', 'booking', 'resort', 'airport'
        ],
        'Savings': [
            'transfer', 'savings', 'investment', 'deposit', 'stock', 'bond', 'retirement',
            '401k', 'ira', 'roth', 'etf', 'mutual fund'
        ],
        'Miscellaneous': [
            'gift', 'donation', 'charity', 'fee', 'interest', 'tax', 'insurance',
            'subscription', 'dues', 'membership', 'service', 'misc'
        ]
    }
    
    # Detect if subcategories exist in categories
    has_subcats = all(isinstance(v, list) for v in categories.values())
    
    # For each description, find the best matching category
    for idx, row in result_df.iterrows():
        # Skip if the categorization was successful via vendor matching
        if row['category'] != 'Uncategorized':
            continue
        
        # Get description for current transaction
        desc = row['description']
        
        # Get subcategory if it exists in the input data
        subcategory = None
        if 'subcategory' in df.columns:
            subcategory = row.get('subcategory')
        elif 'Subcategory' in df.columns:
            subcategory = df.iloc[idx].get('Subcategory')
        elif 'raw_subcategory' in df.columns:
            subcategory = row.get('raw_subcategory')
        
        # Get amount for better categorization
        amount = row['amount']
        
        # Try to match with known vendor database first (most accurate)
        vendor_match = match_vendor(desc, subcategory, amount)
        if vendor_match:
            result_df.loc[idx, 'category'] = vendor_match['category']
            result_df.loc[idx, 'subcategory'] = vendor_match['subcategory']
            continue
        
        # If no vendor match, use keyword-based matching as fallback
        best_match = None
        max_score = 0
        
        for category, keywords in category_keywords.items():
            # Skip categories that don't exist in the user's categories
            if category not in categories:
                continue
                
            # Calculate match score (number of keyword matches)
            score = sum(1 for keyword in keywords if keyword in desc)
            
            if score > max_score:
                max_score = score
                best_match = category
        
        # Assign category if a match was found
        if best_match and max_score > 0:
            result_df.iloc[idx, result_df.columns.get_loc('category')] = best_match
            
            # Try to find a matching subcategory
            if has_subcats:
                subcats = categories.get(best_match, [])
                best_subcat = None
                max_subscore = 0
                
                for subcat in subcats:
                    subcat_lower = subcat.lower()
                    if subcat_lower in desc:
                        # Direct match
                        best_subcat = subcat
                        break
                    else:
                        # Partial match score
                        words = set(subcat_lower.split())
                        desc_words = set(desc.split())
                        overlap = len(words.intersection(desc_words))
                        if overlap > max_subscore:
                            max_subscore = overlap
                            best_subcat = subcat
                
                if best_subcat:
                    result_df.iloc[idx, result_df.columns.get_loc('subcategory')] = best_subcat
                elif subcats:
                    # Default to first subcategory
                    result_df.iloc[idx, result_df.columns.get_loc('subcategory')] = subcats[0]
    
    # Final pass: Any remaining uncategorized positive amounts should be marked as income
    remaining_uncategorized = (result_df['category'] == 'Uncategorized') & (result_df['amount'] > 0)
    result_df.loc[remaining_uncategorized, 'category'] = 'Income'
    result_df.loc[remaining_uncategorized, 'subcategory'] = 'Other Income'
    
    return result_df

def calculate_summary(df):
    """
    Calculate financial summary statistics from transaction data.
    
    Args:
        df: DataFrame containing categorized transactions
    
    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {
            'total_income': 0,
            'total_expenses': 0,
            'net_savings': 0,
            'savings_rate': 0,
            'top_income_category': None,
            'top_income_subcategory': None,
            'top_expense_category': None,
            'expense_by_category': {},
            'income_by_category': {},
            'income_by_subcategory': {},
            'transaction_types': {'income': 0, 'expense': 0},
            'income_transactions': [],
            'expense_transactions': [],
            'monthly_net': {}
        }
    
    # Calculate income and expenses based on both sign and categorization
    # Income is any positive amount with 'Income' category, plus any incorrect sign transactions
    income_mask = (df['category'] == 'Income')
    income_df = df[income_mask]
    
    # For income transactions with negative values, convert to positive
    income_df.loc[income_df['amount'] < 0, 'amount'] = income_df.loc[income_df['amount'] < 0, 'amount'].abs()
    
    # Calculate total income
    total_income = income_df['amount'].sum()
    
    # Special handling for transfer categories (like Investment transfers and Internal Transfers)
    payward_mask = df['description'].str.lower().str.contains('payward')
    transfer_mask = df['category'] == 'Transfer'
    
    # Separate out internal bank transfers
    transfer_df = df[transfer_mask].copy()
    
    # Separate out investment transfers like Payward
    investment_df = df[payward_mask].copy()
    
    # Remaining transactions (non-income, non-transfer, non-payward) are regular expenses
    expense_df = df[~income_mask & ~transfer_mask & ~payward_mask]
    
    # Make sure all expenses are negative
    # For expense transactions with positive values, convert to negative
    expense_df.loc[expense_df['amount'] > 0, 'amount'] = -expense_df.loc[expense_df['amount'] > 0, 'amount']
    
    # Combine all non-income dataframes (expenses, transfers, investments)
    expense_df = pd.concat([expense_df, transfer_df, investment_df])
    
    # Calculate total expenses (always positive for display)
    total_expenses = abs(expense_df['amount'].sum())
    
    # Calculate net savings
    net_savings = total_income - total_expenses
    
    # Calculate savings rate
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    # Calculate expense by category
    expense_by_category = expense_df.groupby('category')['amount'].sum().abs().to_dict()
    
    # Calculate income breakdown by subcategory
    income_by_subcategory = income_df.groupby('subcategory')['amount'].sum().to_dict()
    
    # Calculate monthly net
    df['month'] = df['date'].dt.to_period('M')
    monthly_net = df.groupby('month')['amount'].sum().to_dict()
    # Convert period index to string for JSON serialization
    monthly_net = {str(k): float(v) for k, v in monthly_net.items()}
    
    # Get top categories for expenses
    top_expense_category = max(expense_by_category.items(), key=lambda x: x[1])[0] if expense_by_category else None
    
    # Create income by main category too for backwards compatibility
    income_by_category = {"Income": total_income}
    
    # Get top income subcategory
    top_income_subcategory = max(income_by_subcategory.items(), key=lambda x: x[1])[0] if income_by_subcategory else None
    top_income_category = "Income"  # For backwards compatibility
    
    # Create a breakdown of transactions by type (income vs expense)
    transaction_types = {
        'income': income_df.shape[0],
        'expense': expense_df.shape[0]
    }
    
    # Create a list of transactions marked as income and expense
    income_transactions = income_df[['date', 'description', 'amount', 'subcategory']].sort_values('amount', ascending=False).head(10).to_dict('records')
    expense_transactions = expense_df[['date', 'description', 'amount', 'category', 'subcategory']].sort_values('amount').head(10).to_dict('records')
    
    # Convert date objects to strings for JSON serialization
    for tx in income_transactions:
        tx['date'] = tx['date'].strftime('%Y-%m-%d') if pd.notnull(tx['date']) else None
        tx['amount'] = float(tx['amount'])
    
    for tx in expense_transactions:
        tx['date'] = tx['date'].strftime('%Y-%m-%d') if pd.notnull(tx['date']) else None
        tx['amount'] = float(abs(tx['amount']))  # Make positive for display
    
    return {
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'net_savings': float(net_savings),
        'savings_rate': float(savings_rate),
        'top_expense_category': top_expense_category,
        'top_income_category': top_income_category,  # For backward compatibility
        'top_income_subcategory': top_income_subcategory,
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,  # For backward compatibility
        'income_by_subcategory': income_by_subcategory,
        'transaction_types': transaction_types,
        'income_transactions': income_transactions,
        'expense_transactions': expense_transactions,
        'monthly_net': monthly_net
    }
