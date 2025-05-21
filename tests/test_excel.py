#!/usr/bin/env python3
from src.file_handler_tool import FileHandlerTool
from src.final_answer_processor import process_final_answer
import re

# Test Excel file handling
handler = FileHandlerTool()
result = handler.read_file('test', '7bd855d8-463d-4ed5-93ca-5fe35145f733.xlsx')

print('File type:', result.get('type'))
print('Columns:', result.get('columns', []))

# The file has food items as columns (Burgers, Hot Dogs, Salads, Fries)
# and drink items (Ice Cream, Soda)
food_categories = ['Burgers', 'Hot Dogs', 'Salads', 'Fries']
drink_categories = ['Ice Cream', 'Soda']

# Calculate food sales by summing the values for all food categories across all locations
food_sales = 0
for row in result.get('rows', []):
    for category in food_categories:
        if category in row and row[category] is not None:
            food_sales += float(row[category])

print(f'Food sales (raw): ${food_sales}')
print(f'Food sales type: {type(food_sales)}')
print(f'Food sales representation: {repr(food_sales)}')

# Convert to string directly with proper formatting
food_sales_str = f"{food_sales:.2f}"
print(f'Formatted string: {food_sales_str}')

# Test our fix on the string directly
question = "What were the total sales that the chain made from food (not including drinks)? Express your answer in USD with two decimal places."

# Define our own direct processing function to get exact currency formatting
def format_as_currency(value_str):
    # Clean the string - remove $ and commas
    clean_value = value_str.replace('$', '').replace(',', '')
    
    # Extract the first number if there are multiple
    number_match = re.search(r'(\d+(?:\.\d+)?)', clean_value)
    if number_match:
        clean_value = number_match.group(1)
    
    # Convert to float and format with 2 decimal places
    try:
        value = float(clean_value)
        return f"${value:.2f}"
    except ValueError:
        return value_str

# Try both our direct formatter and the processor
direct_formatted = format_as_currency(food_sales_str)
print(f'Direct formatted: {direct_formatted}')

formatted_answer = process_final_answer(question, food_sales_str)
print(f'Processor formatted: {formatted_answer}')

# Now try with the raw value string
raw_str = str(food_sales)
print(f'Raw string: {raw_str}')
raw_formatted = format_as_currency(raw_str)
print(f'Raw formatted: {raw_formatted}')

formatted_raw = process_final_answer(question, raw_str)
print(f'Processor raw formatted: {formatted_raw}') 