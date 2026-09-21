"""
Module: load.py
Description: Loading layer of the Hospital Patient Care Analytics Pipeline.
Stores transformed datasets into a local SQLite database (hospital_analytics.db)
and exports cleaned CSV files to the processed data warehouse directory.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict


def load_data(
    transformed_datasets: Dict[str, pd.DataFrame],
    database_path: str,
    processed_dir: str
) -> None:
    """
    Persists cleaned datasets into SQLite database tables and saves processed CSV files.

    Args:
        transformed_datasets (Dict[str, pd.DataFrame]): Dictionary of cleaned DataFrames.
        database_path (str): Filepath to the target SQLite database.
        processed_dir (str): Directory where cleaned CSV files should be saved.
    """
    print("\n" + "=" * 60)
    print("STEP 3: [LOAD] Storing Processed Data in SQLite & File Warehouse")
    print("=" * 60)

    # Ensure target directories exist
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # 1. Export Cleaned CSV Files
    print("\n-- [Exporting Cleaned CSV Files] --")
    for table_name, df in transformed_datasets.items():
        csv_filename = f"cleaned_{table_name}.csv" if table_name != "patient_health_summary" else "patient_health_summary.csv"
        csv_filepath = os.path.join(processed_dir, csv_filename)
        df.to_csv(csv_filepath, index=False)
        print(f"  • Exported: '{csv_filename}' ({len(df)} rows) -> {csv_filepath}")

    # 2. Ingest into SQLite Database
    print("\n-- [Writing to SQLite Database] --")
    print(f"  • Connecting to SQLite database at: {database_path}")

    conn = None
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Load each DataFrame into its corresponding table
        for table_name, df in transformed_datasets.items():
            # Write to SQLite
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            
            # Verify record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"  • Table '{table_name}': Loaded successfully ({row_count} records).")

        # Create Analytical Performance Indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_appt_dept ON appointments(department);",
            "CREATE INDEX IF NOT EXISTS idx_appt_pat ON appointments(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_cons_pat ON consultations(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_lab_abn ON lab_reports(is_abnormal);",
            "CREATE INDEX IF NOT EXISTS idx_wear_pat ON wearable_data(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_sum_tier ON patient_health_summary(clinical_risk_tier);"
        ]
        for idx_sql in indexes:
            cursor.execute(idx_sql)
        conn.commit()
        print("  • Database indexes created successfully.")

        print(f"\n Load Phase Complete: All {len(transformed_datasets)} tables loaded into SQLite.")

    except Exception as e:
        print(f"❌ [ERROR] Database loading failed: {str(e)}")
        raise e
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    from extract import extract_data
    from transform import transform_data

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    proc_dir = os.path.join(base_dir, "data", "processed")
    db_file = os.path.join(base_dir, "database", "hospital_analytics.db")

    raw_dfs = extract_data(raw_dir)
    cleaned_dfs = transform_data(raw_dfs)
    load_data(cleaned_dfs, db_file, proc_dir)
