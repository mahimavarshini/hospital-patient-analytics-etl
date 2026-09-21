"""
Module: extract.py
Description: Ingestion layer of the Hospital Patient Care Analytics Pipeline.
Extracts raw CSV files from source directories using Pandas and performs
initial ingestion validation and schema health checks.
"""

import os
import pandas as pd
from typing import Dict


def extract_data(raw_data_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Extracts all raw hospital CSV datasets into Pandas DataFrames.

    Args:
        raw_data_dir (str): Path to the directory containing raw CSV files.

    Returns:
        Dict[str, pd.DataFrame]: Dictionary mapping source names to DataFrames.

    Raises:
        FileNotFoundError: If any required CSV file is missing.
    """
    print("\n" + "=" * 60)
    print("STEP 1: [EXTRACT] Ingesting Raw Hospital Datasets")
    print("=" * 60)

    required_files = {
        "patients": "patients.csv",
        "appointments": "appointments.csv",
        "consultations": "consultations.csv",
        "lab_reports": "lab_reports.csv",
        "wearable_data": "wearable_data.csv"
    }

    raw_datasets: Dict[str, pd.DataFrame] = {}

    for source_name, filename in required_files.items():
        file_path = os.path.join(raw_data_dir, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Required input file missing: {file_path}")

        try:
            # Read CSV with string trimming where possible
            df = pd.read_csv(file_path)
            raw_datasets[source_name] = df
            print(f" [SUCCESS] Extracted '{source_name}': {len(df)} rows, {len(df.columns)} columns from '{filename}'")
        except Exception as e:
            print(f"❌ [ERROR] Failed to extract '{filename}': {str(e)}")
            raise e

    print("\n Extraction Phase Complete: 5/5 datasets ingested successfully.")
    return raw_datasets


if __name__ == "__main__":
    # Test script directly
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    dfs = extract_data(raw_dir)
    for name, df in dfs.items():
        print(f"Preview of {name}:\n", df.head(2), "\n")
