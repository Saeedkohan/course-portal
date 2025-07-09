import sqlite3
import os


DB_FILENAME = 'app.db'
TABLES_TO_CHECK = ['course', 'enrollment']




db_path = os.path.join(os.path.dirname(__file__), DB_FILENAME)

if not os.path.exists(db_path):
    print(f"Error: Database file not found at '{db_path}'.")
    print("Please make sure you have successfully run the 'flask db upgrade' command.")
else:
    print(f"Checking database schema in file: {db_path}\n")
    try:

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for table_name in TABLES_TO_CHECK:
            print(f"--- Checking structure of table: '{table_name}' ---")


            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            if not columns:
                print(f"Table '{table_name}' does not exist in the database.")
            else:
                print(f"Columns found in table '{table_name}':")
                print("-" * 40)

                for col in columns:

                    col_name = col[1]
                    col_type = col[2]
                    print(f"- Column: {col_name:<15} | Type: {col_type}")
                print("-" * 40)
            print("\n")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:

        if 'conn' in locals() and conn:
            conn.close()
