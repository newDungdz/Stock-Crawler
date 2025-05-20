import json

def find_missing_links(file1, file2):
    # Load JSON data from the files
    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)
        data2 = data2[:500]

    # Extract 'link' columns
    links1 = {item['link'] for item in data1 if 'link' in item}
    links2 = {item['link'] for item in data2 if 'link' in item}

    # Find missing links
    missing_in_file2 = links1 - links2
    missing_in_file1 = links2 - links1

    return missing_in_file1, missing_in_file2

if __name__ == "__main__":
    file1 = "data\\article_data\\tinnhanh.json"  # Replace with your first JSON file path
    file2 = "data\\links\\link_tinnhanh.json"  # Replace with your second JSON file path

    missing_in_file1, missing_in_file2 = find_missing_links(file1, file2)

    print("Links missing in file1:", missing_in_file1)
    print("Links missing in file2:", missing_in_file2)