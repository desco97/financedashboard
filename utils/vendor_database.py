"""
Vendor database and smart categorization for the Personal Finance App.
This module provides a database of well-known vendors and merchants, along with
their appropriate categorization for accurate transaction classification.
"""
import re

# Dictionary of known merchants and their categories
# Format: 'merchant_name': {'category': 'Category', 'subcategory': 'Subcategory'}
VENDOR_DATABASE = {
    # Payment Services & Credit Cards
    'amex': {'category': 'Bills & Payments', 'subcategory': 'Credit Card'},
    'american express': {'category': 'Bills & Payments', 'subcategory': 'Credit Card'},
    'mastercard': {'category': 'Bills & Payments', 'subcategory': 'Credit Card'},
    'visa': {'category': 'Bills & Payments', 'subcategory': 'Credit Card'},
    'paypal': {'category': 'Shopping', 'subcategory': 'Online Services'},
    'stripe': {'category': 'Shopping', 'subcategory': 'Online Services'},
    'square': {'category': 'Shopping', 'subcategory': 'Retail'},
    'venmo': {'category': 'Transfer', 'subcategory': 'Money Transfer'},
    'zelle': {'category': 'Transfer', 'subcategory': 'Money Transfer'},
    'cash app': {'category': 'Transfer', 'subcategory': 'Money Transfer'},
    'etoro': {'category': 'Investments', 'subcategory': 'Trading Platform'},
    'payward': {'category': 'Savings', 'subcategory': 'Investments'},
    'kraken': {'category': 'Savings', 'subcategory': 'Investments'},
    'direct debit': {'category': 'Bills & Payments', 'subcategory': 'Direct Debit'},
    'counter credit': {'category': 'Income', 'subcategory': 'Deposit'},
    'hmrc': {'category': 'Bills & Payments', 'subcategory': 'Taxes'},
    'hmrc gov.uk': {'category': 'Bills & Payments', 'subcategory': 'Taxes'},
    'tax': {'category': 'Bills & Payments', 'subcategory': 'Taxes'},
    
    # UK-specific Banking Terms
    'instant saver': {'category': 'Transfer', 'subcategory': 'Internal Transfer'},
    'instant access': {'category': 'Transfer', 'subcategory': 'Internal Transfer'},
    'saver account': {'category': 'Transfer', 'subcategory': 'Internal Transfer'},
    'isa': {'category': 'Savings', 'subcategory': 'ISA'},
    'cash isa': {'category': 'Savings', 'subcategory': 'ISA'},
    'stocks and shares isa': {'category': 'Savings', 'subcategory': 'ISA'},
    
    # UK Banks
    'barclays': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'hsbc': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'lloyds': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'natwest': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'nationwide': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'santander': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'monzo': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'starling': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'revolut': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    
    # Banking & Investments
    'bank transfer': {'category': 'Transfer', 'subcategory': 'Bank Transfer'},
    'direct deposit': {'category': 'Income', 'subcategory': 'Salary/Wages'},
    'interest': {'category': 'Income', 'subcategory': 'Interest'},
    'dividend': {'category': 'Income', 'subcategory': 'Dividends'},
    'vanguard': {'category': 'Investments', 'subcategory': 'Brokerage'},
    'fidelity': {'category': 'Investments', 'subcategory': 'Brokerage'},
    'schwab': {'category': 'Investments', 'subcategory': 'Brokerage'},
    'robinhood': {'category': 'Investments', 'subcategory': 'Brokerage'},
    'etrade': {'category': 'Investments', 'subcategory': 'Brokerage'},
    'td ameritrade': {'category': 'Investments', 'subcategory': 'Brokerage'},
    'ramco': {'category': 'Income', 'subcategory': 'Business Income'},
    'ramco manor park': {'category': 'Income', 'subcategory': 'Business Income'},
    'jn desai limited': {'category': 'Income', 'subcategory': 'Business Income'},
    'instant saver': {'category': 'Transfer', 'subcategory': 'Internal Transfer'},
    'saver': {'category': 'Transfer', 'subcategory': 'Internal Transfer'},
    'astrenska': {'category': 'Income', 'subcategory': 'Insurance Payout'},
    'astrenska insuranc': {'category': 'Income', 'subcategory': 'Insurance Payout'},
    
    # Groceries & Supermarkets
    'tesco': {'category': 'Food', 'subcategory': 'Groceries'},
    'sainsbury': {'category': 'Food', 'subcategory': 'Groceries'},
    'asda': {'category': 'Food', 'subcategory': 'Groceries'},
    'waitrose': {'category': 'Food', 'subcategory': 'Groceries'},
    'morrisons': {'category': 'Food', 'subcategory': 'Groceries'},
    'aldi': {'category': 'Food', 'subcategory': 'Groceries'},
    'lidl': {'category': 'Food', 'subcategory': 'Groceries'},
    'kroger': {'category': 'Food', 'subcategory': 'Groceries'},
    'walmart': {'category': 'Food', 'subcategory': 'Groceries'},
    'target': {'category': 'Food', 'subcategory': 'Groceries'},
    'safeway': {'category': 'Food', 'subcategory': 'Groceries'},
    'trader joe': {'category': 'Food', 'subcategory': 'Groceries'},
    'whole foods': {'category': 'Food', 'subcategory': 'Groceries'},
    'costco': {'category': 'Food', 'subcategory': 'Groceries'},
    'sams club': {'category': 'Food', 'subcategory': 'Groceries'},
    
    # Dining & Restaurants
    'mcdonalds': {'category': 'Food', 'subcategory': 'Fast Food'},
    'mcdonald\'s': {'category': 'Food', 'subcategory': 'Fast Food'},
    'burger king': {'category': 'Food', 'subcategory': 'Fast Food'},
    'wendys': {'category': 'Food', 'subcategory': 'Fast Food'},
    'starbucks': {'category': 'Food', 'subcategory': 'Coffee Shops'},
    'costa': {'category': 'Food', 'subcategory': 'Coffee Shops'},
    'pret': {'category': 'Food', 'subcategory': 'Coffee Shops'},
    'subway': {'category': 'Food', 'subcategory': 'Fast Food'},
    'kfc': {'category': 'Food', 'subcategory': 'Fast Food'},
    'taco bell': {'category': 'Food', 'subcategory': 'Fast Food'},
    'pizza hut': {'category': 'Food', 'subcategory': 'Dining'},
    'dominos': {'category': 'Food', 'subcategory': 'Dining'},
    'domino\'s': {'category': 'Food', 'subcategory': 'Dining'},
    'chipotle': {'category': 'Food', 'subcategory': 'Dining'},
    'nandos': {'category': 'Food', 'subcategory': 'Dining'},
    'greggs': {'category': 'Food', 'subcategory': 'Fast Food'},
    
    # Food Delivery Services
    'ubereats': {'category': 'Food', 'subcategory': 'Food Delivery'},
    'uber eats': {'category': 'Food', 'subcategory': 'Food Delivery'},
    'doordash': {'category': 'Food', 'subcategory': 'Food Delivery'},
    'grubhub': {'category': 'Food', 'subcategory': 'Food Delivery'},
    'deliveroo': {'category': 'Food', 'subcategory': 'Food Delivery'},
    'just eat': {'category': 'Food', 'subcategory': 'Food Delivery'},
    
    # Retail & Shopping
    'amazon': {'category': 'Shopping', 'subcategory': 'Online Shopping'},
    'ebay': {'category': 'Shopping', 'subcategory': 'Online Shopping'},
    'etsy': {'category': 'Shopping', 'subcategory': 'Online Shopping'},
    'apple': {'category': 'Shopping', 'subcategory': 'Electronics'},
    'best buy': {'category': 'Shopping', 'subcategory': 'Electronics'},
    'ikea': {'category': 'Shopping', 'subcategory': 'Home Furnishings'},
    'wayfair': {'category': 'Shopping', 'subcategory': 'Home Furnishings'},
    'home depot': {'category': 'Shopping', 'subcategory': 'Home Improvement'},
    'lowes': {'category': 'Shopping', 'subcategory': 'Home Improvement'},
    'b&q': {'category': 'Shopping', 'subcategory': 'Home Improvement'},
    'homebase': {'category': 'Shopping', 'subcategory': 'Home Improvement'},
    'target': {'category': 'Shopping', 'subcategory': 'Department Store'},
    'marshalls': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'tj maxx': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'tk maxx': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'foot locker': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'primark': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'zara': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'h&m': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'asos': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'next': {'category': 'Shopping', 'subcategory': 'Clothing'},
    'marks & spencer': {'category': 'Shopping', 'subcategory': 'Department Store'},
    'm&s': {'category': 'Shopping', 'subcategory': 'Department Store'},
    'john lewis': {'category': 'Shopping', 'subcategory': 'Department Store'},
    'argos': {'category': 'Shopping', 'subcategory': 'Department Store'},
    'debenhams': {'category': 'Shopping', 'subcategory': 'Department Store'},
    
    # Transportation & Travel
    'uber': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'lyft': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'bolt': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'gett': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'free now': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'black cab': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'taxi': {'category': 'Transportation', 'subcategory': 'Taxi'},
    'tube': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'tfl': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'transport for london': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'train': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'bus': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'oyster': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'underground': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'subway': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'avis': {'category': 'Transportation', 'subcategory': 'Car Rental'},
    'hertz': {'category': 'Transportation', 'subcategory': 'Car Rental'},
    'enterprise': {'category': 'Transportation', 'subcategory': 'Car Rental'},
    'zipcar': {'category': 'Transportation', 'subcategory': 'Car Rental'},
    'national rail': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'british rail': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'amtrak': {'category': 'Transportation', 'subcategory': 'Public Transit'},
    'airline': {'category': 'Travel', 'subcategory': 'Flights'},
    'british airways': {'category': 'Travel', 'subcategory': 'Flights'},
    'easyjet': {'category': 'Travel', 'subcategory': 'Flights'},
    'ryanair': {'category': 'Travel', 'subcategory': 'Flights'},
    'delta': {'category': 'Travel', 'subcategory': 'Flights'},
    'american airlines': {'category': 'Travel', 'subcategory': 'Flights'},
    'united': {'category': 'Travel', 'subcategory': 'Flights'},
    'southwest': {'category': 'Travel', 'subcategory': 'Flights'},
    'jet blue': {'category': 'Travel', 'subcategory': 'Flights'},
    'virgin atlantic': {'category': 'Travel', 'subcategory': 'Flights'},
    'emirates': {'category': 'Travel', 'subcategory': 'Flights'},
    'hotel': {'category': 'Travel', 'subcategory': 'Accommodation'},
    'hilton': {'category': 'Travel', 'subcategory': 'Accommodation'},
    'marriott': {'category': 'Travel', 'subcategory': 'Accommodation'},
    'airbnb': {'category': 'Travel', 'subcategory': 'Accommodation'},
    'booking.com': {'category': 'Travel', 'subcategory': 'Accommodation'},
    'expedia': {'category': 'Travel', 'subcategory': 'Travel Services'},
    'trivago': {'category': 'Travel', 'subcategory': 'Travel Services'},
    
    # Utilities & Housing
    'rent': {'category': 'Housing', 'subcategory': 'Rent'},
    'mortgage': {'category': 'Housing', 'subcategory': 'Mortgage'},
    'council tax': {'category': 'Housing', 'subcategory': 'Property Tax'},
    'property tax': {'category': 'Housing', 'subcategory': 'Property Tax'},
    'water': {'category': 'Utilities', 'subcategory': 'Water'},
    'electric': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'electricity': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'gas': {'category': 'Utilities', 'subcategory': 'Gas'},
    'heating': {'category': 'Utilities', 'subcategory': 'Gas'},
    'internet': {'category': 'Utilities', 'subcategory': 'Internet'},
    'broadband': {'category': 'Utilities', 'subcategory': 'Internet'},
    'wifi': {'category': 'Utilities', 'subcategory': 'Internet'},
    'sewage': {'category': 'Utilities', 'subcategory': 'Water'},
    'waste': {'category': 'Utilities', 'subcategory': 'Waste Management'},
    'comcast': {'category': 'Utilities', 'subcategory': 'Internet'},
    'xfinity': {'category': 'Utilities', 'subcategory': 'Internet'},
    'verizon': {'category': 'Utilities', 'subcategory': 'Phone'},
    'at&t': {'category': 'Utilities', 'subcategory': 'Phone'},
    't-mobile': {'category': 'Utilities', 'subcategory': 'Phone'},
    'british gas': {'category': 'Utilities', 'subcategory': 'Gas'},
    'british telecom': {'category': 'Utilities', 'subcategory': 'Phone'},
    'bt': {'category': 'Utilities', 'subcategory': 'Internet'},
    'eon': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'edf': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'scottish power': {'category': 'Utilities', 'subcategory': 'Electricity'},
    'thames water': {'category': 'Utilities', 'subcategory': 'Water'},
    'severn trent': {'category': 'Utilities', 'subcategory': 'Water'},
    'virgin media': {'category': 'Utilities', 'subcategory': 'Internet'},
    'sky': {'category': 'Utilities', 'subcategory': 'TV/Internet'},
    
    # Telecommunications
    'vodafone': {'category': 'Utilities', 'subcategory': 'Phone'},
    'o2': {'category': 'Utilities', 'subcategory': 'Phone'},
    'ee': {'category': 'Utilities', 'subcategory': 'Phone'},
    'three': {'category': 'Utilities', 'subcategory': 'Phone'},
    'giffgaff': {'category': 'Utilities', 'subcategory': 'Phone'},
    'sprint': {'category': 'Utilities', 'subcategory': 'Phone'},
    'cricket': {'category': 'Utilities', 'subcategory': 'Phone'},
    'boost mobile': {'category': 'Utilities', 'subcategory': 'Phone'},
    
    # Subscriptions & Entertainment
    'netflix': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'hulu': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'disney+': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'amazon prime': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'spotify': {'category': 'Entertainment', 'subcategory': 'Music'},
    'apple music': {'category': 'Entertainment', 'subcategory': 'Music'},
    'youtube': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'youtube premium': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'hbo': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'paramount+': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'peacock': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'now tv': {'category': 'Entertainment', 'subcategory': 'Streaming Services'},
    'cinema': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'odeon': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'vue': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'cineworld': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'amc': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'regal': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'cinemark': {'category': 'Entertainment', 'subcategory': 'Movies'},
    'concert': {'category': 'Entertainment', 'subcategory': 'Events'},
    'ticketmaster': {'category': 'Entertainment', 'subcategory': 'Events'},
    'stubhub': {'category': 'Entertainment', 'subcategory': 'Events'},
    'seetickets': {'category': 'Entertainment', 'subcategory': 'Events'},
    
    # Health & Medical
    'bupa': {'category': 'Healthcare', 'subcategory': 'Health Insurance'},
    'bupa central': {'category': 'Healthcare', 'subcategory': 'Health Insurance'},
    'eyecare payments': {'category': 'Healthcare', 'subcategory': 'Vision'},
    'eyecare': {'category': 'Healthcare', 'subcategory': 'Vision'},
    'aig life': {'category': 'Insurance', 'subcategory': 'Life Insurance'},
    'royal london': {'category': 'Insurance', 'subcategory': 'Life Insurance'},
    'clubwise': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'etika': {'category': 'Healthcare', 'subcategory': 'Medical Services'},
    'blue rewards': {'category': 'Banking', 'subcategory': 'Rewards Program'},
    'axa': {'category': 'Healthcare', 'subcategory': 'Health Insurance'},
    'cvs': {'category': 'Healthcare', 'subcategory': 'Pharmacy'},
    'walgreens': {'category': 'Healthcare', 'subcategory': 'Pharmacy'},
    'boots': {'category': 'Healthcare', 'subcategory': 'Pharmacy'},
    'lloyds pharmacy': {'category': 'Healthcare', 'subcategory': 'Pharmacy'},
    'superdrug': {'category': 'Healthcare', 'subcategory': 'Pharmacy'},
    'nhs': {'category': 'Healthcare', 'subcategory': 'Medical Services'},
    'hospital': {'category': 'Healthcare', 'subcategory': 'Medical Services'},
    'clinic': {'category': 'Healthcare', 'subcategory': 'Medical Services'},
    'doctor': {'category': 'Healthcare', 'subcategory': 'Medical Services'},
    'dentist': {'category': 'Healthcare', 'subcategory': 'Dental'},
    'optician': {'category': 'Healthcare', 'subcategory': 'Vision'},
    'vision express': {'category': 'Healthcare', 'subcategory': 'Vision'},
    'specsavers': {'category': 'Healthcare', 'subcategory': 'Vision'},
    'gym': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'fitness': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'pure gym': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'virgin active': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'la fitness': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'planet fitness': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    '24 hour fitness': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'gold\'s gym': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    'equinox': {'category': 'Healthcare', 'subcategory': 'Fitness'},
    
    # Insurance
    'insurance': {'category': 'Insurance', 'subcategory': 'General Insurance'},
    'geico': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'state farm': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'progressive': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'allstate': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'liberty mutual': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'nationwide': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'aviva': {'category': 'Insurance', 'subcategory': 'General Insurance'},
    'direct line': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'admiral': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'churchill': {'category': 'Insurance', 'subcategory': 'Home Insurance'},
    'hastings': {'category': 'Insurance', 'subcategory': 'Auto Insurance'},
    'legal & general': {'category': 'Insurance', 'subcategory': 'Life Insurance'},
    'prudential': {'category': 'Insurance', 'subcategory': 'Life Insurance'},
    
    # Education
    'university': {'category': 'Education', 'subcategory': 'Tuition'},
    'college': {'category': 'Education', 'subcategory': 'Tuition'},
    'school': {'category': 'Education', 'subcategory': 'Tuition'},
    'student loans': {'category': 'Education', 'subcategory': 'Student Loans'},
    'student loan': {'category': 'Education', 'subcategory': 'Student Loans'},
    'sallie mae': {'category': 'Education', 'subcategory': 'Student Loans'},
    'navient': {'category': 'Education', 'subcategory': 'Student Loans'},
    'great lakes': {'category': 'Education', 'subcategory': 'Student Loans'},
    'nelnet': {'category': 'Education', 'subcategory': 'Student Loans'},
    'chegg': {'category': 'Education', 'subcategory': 'Books & Supplies'},
    'textbooks': {'category': 'Education', 'subcategory': 'Books & Supplies'},
    'coursera': {'category': 'Education', 'subcategory': 'Online Courses'},
    'udemy': {'category': 'Education', 'subcategory': 'Online Courses'},
    'skillshare': {'category': 'Education', 'subcategory': 'Online Courses'},
    'student finance': {'category': 'Education', 'subcategory': 'Student Loans'},
    
    # Business & Professional Services
    'payroll': {'category': 'Income', 'subcategory': 'Salary/Wages'},
    'salary': {'category': 'Income', 'subcategory': 'Salary/Wages'},
    'wages': {'category': 'Income', 'subcategory': 'Salary/Wages'},
    'commission': {'category': 'Income', 'subcategory': 'Commission'},
    'freelance': {'category': 'Income', 'subcategory': 'Self-Employment'},
    'consulting': {'category': 'Income', 'subcategory': 'Self-Employment'},
    'upwork': {'category': 'Income', 'subcategory': 'Self-Employment'},
    'fiverr': {'category': 'Income', 'subcategory': 'Self-Employment'},
    'business': {'category': 'Business', 'subcategory': 'General Business'},
    'advertising': {'category': 'Business', 'subcategory': 'Marketing'},
    'office': {'category': 'Business', 'subcategory': 'Office Supplies'},
    'staples': {'category': 'Business', 'subcategory': 'Office Supplies'},
    'office depot': {'category': 'Business', 'subcategory': 'Office Supplies'},
    'quickbooks': {'category': 'Business', 'subcategory': 'Accounting'},
    'xero': {'category': 'Business', 'subcategory': 'Accounting'},
    'freshbooks': {'category': 'Business', 'subcategory': 'Accounting'},
    'mailchimp': {'category': 'Business', 'subcategory': 'Marketing'},
    'godaddy': {'category': 'Business', 'subcategory': 'Web Services'},
    'squarespace': {'category': 'Business', 'subcategory': 'Web Services'},
    'wix': {'category': 'Business', 'subcategory': 'Web Services'},
    'zoom': {'category': 'Business', 'subcategory': 'Software & Services'},
    'microsoft': {'category': 'Business', 'subcategory': 'Software & Services'},
    'adobe': {'category': 'Business', 'subcategory': 'Software & Services'},
    'google': {'category': 'Business', 'subcategory': 'Software & Services'},
    
    # Miscellaneous
    'atm': {'category': 'Cash', 'subcategory': 'ATM Withdrawal'},
    'fee': {'category': 'Fees & Charges', 'subcategory': 'Service Fee'},
    'interest fee': {'category': 'Fees & Charges', 'subcategory': 'Interest'},
    'overdraft': {'category': 'Fees & Charges', 'subcategory': 'Bank Fees'},
    'service charge': {'category': 'Fees & Charges', 'subcategory': 'Bank Fees'},
    'maintenance fee': {'category': 'Fees & Charges', 'subcategory': 'Bank Fees'},
    'late fee': {'category': 'Fees & Charges', 'subcategory': 'Late Payment'},
    'tax': {'category': 'Taxes', 'subcategory': 'General Tax'},
    'hmrc': {'category': 'Taxes', 'subcategory': 'Income Tax'},
    'irs': {'category': 'Taxes', 'subcategory': 'Income Tax'},
    'income tax': {'category': 'Taxes', 'subcategory': 'Income Tax'},
    'property tax': {'category': 'Taxes', 'subcategory': 'Property Tax'},
    'charity': {'category': 'Giving', 'subcategory': 'Charitable Donations'},
    'donation': {'category': 'Giving', 'subcategory': 'Charitable Donations'},
    'gift': {'category': 'Giving', 'subcategory': 'Gifts'},
    'birthday': {'category': 'Giving', 'subcategory': 'Gifts'},
    'wedding': {'category': 'Giving', 'subcategory': 'Gifts'},
}


def match_vendor(description, subcategory=None, amount=None):
    """
    Match a transaction description to a known vendor in the database.
    
    Args:
        description: Transaction description string
        subcategory: Optional subcategory from transaction data (e.g., "Direct Debit")
        amount: Optional transaction amount to help determine if income/expense
        
    Returns:
        Dictionary with category and subcategory if matched, None otherwise
    """
    # Print debug information
    print(f"Matching: Description='{description}', Subcategory='{subcategory}', Amount={amount}")
    if not description:
        return None
    
    # Convert to lowercase for matching
    desc_lower = description.lower().strip()
    
    # Convert subcategory to lowercase if it exists
    subcat_lower = subcategory.lower() if subcategory else ""
    
    # Check for internal transfers based on description - do this first
    # Specific investment platform checks
    if any(platform in desc_lower for platform in ["etoro", "trading 212", "coinbase", "binance"]):
        return {'category': 'Investments', 'subcategory': 'Trading Platform'}
    
    # Cryptocurrency exchanges - categorize as investments    
    if "payward" in desc_lower or "kraken" in desc_lower:
        return {'category': 'Savings', 'subcategory': 'Investments'}
    
    # Comprehensive internal transfer detection
    # 1. Check for personal name combinations in funds transfers
    if any(name in desc_lower for name in ["jay", "desai", "j n desai"]) and ("funds transfer" in subcat_lower or "ft" in desc_lower):
        if "tax" in desc_lower:
            # Tax transfers between accounts (not HMRC payments)
            return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
        elif "richard" not in desc_lower and "fairchild" not in desc_lower:
            # Transfers to self that aren't to other people
            return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
    
    # 2. Check for transfers between bank accounts using account keywords
    for bank_account_term in ["instant saver", "savings account", "isa", "current account"]:
        if bank_account_term in desc_lower:
            return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
    
    # Handle empty or None subcategory
    if not subcategory or subcategory == 'Other':
        # Try to infer from the description if it's a direct debit or card purchase
        if "ddr" in desc_lower or "direct debit" in desc_lower or " dd" in desc_lower:
            subcategory = "Direct Debit"
        elif "bcc" in desc_lower or "card purchase" in desc_lower or "cpm" in desc_lower:
            subcategory = "Card Purchase"
    
    # Check for UK bank subcategories
    if subcategory:
        subcat_lower = subcategory.lower().strip()
        
        # Counter Credit is usually income
        if "counter credit" in subcat_lower:
            # Specific patterns from Barclays
            if "ramco" in desc_lower:
                return {'category': 'Income', 'subcategory': 'Business Income'}
                
            if "jn desai limited" in desc_lower:
                return {'category': 'Income', 'subcategory': 'Business Income'}
                
            if "astrenska" in desc_lower:
                return {'category': 'Income', 'subcategory': 'Insurance Payout'}
                
            if "tax" in desc_lower or "instant saver" in desc_lower or "instant access" in desc_lower:
                return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
                
            # Enhanced internal transfer detection for UK banks
            internal_transfer_keywords = [
                "saver", "savings", "isa", "transfer to", "transfer from", 
                "instant access", "desai", "jay", "bank transfer"
            ]
            
            if any(keyword in desc_lower for keyword in internal_transfer_keywords):
                return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
                
            # Generic patterns
            if "limited" in desc_lower or "ltd" in desc_lower or "llc" in desc_lower:
                return {'category': 'Income', 'subcategory': 'Business Income'}
            elif "salary" in desc_lower or "wage" in desc_lower or "payroll" in desc_lower:
                return {'category': 'Income', 'subcategory': 'Salary/Wages'}
            # Generic income
            return {'category': 'Income', 'subcategory': 'Other Income'}
        
        # Direct Debit is usually bills
        if "direct debit" in subcat_lower:
            # First check for special Direct Debit patterns from Barclays
            # BUPA is health insurance
            if "bupa" in desc_lower:
                return {'category': 'Healthcare', 'subcategory': 'Health Insurance'}
                
            # American Express is credit card payment
            if "american express" in desc_lower or "amex" in desc_lower:
                return {'category': 'Bills & Payments', 'subcategory': 'Credit Card'}
                
            # Eyecare is vision insurance/payments
            if "eyecare" in desc_lower:
                return {'category': 'Healthcare', 'subcategory': 'Vision'}
                
            # AIG Life is life insurance
            if "aig life" in desc_lower:
                return {'category': 'Insurance', 'subcategory': 'Life Insurance'}
                
            # Royal London is usually life insurance
            if "royal london" in desc_lower:
                return {'category': 'Insurance', 'subcategory': 'Life Insurance'}
                
            # Clubwise is usually gym/fitness
            if "clubwise" in desc_lower:
                return {'category': 'Healthcare', 'subcategory': 'Fitness'}
                
            # Etika is usually subscriptions
            if "etika" in desc_lower:
                return {'category': 'Entertainment', 'subcategory': 'Subscription Services'}
                
            # Look for known vendors in the description
            for vendor, categorization in VENDOR_DATABASE.items():
                if vendor in desc_lower:
                    return categorization
                    
            # Generic bill payment
            return {'category': 'Bills & Payments', 'subcategory': 'Direct Debit'}
        
        # Card Purchase is usually shopping/entertainment/dining
        if "card purchase" in subcat_lower:
            # Apple subscriptions
            if "apple.com" in desc_lower:
                return {'category': 'Entertainment', 'subcategory': 'Subscription Services'}
                
            # HMRC tax payments
            if "hmrc" in desc_lower or "gov.uk" in desc_lower:
                return {'category': 'Bills & Payments', 'subcategory': 'Tax Payments'}
                
            # Restaurant/Dining
            if "mcdonalds" in desc_lower:
                return {'category': 'Food', 'subcategory': 'Fast Food'}
                
            # Sainsbury's is groceries
            if "sainsburys" in desc_lower:
                return {'category': 'Food', 'subcategory': 'Groceries'}
                
        # Handle Barclays "Debit" transactions
        if "debit" == subcat_lower:
            # Blue rewards is a fee
            if "blue rewards" in desc_lower:
                return {'category': 'Bills & Payments', 'subcategory': 'Bank Fees'}
                
            # McDonalds is fast food
            if "mcdonalds" in desc_lower:
                return {'category': 'Food', 'subcategory': 'Fast Food'}
                
            # Sainsbury's is groceries
            if "sainsburys" in desc_lower:
                return {'category': 'Food', 'subcategory': 'Groceries'}
                
        # Handle Barclays "Funds Transfer"
        if "funds transfer" in subcat_lower:
            # eToro is investment platform
            if "etoro" in desc_lower:
                return {'category': 'Investments', 'subcategory': 'Trading Platform'}
                
            # Tax payments to government
            if "hmrc" in desc_lower or "gov.uk" in desc_lower:
                return {'category': 'Bills & Payments', 'subcategory': 'Tax Payments'}
                
            # Internal transfers with "tax" in the description (likely between accounts)
            if "tax" in desc_lower:
                return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
                
            # Payward/Kraken is cryptocurrency - categorized as Savings/Investments
            if "payward" in desc_lower:
                return {'category': 'Savings', 'subcategory': 'Investments'}
            
            # Handle transfers to/from self - look for common name patterns
            if ("jay" in desc_lower or "desai" in desc_lower or
                "transfer to" in desc_lower or "transfer from" in desc_lower or
                "instant saver" in desc_lower or "savings account" in desc_lower):
                return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
    
    # Quick check for common UK transaction prefixes and special cases
    # First check for internal transfers from savings accounts
    if "instant saver" in desc_lower or ("saver" in desc_lower and "tax" in desc_lower):
        return {'category': 'Transfer', 'subcategory': 'Internal Transfer'}
    
    if "salary" in desc_lower or "wages" in desc_lower:
        return {'category': 'Income', 'subcategory': 'Salary/Wages'}
    
    if "dividend" in desc_lower:
        return {'category': 'Income', 'subcategory': 'Dividends'}
    
    if "interest" in desc_lower and not ("loan" in desc_lower or "mortgage" in desc_lower):
        return {'category': 'Income', 'subcategory': 'Interest'}
        
    if "refund" in desc_lower:
        # Try to determine the refund category
        for vendor, categorization in VENDOR_DATABASE.items():
            if re.search(r'\b' + re.escape(vendor) + r'\b', desc_lower):
                # Return the same category but change subcategory to "Refund"
                return {'category': categorization['category'], 'subcategory': 'Refund'}
        # Generic refund
        return {'category': 'Income', 'subcategory': 'Refund'}
    
    # Check for pay sources
    pay_keywords = ["pay", "payroll", "salary", "wage", "income", "direct deposit"]
    if any(keyword in desc_lower for keyword in pay_keywords):
        return {'category': 'Income', 'subcategory': 'Salary/Wages'}
    
    # Try direct matches first (most specific)
    for vendor, categorization in VENDOR_DATABASE.items():
        # Check if the vendor name appears as a whole word in the description
        if re.search(r'\b' + re.escape(vendor) + r'\b', desc_lower):
            return categorization
    
    # Try contains matches (not strict word boundary)
    for vendor, categorization in VENDOR_DATABASE.items():
        # Skip single-word vendors to avoid false positives
        if ' ' in vendor:
            # For multi-word vendors, we can be less strict
            if vendor in desc_lower:
                return categorization
    
    # If no direct match, try partial matches by breaking down the description
    desc_words = set(desc_lower.split())
    best_match = None
    best_score = 0
    best_vendor_length = 0  # Prefer longer vendor names when ties occur
    
    for vendor, categorization in VENDOR_DATABASE.items():
        vendor_words = set(vendor.split())
        
        # Calculate overlap between vendor words and description words
        overlap = len(vendor_words.intersection(desc_words))
        
        # Calculate match quality
        # For multi-word vendors, we need higher overlap
        required_overlap = 1
        if len(vendor_words) > 2:
            required_overlap = 2
        
        # For a better match:
        # 1. We need more overlapping words than our previous best
        # 2. OR same overlap but the vendor name is longer (more specific)
        # 3. AND we meet the minimum required overlap
        if (overlap > best_score or (overlap == best_score and len(vendor) > best_vendor_length)) and overlap >= required_overlap:
            best_score = overlap
            best_match = categorization
            best_vendor_length = len(vendor)
    
    # Return the best match if we found one with sufficient overlap
    if best_score > 0:
        return best_match
        
    # No match found
    return None