"""
Module: analytics.py
Description: Analytics & Reporting engine of the Hospital Patient Care Analytics Pipeline.
Executes SQL queries against SQLite (hospital_analytics.db) to compute hospital KPIs,
operational efficiencies (waiting times), and clinical risk stratifications.
"""

import os
import sqlite3
import pandas as pd


def generate_analytics(database_path: str, output_report_path: str = None) -> None:
    """
    Executes analytical SQL queries against the loaded SQLite database
    and outputs clinical and operational KPIs to console and an export report.

    Args:
        database_path (str): Filepath to the SQLite database.
        output_report_path (str, optional): Filepath to save the text report.
    """
    print("\n" + "=" * 60)
    print("STEP 4: [ANALYZE] Generating Hospital KPIs & Clinical Insights")
    print("=" * 60)

    if not os.path.exists(database_path):
        raise FileNotFoundError(f"Database not found at: {database_path}")

    conn = sqlite3.connect(database_path)
    report_lines = []

    def log_and_record(text: str = ""):
        print(text)
        report_lines.append(text)

    log_and_record("=" * 70)
    log_and_record("🏥 HOSPITAL PATIENT CARE ANALYTICS SYSTEM - EXECUTIVE KPI REPORT")
    log_and_record("=" * 70)

    # --------------------------------------------------------------------------
    # KPI 1: Average Patient Waiting Time (Overall & By Department)
    # --------------------------------------------------------------------------
    log_and_record("\n📊 KPI 1: PATIENT WAITING TIME ANALYSIS (Operational Efficiency)")
    log_and_record("-" * 70)
    query_waiting = """
        SELECT 
            a.department,
            COUNT(c.consultation_id) AS total_patients,
            ROUND(AVG(c.waiting_time_minutes), 1) AS avg_wait_mins,
            ROUND(MIN(c.waiting_time_minutes), 1) AS min_wait_mins,
            ROUND(MAX(c.waiting_time_minutes), 1) AS max_wait_mins
        FROM appointments a
        JOIN consultations c ON a.appointment_id = c.appointment_id
        GROUP BY a.department
        ORDER BY avg_wait_mins DESC;
    """
    df_waiting = pd.read_sql_query(query_waiting, conn)
    log_and_record(df_waiting.to_string(index=False))

    overall_wait = pd.read_sql_query(
        "SELECT ROUND(AVG(waiting_time_minutes), 1) AS overall_avg FROM consultations", conn
    ).iloc[0]["overall_avg"]
    log_and_record(f"\n Hospital-Wide Average Waiting Time: {overall_wait} minutes")

    # --------------------------------------------------------------------------
    # KPI 2: Number of Appointments by Department
    # --------------------------------------------------------------------------
    log_and_record("\n📊 KPI 2: APPOINTMENT VOLUME BY DEPARTMENT")
    log_and_record("-" * 70)
    query_dept = """
        SELECT 
            department,
            COUNT(*) AS total_appointments,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM appointments), 1) AS percentage_share
        FROM appointments
        GROUP BY department
        ORDER BY total_appointments DESC;
    """
    df_dept = pd.read_sql_query(query_dept, conn)
    log_and_record(df_dept.to_string(index=False))

    # --------------------------------------------------------------------------
    # KPI 3: Abnormal Laboratory Results Frequency
    # --------------------------------------------------------------------------
    log_and_record("\n📊 KPI 3: ABNORMAL LABORATORY FINDINGS")
    log_and_record("-" * 70)
    query_lab = """
        SELECT 
            test_name,
            COUNT(*) AS total_tests,
            SUM(is_abnormal) AS abnormal_count,
            ROUND(100.0 * SUM(is_abnormal) / COUNT(*), 1) AS abnormal_rate_pct,
            ROUND(AVG(test_value), 2) AS cohort_avg_value,
            test_unit
        FROM lab_reports
        GROUP BY test_name, test_unit
        ORDER BY abnormal_count DESC;
    """
    df_lab = pd.read_sql_query(query_lab, conn)
    log_and_record(df_lab.to_string(index=False))

    # --------------------------------------------------------------------------
    # KPI 4: Clinical Risk Stratification & High-Risk Count
    # --------------------------------------------------------------------------
    log_and_record("\n📊 KPI 4: CLINICAL RISK STRATIFICATION (NEWS2-aligned Model)")
    log_and_record("-" * 70)
    query_risk = """
        SELECT 
            clinical_risk_tier,
            COUNT(*) AS patient_count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM patient_health_summary), 1) AS percentage_of_patients,
            ROUND(AVG(total_clinical_risk_score), 1) AS avg_risk_score,
            ROUND(AVG(avg_heart_rate), 1) AS cohort_avg_heart_rate,
            ROUND(AVG(avg_systolic_bp), 1) AS cohort_avg_sys_bp
        FROM patient_health_summary
        GROUP BY clinical_risk_tier
        ORDER BY avg_risk_score DESC;
    """
    df_risk = pd.read_sql_query(query_risk, conn)
    log_and_record(df_risk.to_string(index=False))

    # --------------------------------------------------------------------------
    # KPI 5: Average Heart Rate and Vitals by Patient
    # --------------------------------------------------------------------------
    log_and_record("\n📊 KPI 5: PATIENT BIOMETRIC SUMMARY (Wearable Telemetry)")
    log_and_record("-" * 70)
    query_vitals = """
        SELECT 
            patient_id,
            patient_name,
            age,
            gender,
            avg_heart_rate,
            avg_systolic_bp,
            avg_diastolic_bp,
            min_spo2,
            clinical_risk_tier
        FROM patient_health_summary
        ORDER BY avg_heart_rate DESC
        LIMIT 10;
    """
    df_vitals = pd.read_sql_query(query_vitals, conn)
    log_and_record(df_vitals.to_string(index=False))
    log_and_record("  (Showing top 10 patients sorted by resting heart rate)")

    # --------------------------------------------------------------------------
    # KPI 6: Priority Action Roster - Patients Requiring Immediate Attention
    # --------------------------------------------------------------------------
    log_and_record("\n🚨 KPI 6: ACTION ROSTER - PATIENTS REQUIRING IMMEDIATE CLINICAL ATTENTION")
    log_and_record("-" * 70)
    query_attention = """
        SELECT 
            patient_id,
            patient_name,
            age,
            department,
            waiting_time_minutes,
            avg_heart_rate,
            avg_systolic_bp,
            min_spo2,
            abnormal_lab_count,
            total_clinical_risk_score,
            clinical_risk_tier,
            diagnosis,
            care_recommendation
        FROM patient_health_summary
        WHERE high_risk_flag = 1 
           OR waiting_time_minutes > 60
           OR abnormal_lab_count >= 2
        ORDER BY total_clinical_risk_score DESC, waiting_time_minutes DESC;
    """
    df_attention = pd.read_sql_query(query_attention, conn)
    log_and_record(df_attention.to_string(index=False))

    conn.close()

    # Save to report file if specified
    if output_report_path:
        os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"\n [SUCCESS] Analytical report successfully saved to: {output_report_path}")

    print("\n Analytics Phase Complete: All operational and clinical KPIs computed.")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(base_dir, "database", "hospital_analytics.db")
    report_file = os.path.join(base_dir, "analytics_report.txt")
    generate_analytics(db_file, report_file)
