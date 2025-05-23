import json
from datetime import datetime

# File paths
file1_path = 'data\\article_data\\article_data_tinnhanh.json'
file2_path = 'data\\article_data\\article_data_vietstock.json'
output_file_path = 'combined_sorted.json'

# Read JSON files
with open(file1_path, 'r', encoding="utf-8") as file1, open(file2_path, 'r', encoding="utf-8") as file2:
    data1 = json.load(file1)
    data2 = json.load(file2)

print(f"Loaded {len(data1)} records from {file1_path}")
print(f"Loaded {len(data2)} records from {file2_path}")
# Combine data
combined_data = data1 + data2

# Ensure consistent descending order by parsing and sorting dates

def parse_date(item):
    try:
        return datetime.strptime(item['date'], '%d/%m/%Y %H:%M')
    except ValueError:
        return datetime.min  # Handle invalid dates by assigning the earliest possible date


sorted_data = sorted(combined_data, key=parse_date, reverse=True)

# Save to a new JSON file
with open(output_file_path, 'w',  encoding="utf-8") as output_file:
    json.dump(sorted_data, output_file, ensure_ascii=False, indent=4)

print(f"Data combined and saved to {output_file_path}")