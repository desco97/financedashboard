import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

from utils.file_handler import parse_csv, parse_pdf
from utils.data_processor import categorize_transactions, calculate_summary
from utils.tax_calculator import calculate_tax_liability
from utils.visualization import (
    plot_income_vs_expense,
    plot_expense_categories,
    plot_monthly_trend,
    plot_tax_breakdown
)

# Set page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data persistence
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame()

# Track imported statements for management
if 'imported_statements' not in st.session_state:
    st.session_state.imported_statements = []

if 'categories' not in st.session_state:
    st.session_state.categories = {
        'Income': ['Salary', 'Bonus', 'Interest', 'Dividends', 'Other Income'],
        'Housing': ['Rent', 'Mortgage', 'Utilities', 'Maintenance', 'Insurance'],
        'Transportation': ['Car Payment', 'Fuel', 'Public Transit', 'Maintenance', 'Insurance'],
        'Food': ['Groceries', 'Dining Out', 'Delivery', 'Snacks'],
        'Healthcare': ['Insurance', 'Medications', 'Doctor Visits', 'Gym Membership'],
        'Entertainment': ['Movies', 'Streaming Services', 'Hobbies', 'Events'],
        'Shopping': ['Clothing', 'Electronics', 'Home Goods', 'Personal Care'],
        'Education': ['Tuition', 'Books', 'Courses', 'School Supplies'],
        'Travel': ['Flights', 'Hotels', 'Car Rental', 'Activities'],
        'Savings': ['Emergency Fund', 'Investments', 'Retirement'],
        'Miscellaneous': ['Gifts', 'Donations', 'Other']
    }
if 'tax_brackets' not in st.session_state:
    # Default US tax brackets for 2023 (single filer)
    st.session_state.tax_brackets = [
        {"min": 0, "max": 11000, "rate": 0.10},
        {"min": 11000, "max": 44725, "rate": 0.12},
        {"min": 44725, "max": 95375, "rate": 0.22},
        {"min": 95375, "max": 182100, "rate": 0.24},
        {"min": 182100, "max": 231250, "rate": 0.32},
        {"min": 231250, "max": 578125, "rate": 0.35},
        {"min": 578125, "max": float('inf'), "rate": 0.37}
    ]


# Initialize file upload session state
if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False

# Function to reset file uploader
def reset_file_uploader():
    st.session_state.file_processed = False
    st.session_state.statement_uploader = None

# Sidebar for navigation and file upload
with st.sidebar:
    st.title("Personal Finance Tracker")
    
    # Navigation
    page = st.radio("Navigation", ["Dashboard", "Expense Analysis", "Import Data", "Categories", "Tax Settings", "Export"])
    
    # File uploader in the sidebar, always available
    st.subheader("Import New Data")
    
    # Key parameter ensures the uploader has a unique ID
    uploaded_file = st.file_uploader("Upload bank statement (CSV or PDF)", 
                                     type=["csv", "pdf"], 
                                     key="statement_uploader",
                                     help="Upload your bank statement in CSV or PDF format")
    
    # For debugging purposes - display session state keys
    if st.checkbox("Show Debug Info", key="show_debug"):
        st.write("Session State Keys:", list(st.session_state.keys()))
        st.write("File Uploader State:", st.session_state.get("statement_uploader", "Not found"))
        st.write("File Processed State:", st.session_state.file_processed)
    
    if uploaded_file is not None and not st.session_state.file_processed:
        # Display file info for debugging
        st.write(f"File received: {uploaded_file.name}, Size: {uploaded_file.size} bytes")
        
        # Add a button to confirm processing
        if st.button("Process Statement", key="process_file_button"):
            st.session_state.file_processed = True
            with st.spinner("Processing your bank statement..."):
                try:
                    # Determine file type and parse accordingly
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    
                    if file_type == 'csv':
                        st.info(f"Processing CSV file: {uploaded_file.name}")
                        new_data = parse_csv(uploaded_file)
                    elif file_type == 'pdf':
                        st.info(f"Processing PDF file: {uploaded_file.name}")
                        new_data = parse_pdf(uploaded_file)
                    else:
                        st.error("Unsupported file type")
                        new_data = None
                    
                    # Process the new data if parsing was successful
                    if new_data is not None and not new_data.empty:
                        # Show preview of parsed data
                        st.subheader("Preview of imported data")
                        st.dataframe(new_data.head(5))
                        
                        # Get existing transactions
                        current_data = st.session_state.transactions
                        
                        # Get min/max dates for statement identification
                        min_date = new_data['date'].min().date() if not new_data.empty else None
                        max_date = new_data['date'].max().date() if not new_data.empty else None
                        
                        # Create a unique identifier for this statement
                        statement_id = f"{uploaded_file.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        
                        # Add a statement_id column to identify which transactions belong to which statement
                        new_data['statement_id'] = statement_id
                        
                        # Store statement metadata
                        statement_info = {
                            'id': statement_id,
                            'filename': uploaded_file.name,
                            'import_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'transaction_count': len(new_data),
                            'date_range': f"{min_date} to {max_date}" if min_date and max_date else "Unknown",
                            'min_date': min_date,
                            'max_date': max_date
                        }
                        
                        # Add to imported statements list
                        st.session_state.imported_statements.append(statement_info)
                        
                        # Combine with new data
                        if not current_data.empty:
                            # If existing data doesn't have a statement_id, add a default one
                            if 'statement_id' not in current_data.columns:
                                current_data['statement_id'] = 'original_data'
                                
                            combined_data = pd.concat([current_data, new_data], ignore_index=True)
                            # Remove duplicates based on date and amount
                            combined_data = combined_data.drop_duplicates(subset=['date', 'description', 'amount'], keep='first')
                        else:
                            combined_data = new_data
                        
                        # Ensure the date is in datetime format
                        combined_data['date'] = pd.to_datetime(combined_data['date'])
                        
                        # Sort by date
                        combined_data = combined_data.sort_values('date', ascending=False)
                        
                        # Update the categorized data
                        st.session_state.transactions = categorize_transactions(combined_data, st.session_state.categories)
                        
                        st.success(f"Successfully imported {len(new_data)} transactions!")
                        
                        # Prompt the user to go to the Dashboard to see the results
                        st.info("Please go to the Dashboard to see your financial insights.")
                        
                        # Add a button to reset the file uploader state for another upload
                        if st.button("Upload Another File", key="upload_another"):
                            reset_file_uploader()
                            st.rerun()
                    else:
                        st.warning("No data was extracted from your file. Please make sure it contains transaction data in a standard format.")
                        # Reset the file processed flag so user can try again
                        st.session_state.file_processed = False
                        
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    st.error("Please make sure your file is not password protected and contains transaction data in a standard format.")
                    # Reset the file processed flag so user can try again
                    st.session_state.file_processed = False

# Main content area
if page == "Dashboard":
    st.title("Financial Dashboard")
    
    if st.session_state.transactions.empty:
        st.info("No data available. Please import your bank statements first.")
    else:
        # Date range filter
        st.subheader("Filter Data")
        col1, col2 = st.columns(2)
        
        # Get min and max dates from the data
        min_date = st.session_state.transactions['date'].min().date()
        max_date = st.session_state.transactions['date'].max().date()
        
        with col1:
            start_date = st.date_input("Start Date", min_date)
        with col2:
            end_date = st.date_input("End Date", max_date)
        
        # Filter data by date
        filtered_data = st.session_state.transactions[
            (st.session_state.transactions['date'] >= pd.Timestamp(start_date)) & 
            (st.session_state.transactions['date'] <= pd.Timestamp(end_date))
        ]
        
        # Calculate summary statistics
        summary = calculate_summary(filtered_data)
        
        # Display summary metrics
        st.subheader("Financial Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Income", f"${summary['total_income']:.2f}")
        col2.metric("Total Expenses", f"${summary['total_expenses']:.2f}")
        col3.metric("Net Savings", f"${summary['net_savings']:.2f}")
        col4.metric("Savings Rate", f"{summary['savings_rate']:.1f}%")
        
        # Tax liability calculation
        annual_income = summary['total_income'] * (365 / (end_date - start_date).days) if (end_date - start_date).days > 0 else 0
        tax_info = calculate_tax_liability(annual_income, st.session_state.tax_brackets)
        
        st.subheader("Estimated Tax Liability")
        col1, col2, col3 = st.columns(3)
        col1.metric("Estimated Annual Income", f"${annual_income:.2f}")
        col2.metric("Estimated Tax", f"${tax_info['total_tax']:.2f}")
        col3.metric("Effective Tax Rate", f"{tax_info['effective_rate']:.1f}%")
        
        # Visualizations
        st.subheader("Financial Insights")
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Income vs Expenses", "Expense Categories", "Monthly Trend", "Tax Breakdown", "Transaction Lists"])
        
        with tab1:
            st.plotly_chart(plot_income_vs_expense(filtered_data), use_container_width=True)
        
        with tab2:
            st.plotly_chart(plot_expense_categories(filtered_data), use_container_width=True)
        
        with tab3:
            st.plotly_chart(plot_monthly_trend(filtered_data), use_container_width=True)
            
        with tab4:
            st.plotly_chart(plot_tax_breakdown(tax_info), use_container_width=True)
            
        with tab5:
            # Transaction lists section
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top Income Transactions")
                
                # Get the top income transactions from our summary calculation
                income_transactions = summary.get('income_transactions', [])
                
                if income_transactions:
                    # Create a DataFrame for display
                    income_df = pd.DataFrame(income_transactions)
                    
                    # Format the date to dd/mm/yyyy
                    income_df['date'] = pd.to_datetime(income_df['date']).dt.strftime('%d/%m/%Y')
                    
                    # Format the amount column
                    income_df['amount'] = income_df['amount'].apply(lambda x: f"${x:.2f}")
                    
                    # Rename columns for display
                    income_df = income_df.rename(columns={
                        'date': 'Date',
                        'description': 'Description',
                        'amount': 'Amount',
                        'subcategory': 'Subcategory'
                    })
                    
                    # Display with improved formatting
                    st.dataframe(income_df, use_container_width=True, height=300)
                else:
                    st.info("No income transactions found in the selected date range.")
            
            with col2:
                st.subheader("Top Expense Transactions")
                
                # Get the top expense transactions from our summary calculation
                expense_transactions = summary.get('expense_transactions', [])
                
                if expense_transactions:
                    # Create a DataFrame for display
                    expense_df = pd.DataFrame(expense_transactions)
                    
                    # Format the date to dd/mm/yyyy
                    expense_df['date'] = pd.to_datetime(expense_df['date']).dt.strftime('%d/%m/%Y')
                    
                    # Format the amount column
                    expense_df['amount'] = expense_df['amount'].apply(lambda x: f"${x:.2f}")
                    
                    # Rename columns for display
                    expense_df = expense_df.rename(columns={
                        'date': 'Date',
                        'description': 'Description',
                        'amount': 'Amount',
                        'category': 'Category',
                        'subcategory': 'Subcategory'
                    })
                    
                    # Display with improved formatting
                    st.dataframe(expense_df, use_container_width=True, height=300)
                else:
                    st.info("No expense transactions found in the selected date range.")
                    
            # Display transaction type breakdown
            st.subheader("Transactions Breakdown")
            transaction_types = summary.get('transaction_types', {'income': 0, 'expense': 0})
            total_transactions = transaction_types['income'] + transaction_types['expense']
            
            if total_transactions > 0:
                # Calculate percentages
                income_pct = transaction_types['income'] / total_transactions * 100
                expense_pct = transaction_types['expense'] / total_transactions * 100
                
                # Create a DataFrame for the breakdown
                breakdown_df = pd.DataFrame({
                    'Type': ['Income', 'Expenses'],
                    'Count': [transaction_types['income'], transaction_types['expense']],
                    'Percentage': [f"{income_pct:.1f}%", f"{expense_pct:.1f}%"]
                })
                
                st.dataframe(breakdown_df, use_container_width=True)
            else:
                st.info("No transactions found in the selected date range.")
        
        # Recent transactions with category filtering
        st.subheader("Recent Transactions")
        
        # Create category filter
        all_categories = ['All Categories'] + list(st.session_state.categories.keys())
        selected_category = st.selectbox("Filter by category", all_categories, key="recent_tx_category")
        
        # Apply category filter if not "All Categories"
        if selected_category != 'All Categories':
            display_data = filtered_data[filtered_data['category'] == selected_category].copy()
        else:
            display_data = filtered_data.copy()
            
        # Format the data for cleaner display
        if not display_data.empty:
            # Format the date to dd/mm/yyyy
            display_data['date'] = display_data['date'].dt.strftime('%d/%m/%Y')
            
            # Format the amount with currency symbol and proper sign
            display_data['amount'] = display_data.apply(
                lambda row: f"${abs(row['amount']):.2f}" if row['category'] != 'Income' 
                else f"${row['amount']:.2f}", axis=1
            )
            
            # Rename columns for better display
            display_columns = {
                'date': 'Date',
                'description': 'Description',
                'amount': 'Amount',
                'category': 'Category',
                'subcategory': 'Subcategory'
            }
            
            # Display only the most recent 100 transactions to avoid overwhelming the UI
            st.dataframe(
                display_data.head(100).rename(columns=display_columns)[list(display_columns.values())],
                use_container_width=True,
                height=400
            )
        else:
            st.info(f"No transactions found for the selected category and date range.")

elif page == "Expense Analysis":
    st.title("Expense Analysis")
    
    if st.session_state.transactions.empty:
        st.info("No data available. Please import your bank statements first.")
    else:
        # Date range filter
        st.subheader("Filter Data")
        col1, col2 = st.columns(2)
        
        # Get min and max dates from the data
        min_date = st.session_state.transactions['date'].min().date()
        max_date = st.session_state.transactions['date'].max().date()
        
        with col1:
            start_date = st.date_input("Start Date", min_date, key="exp_start_date")
        with col2:
            end_date = st.date_input("End Date", max_date, key="exp_end_date")
        
        # Filter data by date and category (expenses only)
        filtered_data = st.session_state.transactions[
            (st.session_state.transactions['date'] >= pd.Timestamp(start_date)) & 
            (st.session_state.transactions['date'] <= pd.Timestamp(end_date)) &
            (st.session_state.transactions['category'] != 'Income')  # Only show expenses
        ]
        
        # Calculate summary statistics for expenses only
        summary = calculate_summary(filtered_data)
        
        # Display summary metrics
        st.subheader("Expense Summary")
        col1, col2 = st.columns(2)
        col1.metric("Total Expenses", f"${summary['total_expenses']:.2f}")
        col2.metric("Top Expense Category", summary['top_expense_category'] if summary['top_expense_category'] else "N/A")
        
        # Show expense category breakdown as a pie chart
        st.subheader("Expense Categories")
        expense_chart = plot_expense_categories(filtered_data)
        st.plotly_chart(expense_chart, use_container_width=True)
        
        # Show detailed breakdown by category
        st.subheader("Expense Breakdown by Category")
        
        expense_by_category = summary['expense_by_category']
        if expense_by_category:
            # Create a DataFrame for better display
            expense_df = pd.DataFrame({
                'Category': list(expense_by_category.keys()),
                'Amount': list(expense_by_category.values())
            })
            # Sort by amount
            expense_df = expense_df.sort_values('Amount', ascending=False)
            # Format amount
            expense_df['Amount'] = expense_df['Amount'].apply(lambda x: f"${x:.2f}")
            # Calculate percentage
            total_expenses = summary['total_expenses']
            expense_df['Percentage'] = expense_df['Amount'].apply(
                lambda x: f"{float(x.replace('$', '')) / total_expenses * 100:.1f}%" if total_expenses > 0 else "0.0%"
            )
            
            st.dataframe(expense_df, use_container_width=True)
        else:
            st.info("No expense data available for the selected period.")
        
        # Let user drill down into specific categories
        st.subheader("Category Drill-Down")
        
        # Get all expense categories
        expense_categories = [cat for cat in st.session_state.categories.keys() if cat != 'Income']
        
        if expense_categories:
            selected_category = st.selectbox("Select a category to analyze", expense_categories)
            
            if selected_category:
                # Filter transactions for just this category
                category_data = filtered_data[filtered_data['category'] == selected_category]
                
                if not category_data.empty:
                    st.write(f"**{selected_category}** expenses: **${category_data['amount'].abs().sum():.2f}**")
                    
                    # Group by subcategory if available
                    if 'subcategory' in category_data.columns:
                        subcat_summary = category_data.groupby('subcategory')['amount'].sum().abs()
                        
                        # Create a DataFrame for display
                        subcat_df = pd.DataFrame({
                            'Subcategory': subcat_summary.index,
                            'Amount': subcat_summary.values
                        })
                        
                        # Sort by amount
                        subcat_df = subcat_df.sort_values('Amount', ascending=False)
                        
                        # Format amount
                        subcat_df['Amount'] = subcat_df['Amount'].apply(lambda x: f"${x:.2f}")
                        
                        # Display subcategory breakdown
                        st.subheader(f"{selected_category} Subcategories")
                        st.dataframe(subcat_df, use_container_width=True)
                    
                    # Show transactions for this category
                    st.subheader(f"{selected_category} Transactions")
                    
                    # Sort by amount and date
                    display_data = category_data.sort_values(['amount', 'date'])
                    
                    # Only show essential columns in a cleaner format
                    display_cols = ['date', 'description', 'amount', 'subcategory']
                    if display_data[display_cols].shape[0] > 0:
                        # Format date and amount
                        display_data = display_data.copy()
                        # Format date as dd/mm/yyyy
                        display_data['date'] = display_data['date'].dt.strftime('%d/%m/%Y')
                        display_data['amount'] = display_data['amount'].abs().apply(lambda x: f"${x:.2f}")
                        
                        # Rename columns for better display
                        display_columns = {
                            'date': 'Date',
                            'description': 'Description',
                            'amount': 'Amount',
                            'subcategory': 'Subcategory'
                        }
                        
                        # Display with improved formatting
                        st.dataframe(
                            display_data[display_cols].rename(columns=display_columns),
                            use_container_width=True,
                            height=350
                        )
                    else:
                        st.info(f"No transactions found for {selected_category} in the selected date range.")
                else:
                    st.info(f"No transactions found for {selected_category} in the selected date range.")
        else:
            st.info("No expense categories defined.")
        
        # Monthly trends for this category
        st.subheader("Monthly Expense Trends")
        
        if not filtered_data.empty:
            # Group by month and category
            filtered_data['month'] = filtered_data['date'].dt.to_period('M')
            monthly_by_category = filtered_data.groupby(['month', 'category'])['amount'].sum().abs().reset_index()
            
            # Convert period to string for proper display
            monthly_by_category['month'] = monthly_by_category['month'].astype(str)
            
            # Create a pivot table for visualization
            pivot_data = monthly_by_category.pivot(index='month', columns='category', values='amount').fillna(0)
            
            # Convert to DataFrame if it's a Series
            if isinstance(pivot_data, pd.Series):
                pivot_data = pivot_data.to_frame()
            
            # Plot the monthly trends by category
            import plotly.graph_objects as go
            
            fig = go.Figure()
            
            for category in pivot_data.columns:
                fig.add_trace(go.Scatter(
                    x=pivot_data.index,
                    y=pivot_data[category],
                    mode='lines+markers',
                    name=category
                ))
            
            fig.update_layout(
                title='Monthly Expenses by Category',
                xaxis_title='Month',
                yaxis_title='Amount ($)',
                template='plotly_white',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available for the selected period.")

elif page == "Import Data":
    st.title("Import Bank Statements")
    
    # Add a reset button to clear the file uploader state
    if st.button("Reset File Uploader", key="reset_uploader"):
        reset_file_uploader()
        st.success("File uploader has been reset. You can now upload a new file.")
        st.rerun()
    
    st.write("""
    ### Data Import Guide
    
    Upload your bank statement files in CSV or PDF format to import your transaction data.
    
    #### Supported File Formats:
    - **CSV**: Comma-separated values files (most banks offer this format)
    - **PDF**: PDF bank statements (experimental support)
    
    #### Expected CSV Format:
    Your CSV should have columns representing:
    - Transaction date
    - Description or merchant name
    - Amount (positive for credits, negative for debits)
    
    The app will try to automatically detect these columns, but results may vary depending on your bank's format.
    
    #### Troubleshooting:
    If you're having trouble uploading a new file, click the "Reset File Uploader" button above.
    """)
    
    # Show currently imported data
    if not st.session_state.transactions.empty:
        st.subheader("Current Dataset")
        st.write(f"Total transactions: {len(st.session_state.transactions)}")
        st.write(f"Date range: {st.session_state.transactions['date'].min().date()} to {st.session_state.transactions['date'].max().date()}")
        
        # Display imported statements with option to remove
        if st.session_state.imported_statements:
            st.subheader("Manage Bank Statements")
            st.write("Select a bank statement to remove:")
            
            for i, statement in enumerate(st.session_state.imported_statements):
                with st.expander(f"{statement['filename']} - {statement['date_range']} ({statement['transaction_count']} transactions)"):
                    st.write(f"**Import Date:** {statement['import_date']}")
                    st.write(f"**Transaction Count:** {statement['transaction_count']}")
                    
                    # Button to remove this statement
                    if st.button(f"Remove this statement", key=f"remove_stmt_{i}"):
                        # Filter out transactions with this statement_id
                        if 'statement_id' in st.session_state.transactions.columns:
                            statement_id = statement['id']
                            # Check how many transactions will be removed
                            count_to_remove = sum(st.session_state.transactions['statement_id'] == statement_id)
                            
                            # Remove the transactions
                            st.session_state.transactions = st.session_state.transactions[
                                st.session_state.transactions['statement_id'] != statement_id
                            ]
                            
                            # Remove the statement from the imported_statements list
                            st.session_state.imported_statements.remove(statement)
                            
                            st.success(f"Removed {count_to_remove} transactions from {statement['filename']}!")
                            
                            # Refresh the page
                            st.rerun()
        
        # Option to clear all data
        if st.button("Clear All Data"):
            # Clear transactions dataframe
            st.session_state.transactions = pd.DataFrame()
            # Clear imported statements list
            st.session_state.imported_statements = []
            # Display success message
            st.success("All data cleared!")
            # Force a rerun of the app to reflect the changes
            st.rerun()

elif page == "Categories":
    st.title("Manage Transaction Categories")
    
    st.write("""
    ### Category Management
    
    Customize your transaction categories and subcategories to better organize your finances.
    """)
    
    # Display and edit categories
    st.subheader("Edit Categories")
    
    # Make a copy of the categories
    edited_categories = st.session_state.categories.copy()
    
    # Create expandable sections for each main category
    for category in list(edited_categories.keys()):
        with st.expander(f"Category: {category}"):
            # Option to rename the category
            new_category_name = st.text_input(f"Rename '{category}'", category, key=f"rename_{category}")
            
            # Edit subcategories as a comma-separated string
            subcats_str = ", ".join(edited_categories[category])
            new_subcats_str = st.text_input(f"Subcategories (comma-separated)", subcats_str, key=f"subcats_{category}")
            new_subcats = [s.strip() for s in new_subcats_str.split(",") if s.strip()]
            
            # Handle category renaming and subcategory updates
            if new_category_name != category:
                # Add the new category with the existing subcategories
                edited_categories[new_category_name] = edited_categories[category]
                # Remove the old category
                del edited_categories[category]
            
            # Update subcategories
            if category in edited_categories:  # Check if this category still exists
                edited_categories[category] = new_subcats
            else:
                edited_categories[new_category_name] = new_subcats
            
            # Option to delete this category
            if st.button(f"Delete Category: {category}", key=f"delete_{category}"):
                if category in edited_categories:
                    del edited_categories[category]
                else:  # If it was renamed
                    del edited_categories[new_category_name]
    
    # Add new category
    st.subheader("Add New Category")
    col1, col2 = st.columns(2)
    with col1:
        new_cat = st.text_input("New Category Name")
    with col2:
        new_subcats = st.text_input("Subcategories (comma-separated)")
    
    if st.button("Add Category") and new_cat:
        edited_categories[new_cat] = [s.strip() for s in new_subcats.split(",") if s.strip()]
        st.success(f"Added new category: {new_cat}")
    
    # Save changes
    if st.button("Save Category Changes"):
        st.session_state.categories = edited_categories
        # Re-categorize all transactions with the updated categories
        if not st.session_state.transactions.empty:
            st.session_state.transactions = categorize_transactions(
                st.session_state.transactions, st.session_state.categories
            )
        st.success("Categories updated successfully!")
    
    # Display current category mappings
    st.subheader("Current Categories")
    for cat, subcats in st.session_state.categories.items():
        st.write(f"**{cat}**: {', '.join(subcats)}")
    
    # If we have transaction data, allow manual recategorization
    if not st.session_state.transactions.empty:
        st.subheader("Recategorize Transactions")
        st.write("Select transactions to manually recategorize them:")
        
        # Get unique descriptions
        unique_descriptions = st.session_state.transactions['description'].unique()
        
        # Let user select a transaction description
        selected_desc = st.selectbox("Select transaction description", unique_descriptions)
        
        if selected_desc:
            # Show current categorization for this description
            current_cat_mask = st.session_state.transactions['description'] == selected_desc
            if current_cat_mask.any():
                current_row = st.session_state.transactions[current_cat_mask].iloc[0]
                current_cat = current_row['category']
                current_subcat = current_row['subcategory']
                
                st.write(f"Current categorization: **{current_cat}** / *{current_subcat}*")
                
                # Let user select new category
                new_cat = st.selectbox("New category", list(st.session_state.categories.keys()))
                
                # Let user select new subcategory based on selected category
                new_subcat = st.selectbox("New subcategory", 
                                          st.session_state.categories.get(new_cat, []))
                
                # Apply recategorization
                if st.button("Apply New Category"):
                    # Update all matching transactions
                    mask = st.session_state.transactions['description'] == selected_desc
                    st.session_state.transactions.loc[mask, 'category'] = new_cat
                    st.session_state.transactions.loc[mask, 'subcategory'] = new_subcat
                    
                    count = mask.sum()
                    st.success(f"Updated {count} transaction(s) with description '{selected_desc}'")

elif page == "Tax Settings":
    st.title("Tax Settings")
    
    st.write("""
    ### Tax Bracket Configuration
    
    Configure your income tax brackets to calculate your tax liability.
    """)
    
    # Country/region selector (for future expansion)
    tax_region = st.selectbox("Tax Region", ["United States"], disabled=True)
    
    # Make a copy of current tax brackets for editing
    tax_brackets = st.session_state.tax_brackets.copy()
    
    st.subheader("Edit Tax Brackets")
    
    # Create a form for each tax bracket
    updated_brackets = []
    
    for i, bracket in enumerate(tax_brackets):
        with st.expander(f"Bracket {i+1}: {bracket['min']} to {bracket['max']} at {bracket['rate']*100}%"):
            col1, col2, col3 = st.columns(3)
            with col1:
                min_val = st.number_input(f"Minimum Income ($)", 
                                          value=float(bracket['min']), 
                                          min_value=0.0, 
                                          step=1000.0,
                                          key=f"min_{i}")
            with col2:
                # For the highest bracket, allow Infinity
                is_highest = i == len(tax_brackets) - 1
                max_placeholder = "∞" if is_highest else None
                max_val = st.number_input(f"Maximum Income ($)", 
                                          value=float('inf') if is_highest and bracket['max'] == float('inf') else float(bracket['max']),
                                          min_value=0.0, 
                                          step=1000.0,
                                          disabled=is_highest,
                                          placeholder=max_placeholder,
                                          key=f"max_{i}")
            with col3:
                rate = st.number_input(f"Tax Rate (%)", 
                                       value=float(bracket['rate']*100), 
                                       min_value=0.0, 
                                       max_value=100.0, 
                                       step=0.1,
                                       key=f"rate_{i}") / 100
            
            updated_brackets.append({
                "min": min_val,
                "max": float('inf') if is_highest else max_val,
                "rate": rate
            })
            
            # Delete button for this bracket (except the last one)
            if not is_highest and st.button(f"Delete Bracket {i+1}", key=f"delete_bracket_{i}"):
                continue
    
    # Filter out any brackets that were marked for deletion
    updated_brackets = [b for b in updated_brackets if b is not None]
    
    # Add new bracket button
    if st.button("Add New Tax Bracket"):
        # Find the highest 'max' value in the current brackets
        if updated_brackets:
            last_max = max([b['max'] for b in updated_brackets if b['max'] != float('inf')])
            # Update the current highest bracket
            for b in updated_brackets:
                if b['max'] == float('inf'):
                    b['max'] = last_max + 50000
            # Add a new highest bracket
            updated_brackets.append({
                "min": last_max + 50000,
                "max": float('inf'),
                "rate": 0.37  # Default rate for the new bracket
            })
    
    # Save changes
    if st.button("Save Tax Bracket Changes"):
        # Sort brackets by min value to ensure proper order
        updated_brackets.sort(key=lambda x: x['min'])
        st.session_state.tax_brackets = updated_brackets
        st.success("Tax brackets updated successfully!")
    
    # Display current tax brackets
    st.subheader("Current Tax Brackets")
    tax_data = []
    for bracket in st.session_state.tax_brackets:
        max_display = "∞" if bracket['max'] == float('inf') else f"${bracket['max']:,.2f}"
        tax_data.append([
            f"${bracket['min']:,.2f}",
            max_display,
            f"{bracket['rate']*100:.1f}%"
        ])
    
    # Create a DataFrame for display
    tax_df = pd.DataFrame(tax_data, columns=["Minimum Income", "Maximum Income", "Tax Rate"])
    st.table(tax_df)
    
    # Sample tax calculation
    st.subheader("Tax Liability Calculator")
    sample_income = st.number_input("Enter annual income to calculate tax", min_value=0.0, value=75000.0, step=5000.0)
    if sample_income > 0:
        tax_info = calculate_tax_liability(sample_income, st.session_state.tax_brackets)
        
        st.write(f"Total tax: **${tax_info['total_tax']:,.2f}**")
        st.write(f"Effective tax rate: **{tax_info['effective_rate']:.2f}%**")
        
        # Show breakdown
        st.write("Tax Bracket Breakdown:")
        for bracket in tax_info['bracket_breakdown']:
            st.write(f"- ${bracket['income_in_bracket']:,.2f} taxed at {bracket['rate']*100:.1f}% = ${bracket['tax_amount']:,.2f}")

elif page == "Export":
    st.title("Export Data")
    
    if st.session_state.transactions.empty:
        st.info("No data available to export. Please import your bank statements first.")
    else:
        st.write("""
        ### Export Your Financial Data
        
        Download your transaction data and financial reports.
        """)
        
        # Export transactions
        st.subheader("Export Transactions")
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", st.session_state.transactions['date'].min().date())
        with col2:
            end_date = st.date_input("End Date", st.session_state.transactions['date'].max().date())
        
        # Filter data by date
        filtered_data = st.session_state.transactions[
            (st.session_state.transactions['date'] >= pd.Timestamp(start_date)) & 
            (st.session_state.transactions['date'] <= pd.Timestamp(end_date))
        ]
        
        # Format options
        export_format = st.radio("Export Format", ["CSV", "Excel"])
        
        if st.button("Generate Export"):
            if export_format == "CSV":
                csv = filtered_data.to_csv(index=False)
                # Create a download button
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"financial_transactions_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:  # Excel
                # Create in-memory Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_data.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    # Add summary sheet
                    summary = calculate_summary(filtered_data)
                    summary_df = pd.DataFrame({
                        'Metric': ['Total Income', 'Total Expenses', 'Net Savings', 'Savings Rate'],
                        'Value': [
                            f"${summary['total_income']:.2f}", 
                            f"${summary['total_expenses']:.2f}", 
                            f"${summary['net_savings']:.2f}", 
                            f"{summary['savings_rate']:.1f}%"
                        ]
                    })
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Add category breakdown sheet
                    cat_summary = filtered_data.groupby('category')['amount'].sum().reset_index()
                    # Split into income and expenses
                    income = cat_summary[cat_summary['amount'] > 0].sort_values('amount', ascending=False)
                    expenses = cat_summary[cat_summary['amount'] < 0].sort_values('amount')
                    expenses['amount'] = expenses['amount'].abs()  # Make expenses positive for reporting
                    
                    income.to_excel(writer, sheet_name='Income Breakdown', index=False)
                    expenses.to_excel(writer, sheet_name='Expense Breakdown', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=output,
                    file_name=f"financial_report_{start_date}_to_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Generate financial report
        st.subheader("Generate Financial Report")
        report_type = st.selectbox(
            "Report Type", 
            ["Monthly Summary", "Yearly Summary", "Category Analysis", "Tax Report"]
        )
        
        if st.button("Generate Report"):
            # Calculate summary for the filtered data
            summary = calculate_summary(filtered_data)
            
            # Add report-specific calculations based on the selected report type
            if report_type == "Monthly Summary":
                # Monthly grouping
                monthly_data = filtered_data.copy()
                monthly_data['month'] = monthly_data['date'].dt.to_period('M')
                monthly_summary = monthly_data.groupby('month').agg({
                    'amount': lambda x: (x > 0).sum(),  # Count of income transactions
                    'amount': lambda x: (x < 0).sum(),  # Count of expense transactions
                    'amount': lambda x: x[x > 0].sum(),  # Sum of income
                    'amount': lambda x: x[x < 0].sum()   # Sum of expenses
                }).reset_index()
                
                # Format as report
                report = f"""
                # Monthly Financial Summary: {start_date} to {end_date}
                
                ## Overall Summary
                - Total Income: ${summary['total_income']:.2f}
                - Total Expenses: ${summary['total_expenses']:.2f}
                - Net Savings: ${summary['net_savings']:.2f}
                - Savings Rate: {summary['savings_rate']:.1f}%
                
                ## Monthly Breakdown
                """
                
                # Add monthly data
                for _, row in monthly_summary.iterrows():
                    month_str = row['month'].strftime('%B %Y')
                    report += f"""
                    ### {month_str}
                    - Income: ${row['amount'][2]:.2f}
                    - Expenses: ${abs(row['amount'][3]):.2f}
                    - Net: ${(row['amount'][2] + row['amount'][3]):.2f}
                    - Transactions: {row['amount'][0] + abs(row['amount'][1])}
                    """
            
            elif report_type == "Yearly Summary":
                # Yearly grouping
                yearly_data = filtered_data.copy()
                yearly_data['year'] = yearly_data['date'].dt.year
                yearly_summary = yearly_data.groupby('year').agg({
                    'amount': [
                        ('income_count', lambda x: (x > 0).sum()),
                        ('expense_count', lambda x: (x < 0).sum()),
                        ('income_sum', lambda x: x[x > 0].sum()),
                        ('expense_sum', lambda x: x[x < 0].sum())
                    ]
                }).reset_index()
                
                # Format as report
                report = f"""
                # Yearly Financial Summary: {start_date} to {end_date}
                
                ## Overall Summary
                - Total Income: ${summary['total_income']:.2f}
                - Total Expenses: ${summary['total_expenses']:.2f}
                - Net Savings: ${summary['net_savings']:.2f}
                - Savings Rate: {summary['savings_rate']:.1f}%
                
                ## Yearly Breakdown
                """
                
                # Add yearly data
                for _, row in yearly_summary.iterrows():
                    year = row['year']
                    income = row[('amount', 'income_sum')]
                    expenses = row[('amount', 'expense_sum')]
                    net = income + expenses
                    savings_rate = (net / income * 100) if income > 0 else 0
                    
                    report += f"""
                    ### {year}
                    - Income: ${income:.2f}
                    - Expenses: ${abs(expenses):.2f}
                    - Net Savings: ${net:.2f}
                    - Savings Rate: {savings_rate:.1f}%
                    - Transactions: {row[('amount', 'income_count')] + row[('amount', 'expense_count')]}
                    """
            
            elif report_type == "Category Analysis":
                # Category analysis
                cat_data = filtered_data.copy()
                
                # Calculate total expenses by category
                cat_expenses = cat_data[cat_data['amount'] < 0].groupby('category')['amount'].sum().abs().sort_values(ascending=False)
                
                # Calculate subcategory breakdown
                subcat_expenses = cat_data[cat_data['amount'] < 0].groupby(['category', 'subcategory'])['amount'].sum().abs()
                
                # Format as report
                report = f"""
                # Expense Category Analysis: {start_date} to {end_date}
                
                ## Overall Expenses
                - Total Expenses: ${summary['total_expenses']:.2f}
                
                ## Category Breakdown
                """
                
                # Add category data
                for cat, amount in cat_expenses.items():
                    report += f"""
                    ### {cat}: ${amount:.2f} ({amount/summary['total_expenses']*100:.1f}%)
                    """
                    
                    # Add subcategories
                    if cat in subcat_expenses.index.get_level_values(0):
                        for subcat, subamount in subcat_expenses[cat].sort_values(ascending=False).items():
                            report += f"- {subcat}: ${subamount:.2f} ({subamount/amount*100:.1f}%)\n"
            
            elif report_type == "Tax Report":
                # Get yearly income for tax calculations
                yearly_data = filtered_data.copy()
                yearly_data['year'] = yearly_data['date'].dt.year
                yearly_income = yearly_data[yearly_data['amount'] > 0].groupby('year')['amount'].sum()
                
                # Format as report
                report = f"""
                # Tax Liability Report: {start_date} to {end_date}
                
                ## Current Tax Brackets
                """
                
                # Add tax bracket information
                for bracket in st.session_state.tax_brackets:
                    max_display = "∞" if bracket['max'] == float('inf') else f"${bracket['max']:,.2f}"
                    report += f"- ${bracket['min']:,.2f} to {max_display}: {bracket['rate']*100:.1f}%\n"
                
                report += "\n## Tax Liability by Year\n"
                
                # Calculate tax for each year
                for year, income in yearly_income.items():
                    tax_info = calculate_tax_liability(income, st.session_state.tax_brackets)
                    
                    report += f"""
                    ### {year}
                    - Annual Income: ${income:.2f}
                    - Estimated Tax: ${tax_info['total_tax']:.2f}
                    - Effective Tax Rate: {tax_info['effective_rate']:.2f}%
                    
                    #### Tax Bracket Breakdown:
                    """
                    
                    for bracket in tax_info['bracket_breakdown']:
                        report += f"- ${bracket['income_in_bracket']:,.2f} taxed at {bracket['rate']*100:.1f}% = ${bracket['tax_amount']:,.2f}\n"
            
            # Display the report
            st.markdown(report)
            
            # Provide download option for the report
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"{report_type.replace(' ', '_').lower()}_{start_date}_to_{end_date}.md",
                mime="text/markdown"
            )
