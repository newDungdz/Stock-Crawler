import json
from supabase import create_client, Client
from datetime import datetime
from tqdm import tqdm  # progress bar

# Initialize Supabase client
url = "https://fmjjbdnghgdamhcoliun.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtampiZG5naGdkYW1oY29saXVuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MTc0ODAyNiwiZXhwIjoyMDU3MzI0MDI2fQ.Boqfsg63piR-BE-ilSSqK505C3Cf6QuF21tMH8YhBTk"

supabase: Client = create_client(url, key)

def clear_table_and_reset_id(table_name):
    # Delete all rows
    supabase.rpc("execute_sql", {"sql": f"DELETE FROM {table_name} WHERE id != 0;"}).execute()
    # Reset the sequence
    supabase.rpc("execute_sql", {
        "sql": f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1;"
    }).execute()
    print(f"✅ Cleared '{table_name}' and reset ID counter.")


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return date_str

def is_valid_row(row):
    # Skip row if 'date' is empty or invalid
    if 'date' not in row or not row['date'].strip():
        return False
    if parse_date(row['date']) is None:
        return False
    return True

def upload_json_to_supabase(json_file_path, table_name, batch_size=100):
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    cleaned_data = []
    skipped_rows = 0


    for row in data:
        if not is_valid_row(row):
            skipped_rows += 1
            continue

        for key, value in row.items():
            if isinstance(value, str) and "/" in value and ":" in value:
                parsed = parse_date(value)
                if parsed:
                    row[key] = parsed
        cleaned_data.append(row)

    print(f"✅ Total valid rows: {len(cleaned_data)}")
    print(f"⚠️ Skipped corrupted rows: {skipped_rows}")

    # Use tqdm to track batch progress
    total_batches = len(cleaned_data) // batch_size + (1 if len(cleaned_data) % batch_size != 0 else 0)
    for i in tqdm(range(0, len(cleaned_data), batch_size), desc="Uploading to Supabase", total=total_batches):
        batch = cleaned_data[i:i + batch_size]
        try:
            supabase.table(table_name).insert(batch).execute()
        except Exception as e:
            print(f"\n❌ Error on batch {i // batch_size + 1}: {e}")


# Example usage
if __name__ == "__main__":
    json_file_path = "data\\article_data\\article_data_vietstock.json"
    table_name = "article_data"
    # clear_table_and_reset_id(table_name)
    upload_json_to_supabase(json_file_path, table_name)