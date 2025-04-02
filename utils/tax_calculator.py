def calculate_tax_liability(annual_income, tax_brackets):
    """
    Calculate tax liability based on annual income and tax brackets.
    
    Args:
        annual_income: Annual income amount
        tax_brackets: List of dictionaries with tax bracket information (min, max, rate)
    
    Returns:
        Dictionary with tax liability information
    """
    # Sort tax brackets by min value to ensure correct order
    sorted_brackets = sorted(tax_brackets, key=lambda x: x['min'])
    
    # Initialize variables for calculating tax
    total_tax = 0
    remaining_income = annual_income
    bracket_breakdown = []
    
    # Calculate tax for each bracket
    for bracket in sorted_brackets:
        min_amount = bracket['min']
        max_amount = bracket['max']
        rate = bracket['rate']
        
        # Calculate income in this bracket
        if remaining_income <= 0:
            income_in_bracket = 0
        elif min_amount <= remaining_income <= max_amount:
            income_in_bracket = remaining_income - min_amount
        elif remaining_income > max_amount:
            income_in_bracket = max_amount - min_amount
        else:  # remaining_income < min_amount
            income_in_bracket = 0
        
        # Calculate tax for this bracket
        tax_amount = income_in_bracket * rate
        
        # Add to total tax
        total_tax += tax_amount
        
        # Reduce remaining income
        remaining_income -= income_in_bracket
        
        # Add to breakdown if there was income in this bracket
        if income_in_bracket > 0:
            bracket_breakdown.append({
                'min': min_amount,
                'max': max_amount,
                'rate': rate,
                'income_in_bracket': income_in_bracket,
                'tax_amount': tax_amount
            })
        
        # If no more income to tax, break out of the loop
        if remaining_income <= 0:
            break
    
    # Calculate effective tax rate
    effective_rate = (total_tax / annual_income * 100) if annual_income > 0 else 0
    
    return {
        'annual_income': annual_income,
        'total_tax': total_tax,
        'effective_rate': effective_rate,
        'bracket_breakdown': bracket_breakdown
    }
