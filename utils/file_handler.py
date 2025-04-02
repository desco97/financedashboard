import pandas as pd
import tabula
import io
import re
from datetime import datetime

def parse_csv(file):
    """
    Parse a CSV bank statement file into a standardized DataFrame.
    
    Args:
        file: CSV file upload object
    
    Returns:
        DataFrame with standardized columns
    """
    try:
        # Check if this is a Barclays CSV format by reading the first few lines
        file.seek(0)
        header = file.read(1024).decode('utf-8')
        file.seek(0)
        
        # Barclays CSV typically has: Number,Date,Account,Amount,Subcategory,Memo
        if 'Number,Date,Account,Amount,Subcategory,Memo' in header:
            # Special handling for Barclays CSV format
            df = pd.read_csv(file)
            
            # Standardize the column names
            standardized_df = pd.DataFrame()
            standardized_df['date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            standardized_df['description'] = df['Memo'].apply(clean_description)
            standardized_df['amount'] = df['Amount'].astype(float)
            standardized_df['raw_description'] = df['Memo']
            standardized_df['subcategory'] = df['Subcategory']  # Keep original subcategory for reference
            standardized_df['raw_subcategory'] = df['Subcategory']  # Store the raw subcategory for debugging
            
            # Return the standardized DataFrame
            return standardized_df
            
        # If not a Barclays format, proceed with the general approach
        file.seek(0)
        df = pd.read_csv(file)
        
        # Try to identify date, description, and amount columns
        date_columns = []
        description_columns = []
        amount_columns = []
        
        # Look for common column names
        for col in df.columns:
            col_lower = col.lower()
            # Date column detection - including memo and posted date keywords
            if any(keyword in col_lower for keyword in ['date', 'time', 'day', 'post', 'memo', 'transaction date']):
                date_columns.append(col)
            # Description column detection
            elif any(keyword in col_lower for keyword in ['desc', 'narrative', 'details', 'transaction', 'merchant', 'payee', 'name', 'memo', 'description']):
                description_columns.append(col)
            # Amount column detection
            elif any(keyword in col_lower for keyword in ['amount', 'sum', 'value', 'debit', 'credit', 'balance']):
                amount_columns.append(col)
        
        # If we couldn't identify all columns, try a different approach
        if not (date_columns and description_columns and amount_columns):
            # Check column data types
            for col in df.columns:
                # Sample the first few non-null values
                sample = df[col].dropna().head(5)
                if not len(sample):
                    continue
                
                # Check if column could be a date
                if not date_columns:
                    try:
                        # Try parsing as date
                        pd.to_datetime(sample)
                        date_columns.append(col)
                    except:
                        pass
                
                # Check if column could be a description (string)
                if not description_columns and df[col].dtype == 'object':
                    # If most values have more than 10 characters, it's likely a description
                    if sample.str.len().mean() > 10:
                        description_columns.append(col)
                
                # Check if column could be an amount (numeric)
                if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                    # Look for columns that contain currency values
                    # Most transaction amounts should have decimal places
                    sample_values = df[col].dropna().head(50)
                    # Check if values look like money (e.g., have decimals or currency symbols)
                    has_decimals = any('.' in str(v) for v in sample_values if pd.notnull(v))
                    has_currency = any(('$' in str(v) or '£' in str(v) or '€' in str(v)) 
                                      for v in sample_values if isinstance(v, str))
                    # Check the range - transaction amounts are typically between -10000 and 10000
                    in_range = sample_values.abs().mean() < 100000
                    
                    if has_decimals or has_currency or in_range:
                        amount_columns.append(col)
        
        # If we still don't have all required columns, try inferring from position
        if not date_columns:
            # First column is often a date
            date_columns = [df.columns[0]]
        
        if not description_columns:
            # Look for the column with the longest string values
            str_lengths = {col: df[col].astype(str).str.len().mean() for col in df.columns}
            description_columns = [max(str_lengths.items(), key=lambda x: x[1])[0]]
        
        if not amount_columns or len(amount_columns) > 3:
            # Look for columns that look like amounts (with decimals, currencies, etc.)
            potential_amount_cols = []
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]) and col not in date_columns:
                    potential_amount_cols.append(col)
                elif df[col].dtype == 'object':
                    # For string columns, check if they can be converted to numbers after cleaning
                    sample = df[col].dropna().astype(str).head(20)
                    # Remove currency symbols, commas, etc.
                    cleaned = sample.str.replace(r'[$£€,]', '', regex=True)
                    # Check if it can be converted to numeric
                    numeric_values = pd.to_numeric(cleaned, errors='coerce')
                    if numeric_values.notna().sum() > len(sample) * 0.7:  # If more than 70% can be converted
                        potential_amount_cols.append(col)
            
            # Filter columns by looking at the distribution of values
            filtered_amount_cols = []
            for col in potential_amount_cols:
                # Convert to numeric if needed
                if df[col].dtype == 'object':
                    values = pd.to_numeric(df[col].astype(str).str.replace(r'[$£€,]', '', regex=True), errors='coerce')
                else:
                    values = df[col]
                
                # Check if the column has a reasonable range of values for amounts
                if values.notna().any():
                    mean_val = values.abs().mean()
                    if 0.01 <= mean_val <= 10000:  # Typical range for transaction amounts
                        filtered_amount_cols.append(col)
            
            # If we still have too many columns, prioritize by names                
            if filtered_amount_cols:
                amount_columns = filtered_amount_cols
            else:
                amount_columns = potential_amount_cols
        
        # Select columns based on best guess
        date_col = date_columns[0]
        description_col = description_columns[0]
        
        # For amount, we need to handle different bank formats
        # Some banks use separate debit/credit columns, others use a single amount column
        
        # Case 1: Single amount column with positive and negative values
        if len(amount_columns) == 1:
            amount_col = amount_columns[0]
            # Create a raw_description column to preserve original text
            # Also check if there's a subcategory column in the original data
            subcategory_col = None
            for col in df.columns:
                if col.lower() in ['subcategory', 'subcat', 'category', 'type', 'transaction type']:
                    subcategory_col = col
                    break
                    
            result_df = pd.DataFrame({
                'date': pd.to_datetime(df[date_col], errors='coerce', dayfirst=True),
                'description': df[description_col].astype(str),
                'amount': df[amount_col],
                'raw_description': df[description_col].astype(str)  # Keep original description
            })
            
            # Add subcategory column if it exists
            if subcategory_col:
                result_df['subcategory'] = df[subcategory_col]
        
        # Case 2: Separate debit and credit columns
        elif len(amount_columns) >= 2:
            # First, try to identify which columns are debit and credit based on column names
            debit_col = None
            credit_col = None
            
            for col in amount_columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['debit', 'withdrawal', 'expense', 'payment', 'out']):
                    debit_col = col
                elif any(keyword in col_lower for keyword in ['credit', 'deposit', 'income', 'received', 'in']):
                    credit_col = col
            
            # If we couldn't identify by names, try to infer from data patterns
            if not (debit_col and credit_col):
                # Analyze values in each column
                column_stats = {}
                for col in amount_columns:
                    # Count positive, negative and zero values in each column
                    if df[col].dtype == 'object':
                        # Try to convert string values to numeric
                        values = pd.to_numeric(df[col].astype(str).str.replace(r'[$£€,]', '', regex=True), errors='coerce')
                    else:
                        values = df[col]
                    
                    if values.notna().any():
                        pos_count = (values > 0).sum()
                        neg_count = (values < 0).sum()
                        zero_count = (values == 0).sum()
                        total = pos_count + neg_count + zero_count
                        
                        column_stats[col] = {
                            'positive_ratio': pos_count / total if total > 0 else 0,
                            'negative_ratio': neg_count / total if total > 0 else 0,
                            'zero_ratio': zero_count / total if total > 0 else 0,
                            'mean': values.mean() if values.notna().any() else 0
                        }
                
                # Sort columns by characteristics
                # If a column has mostly positive values, it's likely a credit/income column
                # If a column has mostly negative values, it's likely a debit/expense column
                credit_candidates = sorted(
                    [(col, stats['positive_ratio']) for col, stats in column_stats.items()],
                    key=lambda x: x[1], reverse=True
                )
                debit_candidates = sorted(
                    [(col, stats['negative_ratio']) for col, stats in column_stats.items()],
                    key=lambda x: x[1], reverse=True
                )
                
                # Select the best candidates that are different columns
                if credit_candidates and debit_candidates:
                    # If same column has highest positive and negative ratios, it's likely a single amount column
                    if credit_candidates[0][0] == debit_candidates[0][0]:
                        # Use this as a single amount column instead
                        amount_col = credit_candidates[0][0]
                        result_df = pd.DataFrame({
                            'date': pd.to_datetime(df[date_col], errors='coerce', dayfirst=True),
                            'description': df[description_col].astype(str),
                            'amount': df[amount_col]
                        })
                        return result_df
                    else:
                        credit_col = credit_candidates[0][0]
                        # Find the first debit candidate that isn't the credit column
                        for col, _ in debit_candidates:
                            if col != credit_col:
                                debit_col = col
                                break
            
            # If still not identified, use the first two columns
            if not (debit_col and credit_col):
                debit_col = amount_columns[0]
                credit_col = amount_columns[1]
            
            # Create a combined amount column (credit positive, debit negative)
            # Convert columns to numeric first to ensure proper calculation
            credit_values = pd.to_numeric(df[credit_col].astype(str).str.replace(r'[$£€,]', '', regex=True), errors='coerce').fillna(0)
            debit_values = pd.to_numeric(df[debit_col].astype(str).str.replace(r'[$£€,]', '', regex=True), errors='coerce').fillna(0)
            
            # Make sure debit values are negative for consistent representation
            debit_values = -1 * debit_values.abs()
            
            # Combine values (credit is positive, debit is negative)
            df['combined_amount'] = credit_values + debit_values
            
            # When one column is 0 and the other has a value, use that value
            df.loc[credit_values != 0, 'combined_amount'] = credit_values
            df.loc[debit_values != 0, 'combined_amount'] = debit_values
            
            # Also check if there's a subcategory column in the original data
            subcategory_col = None
            for col in df.columns:
                if col.lower() in ['subcategory', 'subcat', 'category', 'type', 'transaction type']:
                    subcategory_col = col
                    break
                    
            result_df = pd.DataFrame({
                'date': pd.to_datetime(df[date_col], errors='coerce', dayfirst=True),
                'description': df[description_col].astype(str),
                'amount': df['combined_amount'],
                'raw_description': df[description_col].astype(str)  # Keep original description
            })
            
            # Add subcategory column if it exists
            if subcategory_col:
                result_df['subcategory'] = df[subcategory_col]
        
        # Clean up the data
        # Remove rows with invalid dates
        result_df = result_df.dropna(subset=['date'])
        
        # Clean description
        result_df['description'] = result_df['description'].apply(lambda x: clean_description(x))
        
        # Ensure amount is numeric
        result_df['amount'] = pd.to_numeric(result_df['amount'], errors='coerce')
        
        # Drop rows with missing amounts
        result_df = result_df.dropna(subset=['amount'])
        
        return result_df
    
    except Exception as e:
        # If automatic parsing fails, try a more generic approach
        try:
            # Just read the CSV without assumptions
            df = pd.read_csv(file)
            
            # Let the user know about the issue
            print(f"Warning: Automatic column detection failed. Using generic parsing. Error: {str(e)}")
            
            # Return the DataFrame with original columns
            return df
        except:
            raise Exception(f"Failed to parse CSV file: {str(e)}")

def parse_pdf(file):
    """
    Parse a PDF bank statement into a standardized DataFrame.
    
    Args:
        file: PDF file upload object
    
    Returns:
        DataFrame with standardized columns
    """
    try:
        # Read PDF tables
        # Convert the uploaded file to bytes for tabula to read
        file_bytes = io.BytesIO(file.read())
        
        # Try to extract tables with multiple settings to maximize success
        try:
            # First attempt with default settings
            tables = tabula.read_pdf(file_bytes, pages='all', multiple_tables=True)
            
            # If no tables found, try with different area settings
            if not tables:
                print("Trying alternate PDF parsing settings...")
                file_bytes.seek(0)  # Reset file pointer
                tables = tabula.read_pdf(
                    file_bytes, 
                    pages='all', 
                    multiple_tables=True,
                    guess=True,
                    lattice=True
                )
            
            # If still no tables, try with stream mode
            if not tables:
                file_bytes.seek(0)
                tables = tabula.read_pdf(
                    file_bytes, 
                    pages='all', 
                    multiple_tables=True,
                    stream=True,
                    guess=False
                )
                
        except Exception as parse_error:
            print(f"PDF parsing error: {str(parse_error)}")
            # Last resort: try with minimal settings
            file_bytes.seek(0)
            tables = tabula.read_pdf(
                file_bytes, 
                pages='all',
                silent=True
            )
        
        if not tables or all(df.empty for df in tables):
            raise Exception("No tables found in the PDF. The PDF may be encrypted, image-based, or in a format not supported by the parser.")
        
        # Remove empty dataframes
        tables = [df for df in tables if not df.empty]
        
        if not tables:
            raise Exception("All extracted tables were empty")
            
        # Print diagnostic information
        print(f"Successfully extracted {len(tables)} tables from PDF")
        for i, table in enumerate(tables):
            print(f"Table {i+1} shape: {table.shape}, columns: {list(table.columns)}")
        
        # Combine all tables
        combined_df = pd.concat(tables, ignore_index=True)
        
        # Try to identify date, description, and amount columns
        date_col = None
        description_col = None
        amount_cols = []
        
        # Print all column names for debugging
        print(f"All columns in combined table: {list(combined_df.columns)}")
        
        for col in combined_df.columns:
            col_str = str(col).lower()
            # Date column detection
            if any(keyword in col_str for keyword in ['date', 'time', 'day', 'posting date', 'trans date', 'post', 'memo', 'transaction date']):
                date_col = col
                print(f"Identified date column: {col}")
            # Description column detection
            elif any(keyword in col_str for keyword in ['desc', 'narrative', 'details', 'transaction', 'merchant', 'payee', 'name', 'reference', 'memo', 'description']):
                description_col = col
                print(f"Identified description column: {col}")
            # Amount column detection
            elif any(keyword in col_str for keyword in ['amount', 'sum', 'value', 'debit', 'credit', 'balance', 'withdrawal', 'deposit']):
                amount_cols.append(col)
                print(f"Identified amount column: {col}")
        
        # If we couldn't identify columns by name, try by content
        if not (date_col and description_col and amount_cols):
            print("Attempting to identify columns by content...")
            # Check each column for date-like content
            for col in combined_df.columns:
                if not date_col:
                    # Sample values and check if they look like dates
                    sample_values = combined_df[col].dropna().astype(str).head(5)
                    print(f"Sample values for column {col}: {sample_values.tolist()}")
                    
                    # Check for column header with "Date" in it
                    if col == "Your transactions" or any(val.lower().startswith('date') for val in sample_values):
                        date_col = col
                        print(f"Found date column by header detection: {col}")
                    else:
                        # Check for date patterns in the content
                        date_patterns = [
                            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
                            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY or DD-MM-YYYY
                            r'\d{2,4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
                            r'\d{1,2}\s[A-Za-z]{3}\s\d{2,4}',  # DD MMM YYYY
                            r'\d{1,2}\s[A-Za-z]{3}'  # DD MMM (without year)
                        ]
                        
                        for pattern in date_patterns:
                            if sample_values.str.contains(pattern, regex=True).any():
                                date_col = col
                                print(f"Found date column by pattern: {col}")
                                break
                
                # Check for description column (longest string values)
                if not description_col and combined_df[col].dtype == 'object':
                    sample_values = combined_df[col].dropna().astype(str).head(5)
                    if sample_values.str.len().mean() > 10:
                        description_col = col
                        print(f"Found description column by length: {col}")
                
                # Check for numeric columns that could be amounts
                try:
                    # Try to convert to numeric after cleaning
                    cleaned_vals = combined_df[col].astype(str).str.replace(r'[,$()+-]', '', regex=True)
                    # Check if at least some values are numeric
                    if pd.to_numeric(cleaned_vals, errors='coerce').notna().any():
                        amount_cols.append(col)
                        print(f"Found amount column by numeric detection: {col}")
                except:
                    pass
        
        # Select columns based on best guess
        # If still missing, use position-based guesses
        if not date_col and len(combined_df.columns) >= 1:
            date_col = combined_df.columns[0]
            print(f"Using first column as date column: {date_col}")
        
        if not description_col and len(combined_df.columns) >= 2:
            description_col = combined_df.columns[1]
            print(f"Using second column as description column: {description_col}")
        
        if not amount_cols and len(combined_df.columns) >= 3:
            amount_cols = [combined_df.columns[2]]
            print(f"Using third column as amount column: {amount_cols[0]}")
        
        # Process the columns to create a standardized DataFrame
        try:
            # Try to convert date strings to datetime
            print(f"Converting dates using column: {date_col}")
            
            # Special handling for UK/European bank statement formats with combined date/description
            if date_col == "Your transactions" or any('date description' in val.lower() for val in combined_df[date_col].astype(str).head(3)):
                print("Using special date extraction for UK bank statement format")
                
                # Create a new date column by extracting dates from the text
                extracted_dates = []
                extracted_descriptions = []
                
                # Process each row
                for idx, row in combined_df.iterrows():
                    text = str(row[date_col])
                    # UK date format: "3 Sep" or "12 Sep"
                    date_match = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', text, re.IGNORECASE)
                    
                    if date_match:
                        day = date_match.group(1)
                        month = date_match.group(2)
                        # Assume current year if not specified
                        year = datetime.now().year
                        date_str = f"{day} {month} {year}"
                        
                        try:
                            # Parse the date
                            extracted_date = pd.to_datetime(date_str, format="%d %b %Y", errors='coerce')
                            extracted_dates.append(extracted_date)
                            
                            # Use the description part (after removing the date)
                            desc = re.sub(r'\d{1,2}\s+[A-Za-z]{3}', '', text, 1).strip()
                            extracted_descriptions.append(desc)
                        except:
                            extracted_dates.append(pd.NaT)
                            extracted_descriptions.append(text)
                    else:
                        extracted_dates.append(pd.NaT)
                        extracted_descriptions.append(text)
                
                # Create Series from the lists
                dates = pd.Series(extracted_dates)
                descriptions = pd.Series(extracted_descriptions)
                print(f"Extracted {dates.notna().sum()} dates from combined date/description field")
                
                # If we also have a separate description column, try to combine the information
                if description_col and description_col != date_col:
                    old_descriptions = combined_df[description_col].astype(str)
                    # Combine where needed
                    for i in range(len(descriptions)):
                        if pd.notna(dates[i]) and descriptions[i] in ["", "Unknown"]:
                            descriptions[i] = old_descriptions[i] if i < len(old_descriptions) else "Unknown"
            else:
                # Standard date parsing
                # First clean the date strings
                date_series = combined_df[date_col].astype(str)
                # Remove any non-date characters that might be present
                date_series = date_series.str.replace(r'[^\d/\-\s\w]', '', regex=True)
                dates = pd.to_datetime(date_series, errors='coerce', dayfirst=True)
            
            # Extract descriptions
            print(f"Extracting descriptions from column: {description_col}")
            descriptions = combined_df[description_col].astype(str)
            
            # Process amount columns
            print(f"Processing amount columns: {amount_cols}")
            if len(amount_cols) == 1:
                # Single amount column
                amount_series = combined_df[amount_cols[0]].astype(str)
                # Replace special characters
                amount_series = amount_series.str.replace(r'[,$\s]', '', regex=True)
                # Handle negative indicators
                amount_series = amount_series.str.replace(r'\((.+)\)', r'-\1', regex=True)  # Handle (100.00) format
                amount_series = amount_series.str.replace('CR', '', regex=False)  # Remove CR indicator (credit)
                amount_series = amount_series.str.replace('DR', '-', regex=False)  # Replace DR with minus (debit)
                
                print(f"Cleaned amount values (sample): {amount_series.head().tolist()}")
                amounts = pd.to_numeric(amount_series, errors='coerce')
            else:
                # Try to identify debit and credit columns
                debit_col = None
                credit_col = None
                
                for col in amount_cols:
                    col_str = str(col).lower()
                    if 'debit' in col_str or 'payment' in col_str or 'withdrawal' in col_str:
                        debit_col = col
                    elif 'credit' in col_str or 'deposit' in col_str or 'received' in col_str:
                        credit_col = col
                
                if debit_col and credit_col:
                    print(f"Using debit column {debit_col} and credit column {credit_col}")
                    # Convert to numeric, handling special characters
                    debits = pd.to_numeric(combined_df[debit_col].astype(str)
                                         .str.replace(r'[,$\s]', '', regex=True), 
                                         errors='coerce').fillna(0)
                    
                    credits = pd.to_numeric(combined_df[credit_col].astype(str)
                                          .str.replace(r'[,$\s]', '', regex=True), 
                                          errors='coerce').fillna(0)
                    
                    # Credits are positive, debits are negative
                    amounts = credits - debits
                else:
                    # If we can't identify debit/credit, use the first amount column
                    print(f"Using single amount column (best guess): {amount_cols[0]}")
                    amount_series = combined_df[amount_cols[0]].astype(str)
                    amount_series = amount_series.str.replace(r'[,$\s]', '', regex=True)
                    amount_series = amount_series.str.replace(r'\((.+)\)', r'-\1', regex=True)
                    amount_series = amount_series.str.replace('CR', '', regex=False)
                    amount_series = amount_series.str.replace('DR', '-', regex=False)
                    
                    amounts = pd.to_numeric(amount_series, errors='coerce')
            
            # Create the result DataFrame
            result_df = pd.DataFrame({
                'date': dates,
                'description': descriptions.apply(lambda x: clean_description(x)),
                'amount': amounts
            })
            
            # Clean up the data
            # Remove rows with invalid dates
            initial_rows = len(result_df)
            result_df = result_df.dropna(subset=['date'])
            date_dropped = initial_rows - len(result_df)
            print(f"Dropped {date_dropped} rows with invalid dates")
            
            # Ensure amount is numeric
            result_df['amount'] = pd.to_numeric(result_df['amount'], errors='coerce')
            
            # Drop rows with missing amounts
            amount_rows = len(result_df)
            result_df = result_df.dropna(subset=['amount'])
            amount_dropped = amount_rows - len(result_df)
            print(f"Dropped {amount_dropped} rows with invalid amounts")
            
            # Report final results
            print(f"Final dataframe shape: {result_df.shape}")
            
            if result_df.empty:
                raise Exception("Failed to extract any valid transaction data from the PDF")
                
            return result_df
            
        except Exception as e:
            print(f"Error in column processing: {str(e)}")
            # If we can't process the data in the standard way, try a simplified approach
            
            # Create a basic DataFrame from the raw data
            simple_df = pd.DataFrame()
            
            # Try to find any columns with numeric values that could be amounts
            for col in combined_df.columns:
                try:
                    numeric_values = pd.to_numeric(combined_df[col].astype(str).str.replace(r'[,$\s()]', '', regex=True), 
                                                  errors='coerce')
                    if numeric_values.notna().sum() > 0:
                        simple_df['amount'] = numeric_values
                        break
                except:
                    continue
            
            # If we found an amount column, try to find date and description
            if 'amount' in simple_df.columns:
                # Use the first column as date if not already identified
                if date_col:
                    simple_df['date'] = pd.to_datetime(combined_df[date_col], errors='coerce', dayfirst=True)
                else:
                    for col in combined_df.columns:
                        dates = pd.to_datetime(combined_df[col], errors='coerce', dayfirst=True)
                        if dates.notna().sum() > 0:
                            simple_df['date'] = dates
                            break
                
                # Use the longest text column as description
                if description_col:
                    simple_df['description'] = combined_df[description_col].astype(str)
                else:
                    text_lengths = {}
                    for col in combined_df.columns:
                        if col != date_col and combined_df[col].dtype == 'object':
                            text_lengths[col] = combined_df[col].astype(str).str.len().mean()
                    
                    if text_lengths:
                        best_desc_col = max(text_lengths.items(), key=lambda x: x[1])[0]
                        simple_df['description'] = combined_df[best_desc_col].astype(str)
                    else:
                        # Use the first non-date column as description
                        for col in combined_df.columns:
                            if col != date_col:
                                simple_df['description'] = combined_df[col].astype(str)
                                break
                
                # Clean up the data
                if 'date' in simple_df.columns:
                    simple_df = simple_df.dropna(subset=['date'])
                if 'description' in simple_df.columns:
                    simple_df['description'] = simple_df['description'].apply(clean_description)
                
                # Ensure we have all required columns
                for col in ['date', 'description', 'amount']:
                    if col not in simple_df.columns:
                        if col == 'date':
                            # Use current date as fallback
                            simple_df[col] = pd.Timestamp.now()
                        elif col == 'description':
                            simple_df[col] = "Unknown transaction"
                        elif col == 'amount':
                            # Can't proceed without amounts
                            raise Exception("Could not identify transaction amounts in the PDF")
                
                return simple_df
            
            raise Exception(f"Failed to extract transaction data: {str(e)}")
    
    except Exception as e:
        print(f"PDF parsing failed: {str(e)}")
        raise Exception(f"Failed to parse PDF file: {str(e)}")

def clean_description(desc):
    """
    Clean transaction descriptions to remove unnecessary information.
    
    Args:
        desc: Original transaction description
    
    Returns:
        Cleaned description
    """
    if not isinstance(desc, str):
        return str(desc)
    
    # Remove extra whitespace
    cleaned = ' '.join(desc.split())
    
    # Special handling for Barclays format (observed in sample data)
    # Format is often: "VENDOR NAME      REFERENCE INFO"
    if '\t' in cleaned:
        # Split on tab characters 
        parts = cleaned.split('\t')
        # Get the vendor name part, which is usually the first part
        vendor_part = parts[0].strip()
        
        # If it's just "Direct Debit" or "Debit", get the second part too for more info
        if vendor_part in ["Direct Debit", "Debit", "Card Purchase"]:
            # Try to get something more specific from memo field
            if len(parts) > 1:
                # Replace original description with more specific vendor info
                vendor_part = parts[1].strip()
                
                # Clean up typical suffixes like "DDR" or "BGC"
                vendor_part = re.sub(r'\b(DDR|BGC|CBP|BCC|CPM|BP|SO|DD|FT)$', '', vendor_part).strip()
                
                # Remove dates in the format "ON 29 JAN"
                vendor_part = re.sub(r'ON\s+\d+\s+[A-Z]{3}', '', vendor_part).strip()
                
                return vendor_part
        
        return vendor_part
    
    # Check for UK direct debit/standing order format like "Direct Debit to BUPA" or "28 Nov Direct Debit to BUPA"
    bupa_match = re.search(r'Direct\s+Debit\s+to\s+BUPA', cleaned, re.IGNORECASE)
    if bupa_match:
        return "BUPA Healthcare"
    
    # Check for other common UK bank formats - extract payee name from direct debits
    dd_match = re.search(r'Direct\s+Debit\s+to\s+([A-Za-z0-9\s&]+)', cleaned, re.IGNORECASE)
    if dd_match:
        payee = dd_match.group(1).strip()
        return payee
    
    # Check for payment and transfer formats
    payment_match = re.search(r'(Payment|Transfer)\s+to\s+([A-Za-z0-9\s&]+)', cleaned, re.IGNORECASE)
    if payment_match:
        payee = payment_match.group(2).strip()
        return payee
    
    # Look for common UK reference formats (e.g., "Ref: VENDORNAME")
    ref_match = re.search(r'Ref:\s*([A-Za-z0-9\s&]+)', cleaned, re.IGNORECASE)
    if ref_match:
        ref = ref_match.group(1).strip()
        # Only return if ref looks like a proper name, not just numbers
        if re.search(r'[A-Za-z]{3,}', ref):
            return ref
    
    # Remove common reference numbers and codes
    cleaned = re.sub(r'\b(REF|ID|TRXN|TRAN|TRANS|TRN)[\s#:]*\d+\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b\d{5,}\b', '', cleaned)  # Remove long numbers
    
    # Remove dates from description
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'\d{1,2}-\d{1,2}-\d{2,4}',
        r'\d{2,4}-\d{1,2}-\d{1,2}',
        r'\d{1,2}\s[A-Za-z]{3}\s\d{2,4}'
    ]
    for pattern in date_patterns:
        cleaned = re.sub(pattern, '', cleaned)
    
    # Remove common prefixes/suffixes that would interfere with merchant matching
    prefixes = [
        'PAYMENT TO ', 'PAYMENT FROM ', 'PURCHASE AT ', 'POS PURCHASE ', 
        'DEPOSIT AT ', 'ATM ', 'CHQ ', 'CHEQUE ', 'DIRECT DEPOSIT ', 
        'ACH ', 'CREDIT ', 'DEBIT ', 'DIRECT DEBIT TO '
    ]
    for prefix in prefixes:
        if cleaned.upper().startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    # Remove extra whitespace again after all processing
    cleaned = ' '.join(cleaned.split())
    
    # Special case handling for common merchants
    # Credit cards
    if re.search(r'AMEX|American Express', cleaned, re.IGNORECASE):
        return "American Express"
    if re.search(r'VISA|MASTERCARD|CREDIT CARD PMT', cleaned, re.IGNORECASE):
        return "Credit Card Payment"
        
    # Common retailers 
    if re.search(r'AMAZON|AMZN', cleaned, re.IGNORECASE):
        return "Amazon"
    if re.search(r'TESCO', cleaned, re.IGNORECASE):
        return "Tesco"
    if re.search(r'SAINSBURY', cleaned, re.IGNORECASE):
        return "Sainsbury's"
    if re.search(r'ASDA', cleaned, re.IGNORECASE):
        return "Asda"
    if re.search(r'ALDI', cleaned, re.IGNORECASE):
        return "Aldi"
    if re.search(r'LIDL', cleaned, re.IGNORECASE):
        return "Lidl"
    if re.search(r'MORRISONS', cleaned, re.IGNORECASE):
        return "Morrisons"
    if re.search(r'WAITROSE', cleaned, re.IGNORECASE):
        return "Waitrose"
    if re.search(r'IKEA', cleaned, re.IGNORECASE):
        return "IKEA"
    
    # Utilities and services
    if re.search(r'NETFLIX', cleaned, re.IGNORECASE):
        return "Netflix"
    if re.search(r'SPOTIFY', cleaned, re.IGNORECASE):
        return "Spotify"
    if re.search(r'BRITISH GAS|BRITISHGAS', cleaned, re.IGNORECASE):
        return "British Gas"
    if re.search(r'EDF|E\.D\.F', cleaned, re.IGNORECASE):
        return "EDF Energy"
    if re.search(r'THAMES WATER|THAMESWATER', cleaned, re.IGNORECASE):
        return "Thames Water"
    if re.search(r'TV LICENSE|TVLICENSE', cleaned, re.IGNORECASE):
        return "TV License"
    if re.search(r'(?<![A-Z])SKY(?![A-Z])', cleaned, re.IGNORECASE):
        return "Sky"
    if re.search(r'VIRGIN MEDIA|VIRGINMEDIA', cleaned, re.IGNORECASE):
        return "Virgin Media"
    if re.search(r'BT GROUP|BTGROUP|BT\.COM', cleaned, re.IGNORECASE):
        return "BT"
        
    # Remove transaction type indicators that remain
    type_indicators = [
        'PURCHASE', 'PAYMENT', 'TRANSFER', 'FEE', 'INTEREST', 'DEPOSIT', 'WITHDRAWAL',
        'REFUND', 'REVERSAL', 'CHARGE', 'CREDIT', 'DEBIT', 'TRANSACTION'
    ]
    for indicator in type_indicators:
        cleaned = re.sub(rf'\b{indicator}\b', '', cleaned, flags=re.IGNORECASE)
    
    # Final cleanup - if we've stripped too much, return original
    cleaned = cleaned.strip()
    if len(cleaned) < 2:
        # If we've removed too much, return the original with basic cleaning
        return ' '.join(desc.split())
        
    return cleaned
