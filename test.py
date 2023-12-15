import pandas as pd

# Sample DataFrame with 'ID' as strings
data = {'ID': ['1', '2', '3', '4', '1_A', 'asdfsd1sdfasdf'],
        'Category': ['A_1', 'B_2', 'C_3', 'A_4', 'X', 'Y']}
df = pd.DataFrame(data)

# Lookup dictionary with string keys
lookup_dict = {'1': 'Category_X', '2': 'Category_Y', '3': 'Category_Z'}

# Update the 'Category' column based on whether any dictionary key is contained in the 'ID' value
df['Category'] = df['ID'].apply(lambda x: next((v for k, v in lookup_dict.items() if k in x), x))

# Print the updated DataFrame
print(df)
