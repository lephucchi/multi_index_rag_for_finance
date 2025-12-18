import os
import pandas as pd

DATA_DIR = os.path.join(os.getcwd(), "data")

def inspect_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        print(f"--- Inspecting {filename} ---")
        try:
            df = pd.read_csv(path, nrows=3)
            print("Columns:", df.columns.tolist())
            print("Sample Data:")
            print(df.head(1).to_string())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    else:
        print(f"File {filename} not found.")

if __name__ == "__main__":
    if os.path.exists(DATA_DIR):
        print("Files in data:", os.listdir(DATA_DIR))
        inspect_csv("finance_index_vnstock.csv")
    else:
        print("Data dir not found")
