import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_income_vs_expense(df):
    """
    Create a bar chart comparing income vs expenses.
    
    Args:
        df: DataFrame containing transaction data
    
    Returns:
        Plotly figure object
    """
    # Extract income and expenses
    income = df[df['amount'] > 0]['amount'].sum()
    expenses = abs(df[df['amount'] < 0]['amount'].sum())
    
    # Create data for the chart
    categories = ['Income', 'Expenses']
    values = [income, expenses]
    colors = ['rgba(44, 160, 44, 0.7)', 'rgba(214, 39, 40, 0.7)']
    
    # Create the bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors,
            text=[f'${v:,.2f}' for v in values],
            textposition='auto'
        )
    ])
    
    # Update layout
    fig.update_layout(
        title='Income vs Expenses',
        xaxis_title='Category',
        yaxis_title='Amount ($)',
        yaxis=dict(tickprefix='$'),
        height=400
    )
    
    return fig

def plot_expense_categories(df):
    """
    Create a pie chart showing expense distribution by category.
    
    Args:
        df: DataFrame containing transaction data
    
    Returns:
        Plotly figure object
    """
    # Filter for expenses only and group by category
    expenses = df[df['amount'] < 0].copy()
    expenses['amount'] = expenses['amount'].abs()  # Convert to positive for visualization
    
    category_expenses = expenses.groupby('category')['amount'].sum().reset_index()
    
    # Sort by amount descending
    category_expenses = category_expenses.sort_values('amount', ascending=False)
    
    # Create the pie chart
    fig = px.pie(
        category_expenses,
        values='amount',
        names='category',
        title='Expense Distribution by Category',
        hole=0.4,  # Create a donut chart
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Update layout and traces
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='%{label}: $%{value:.2f} (%{percent})'
    )
    
    fig.update_layout(height=500)
    
    return fig

def plot_monthly_trend(df):
    """
    Create a line chart showing monthly income, expenses, and savings.
    
    Args:
        df: DataFrame containing transaction data
    
    Returns:
        Plotly figure object
    """
    # Add month column
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M')
    
    # Group by month and calculate income, expenses, and net
    monthly_summary = df_monthly.groupby('month').apply(
        lambda x: pd.Series({
            'income': x[x['amount'] > 0]['amount'].sum(),
            'expenses': abs(x[x['amount'] < 0]['amount'].sum()),
            'net': x['amount'].sum()
        })
    ).reset_index()
    
    # Convert Period to datetime for plotting
    monthly_summary['month'] = monthly_summary['month'].dt.to_timestamp()
    
    # Create the line chart
    fig = go.Figure()
    
    # Add income line
    fig.add_trace(go.Scatter(
        x=monthly_summary['month'],
        y=monthly_summary['income'],
        mode='lines+markers',
        name='Income',
        line=dict(color='rgba(44, 160, 44, 0.7)', width=2),
        hovertemplate='%{x|%b %Y}<br>Income: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add expense line
    fig.add_trace(go.Scatter(
        x=monthly_summary['month'],
        y=monthly_summary['expenses'],
        mode='lines+markers',
        name='Expenses',
        line=dict(color='rgba(214, 39, 40, 0.7)', width=2),
        hovertemplate='%{x|%b %Y}<br>Expenses: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add net savings line
    fig.add_trace(go.Scatter(
        x=monthly_summary['month'],
        y=monthly_summary['net'],
        mode='lines+markers',
        name='Net Savings',
        line=dict(color='rgba(31, 119, 180, 0.7)', width=2),
        hovertemplate='%{x|%b %Y}<br>Net Savings: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add zero line
    fig.add_shape(
        type="line",
        x0=monthly_summary['month'].min(),
        y0=0,
        x1=monthly_summary['month'].max(),
        y1=0,
        line=dict(color="black", width=1, dash="dash")
    )
    
    # Update layout
    fig.update_layout(
        title='Monthly Financial Trend',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        yaxis=dict(tickprefix='$'),
        hovermode='x unified',
        height=500
    )
    
    return fig

def plot_tax_breakdown(tax_info):
    """
    Create a waterfall chart showing tax bracket breakdown.
    
    Args:
        tax_info: Dictionary with tax liability information
    
    Returns:
        Plotly figure object
    """
    # Extract data from tax_info
    bracket_breakdown = tax_info['bracket_breakdown']
    total_tax = tax_info['total_tax']
    annual_income = tax_info['annual_income']
    effective_rate = tax_info['effective_rate']
    
    # Create data for the waterfall chart
    measures = []
    values = []
    names = []
    text = []
    colors = []
    
    # Add bracket breakdowns
    for i, bracket in enumerate(bracket_breakdown):
        rate_pct = bracket['rate'] * 100
        tax_amount = bracket['tax_amount']
        income_in_bracket = bracket['income_in_bracket']
        
        measures.append('relative')
        values.append(tax_amount)
        names.append(f"{bracket['min']:,.0f} - {bracket['max']:,.0f} ({rate_pct:.1f}%)")
        text.append(f"${tax_amount:,.2f}")
        
        # Color gradient from green to red
        color_val = i / max(1, len(bracket_breakdown) - 1)
        r = int(214 * color_val + 44 * (1 - color_val))
        g = int(39 * color_val + 160 * (1 - color_val))
        b = int(40 * color_val + 44 * (1 - color_val))
        colors.append(f"rgba({r}, {g}, {b}, 0.7)")
    
    # Add total line
    measures.append('total')
    values.append(total_tax)
    names.append('Total Tax')
    text.append(f"${total_tax:,.2f}")
    colors.append('rgba(31, 119, 180, 0.7)')
    
    # Create the waterfall chart
    fig = go.Figure(go.Waterfall(
        measure=measures,
        x=names,
        y=values,
        text=text,
        textposition='outside',
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "rgba(44, 160, 44, 0.7)"}},
        increasing={"marker": {"color": "rgba(214, 39, 40, 0.7)"}},
        totals={"marker": {"color": "rgba(31, 119, 180, 0.7)"}}
    ))
    
    # Update layout
    fig.update_layout(
        title=f'Tax Breakdown (Annual Income: ${annual_income:,.2f}, Effective Rate: {effective_rate:.2f}%)',
        xaxis_title='Tax Brackets',
        yaxis_title='Tax Amount ($)',
        yaxis=dict(tickprefix='$'),
        showlegend=False,
        height=500
    )
    
    return fig
