"""
================================================================================
Hospital Patient Care Analytics System - End-to-End ETL Pipeline
================================================================================
Architecture:
  1. Extract: Ingest 5 raw CSV sources (patients, appointments, consultations,
              lab reports, wearable telemetry).
  2. Transform: Clean, deduplicate, impute missing values (median/mode),
                calculate patient waiting times, aggregate telemetry & lab findings,
                and evaluate clinical risk scores across structured thresholds.
  3. Load: Store cleaned relational data into SQLite (hospital_analytics.db)
           and export sanitized CSV files to data/processed/.
  4. Analyze: Query the database with SQL to generate executive KPIs on
              department workload, waiting times, lab abnormalities, and
              high-risk patient prioritization.
================================================================================
"""

import os
import sys
import time
from src.extract import extract_data
from src.transform import transform_data
from src.load import load_data
from src.analytics import generate_analytics


def run_pipeline() -> None:
    """Orchestrates the end-to-end ETL & Analytics pipeline."""
    start_time = time.time()
    
    print("\n" + "#" * 70)
    print("#  🏥 STARTING HOSPITAL PATIENT CARE ANALYTICS ETL PIPELINE         #")
    print("#" * 70)

    # Resolve project root and directory paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_dir = os.path.join(base_dir, "data", "raw")
    processed_data_dir = os.path.join(base_dir, "data", "processed")
    database_path = os.path.join(base_dir, "database", "hospital_analytics.db")
    report_path = os.path.join(base_dir, "analytics_report.txt")

    try:
        # Phase 1: Extract
        t0 = time.time()
        raw_datasets = extract_data(raw_data_dir)
        print(f"⏱️  Extract stage finished in {time.time() - t0:.2f}s")

        # Phase 2: Transform
        t1 = time.time()
        transformed_datasets = transform_data(raw_datasets)
        print(f"⏱️  Transform stage finished in {time.time() - t1:.2f}s")

        # Phase 3: Load
        t2 = time.time()
        load_data(transformed_datasets, database_path, processed_data_dir)
        print(f"⏱️  Load stage finished in {time.time() - t2:.2f}s")

        # Phase 4: Analyze
        t3 = time.time()
        generate_analytics(database_path, report_path)
        print(f"⏱️  Analytics stage finished in {time.time() - t3:.2f}s")

        total_elapsed = time.time() - start_time
        print("\n" + "#" * 70)
        print(f"#  🎉 PIPELINE EXECUTION COMPLETE IN {total_elapsed:.2f} SECONDS!                     #")
        print("#" * 70)
        print(f"\n📁 Cleaned CSVs:     {processed_data_dir}")
        print(f"💾 SQLite Database:  {database_path}")
        print(f"📄 Analytics Report: {report_path}\n")

    except Exception as e:
        print(f"\n❌ [CRITICAL PIPELINE FAILURE]: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
