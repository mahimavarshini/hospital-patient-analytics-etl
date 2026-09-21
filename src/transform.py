"""
Module: transform.py
Description: Transformation engine for the Hospital Patient Care Analytics Pipeline.
Performs data cleaning, deduplication, missing value imputation (median/mode),
datetime standardization, waiting time computation, wearable & lab aggregations,
and multi-parameter clinical risk scoring with defined clinical thresholds.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Tuple


# ==============================================================================
# Clinical Risk Scoring Rules & Thresholds
# Standard clinical early warning criteria (NEWS2 / Hospital Clinical Risk Index)
# ==============================================================================

def calculate_heart_rate_score(hr: float) -> int:
    """
    Heart Rate Clinical Scoring Thresholds:
      - 60 - 100 bpm: 0 points (Normal resting range)
      - 51 - 59 bpm or 101 - 110 bpm: 1 point (Mild bradycardia / tachycardia)
      - 41 - 50 bpm or 111 - 130 bpm: 2 points (Moderate risk)
      - <= 40 bpm or > 130 bpm: 3 points (Severe risk / Hemodynamic instability)
    """
    if pd.isna(hr):
        return 0
    if 60 <= hr <= 100:
        return 0
    elif (51 <= hr < 60) or (101 <= hr <= 110):
        return 1
    elif (41 <= hr <= 50) or (111 <= hr <= 130):
        return 2
    else:
        return 3


def calculate_blood_pressure_score(sys_bp: float) -> int:
    """
    Systolic Blood Pressure Clinical Scoring Thresholds:
      - 110 - 139 mmHg: 0 points (Normal normotensive)
      - 100 - 109 mmHg or 140 - 159 mmHg: 1 point (Stage 1 / Pre-hypertension or mild hypotension)
      - 91 - 99 mmHg or 160 - 179 mmHg: 2 points (Stage 2 hypertension or moderate hypotension)
      - <= 90 mmHg or >= 180 mmHg: 3 points (Hypertensive crisis or severe hypotension / shock)
    """
    if pd.isna(sys_bp):
        return 0
    if 110 <= sys_bp <= 139:
        return 0
    elif (100 <= sys_bp < 110) or (140 <= sys_bp <= 159):
        return 1
    elif (91 <= sys_bp < 100) or (160 <= sys_bp <= 179):
        return 2
    else:
        return 3


def calculate_spo2_score(spo2: float) -> int:
    """
    Oxygen Saturation (SpO2) Clinical Scoring Thresholds:
      - >= 96%: 0 points (Normal oxygenation)
      - 94% - 95%: 1 point (Mild hypoxemia)
      - 92% - 93%: 2 points (Moderate hypoxemia)
      - < 92%: 3 points (Severe hypoxemia / Acute respiratory failure)
    """
    if pd.isna(spo2):
        return 0
    if spo2 >= 96.0:
        return 0
    elif 94.0 <= spo2 < 96.0:
        return 1
    elif 92.0 <= spo2 < 94.0:
        return 2
    else:
        return 3


def calculate_lab_score(abnormal_count: int) -> int:
    """
    Abnormal Laboratory Findings Scoring:
      - 0 abnormal tests: 0 points
      - 1 abnormal test: 1 point
      - 2 abnormal tests: 2 points
      - >= 3 abnormal tests: 3 points
    """
    if pd.isna(abnormal_count) or abnormal_count <= 0:
        return 0
    elif abnormal_count == 1:
        return 1
    elif abnormal_count == 2:
        return 2
    else:
        return 3


def calculate_comorbidity_score(chronic_condition: str, age: int) -> int:
    """
    Comorbidity & Geriatric Factor Scoring:
      - Age >= 65: +1 point
      - High-risk chronic conditions (Heart Failure, COPD, CKD, Coronary Artery Disease): +2 points
      - Moderate chronic conditions (Hypertension, Diabetes, Arrhythmia, Asthma): +1 point
      - None / Unknown: 0 points
    """
    score = 0
    if not pd.isna(age) and age >= 65:
        score += 1

    cond = str(chronic_condition).lower() if not pd.isna(chronic_condition) else ""
    high_risk_conditions = ["heart failure", "copd", "chronic kidney disease", "coronary artery disease"]
    moderate_conditions = ["hypertension", "diabetes", "arrhythmia", "asthma"]

    if any(h in cond for h in high_risk_conditions):
        score += 2
    elif any(m in cond for m in moderate_conditions):
        score += 1

    return score


def evaluate_clinical_risk_tier(total_score: int, max_subscore: int) -> Tuple[str, int, str]:
    """
    Maps total clinical score and highest single-system score into actionable clinical tiers:
      - High Risk (Score >= 6 OR any single parameter score == 3):
          high_risk_flag = 1, recommendation: Immediate senior doctor escalation
      - Moderate Risk (Score 3 - 5):
          high_risk_flag = 0, recommendation: Priority monitoring & clinical review
      - Low Risk (Score 0 - 2):
          high_risk_flag = 0, recommendation: Routine outpatient follow-up
    """
    if total_score >= 6 or max_subscore >= 3:
        return "High", 1, "URGENT: Escalate to Senior Consultant / High-Dependency Unit"
    elif total_score >= 3:
        return "Moderate", 0, "PRIORITY: Continuous vitals monitoring & clinical review"
    else:
        return "Low", 0, "ROUTINE: Standard outpatient care & scheduled follow-up"


# ==============================================================================
# Main Transformation Pipeline
# ==============================================================================

def transform_data(raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Transforms raw hospital datasets through deduplication, null imputation,
    datetime parsing, metric calculation, and patient health summary synthesis.

    Args:
        raw_data (Dict[str, pd.DataFrame]): Dictionary of raw DataFrames.

    Returns:
        Dict[str, pd.DataFrame]: Cleaned and derived DataFrames ready for loading.
    """
    print("\n" + "=" * 60)
    print("STEP 2: [TRANSFORM] Cleaning, Standardizing & Clinical Scoring")
    print("=" * 60)

    # Make explicit copies to avoid mutating input references
    patients = raw_data["patients"].copy()
    appointments = raw_data["appointments"].copy()
    consultations = raw_data["consultations"].copy()
    lab_reports = raw_data["lab_reports"].copy()
    wearable_data = raw_data["wearable_data"].copy()

    # --------------------------------------------------------------------------
    # 1. Transform Patients Dataset
    # --------------------------------------------------------------------------
    print("\n-- [Transforming Patients] --")
    initial_p_count = len(patients)
    patients.drop_duplicates(inplace=True)
    print(f"  • Deduplication: Removed {initial_p_count - len(patients)} duplicate row(s)")

    # Standardize string columns
    patients["first_name"] = patients["first_name"].str.strip().str.title()
    patients["last_name"] = patients["last_name"].str.strip().str.title()
    patients["full_name"] = patients["first_name"] + " " + patients["last_name"]

    # Standardize Gender (M/male -> Male, F/female -> Female)
    gender_map = {
        "m": "Male", "male": "Male",
        "f": "Female", "female": "Female"
    }
    patients["gender"] = patients["gender"].astype(str).str.strip().str.lower().map(gender_map).fillna("Other")

    # Handle Missing Values (following ETLPipeline.ipynb best practices)
    patients["phone"] = patients["phone"].fillna("Not Provided")
    patients["chronic_condition"] = patients["chronic_condition"].fillna("None")

    # Validate Patient IDs (format: P followed by digits)
    valid_id_mask = patients["patient_id"].astype(str).str.match(r"^P\d+$")
    if not valid_id_mask.all():
        invalid_count = (~valid_id_mask).sum()
        print(f"  ⚠️ Warning: Found {invalid_count} invalid patient_id entries; dropping them.")
        patients = patients[valid_id_mask]

    # Calculate Patient Age from DOB
    patients["date_of_birth"] = pd.to_datetime(patients["date_of_birth"], errors="coerce")
    reference_date = pd.Timestamp("2025-05-10")
    patients["age"] = (reference_date - patients["date_of_birth"]).dt.days // 365
    # If any age is missing, impute with median age (as shown in ETLPipeline.ipynb)
    median_age = int(patients["age"].median())
    patients["age"] = patients["age"].fillna(median_age).astype(int)
    patients["date_of_birth"] = patients["date_of_birth"].dt.strftime("%Y-%m-%d")
    print(f"  • Standardized demographics; median age calculated as {median_age} years.")

    # --------------------------------------------------------------------------
    # 2. Transform Appointments Dataset
    # --------------------------------------------------------------------------
    print("\n-- [Transforming Appointments] --")
    initial_a_count = len(appointments)
    appointments.drop_duplicates(inplace=True)
    print(f"  • Deduplication: Removed {initial_a_count - len(appointments)} duplicate row(s)")

    appointments["department"] = appointments["department"].str.strip().str.title()
    appointments["status"] = appointments["status"].str.strip().str.title()
    appointments["appointment_date"] = pd.to_datetime(appointments["appointment_date"]).dt.strftime("%Y-%m-%d")
    appointments["scheduled_time"] = pd.to_datetime(appointments["scheduled_time"])

    # --------------------------------------------------------------------------
    # 3. Transform Consultations Dataset & Calculate Waiting Time
    # --------------------------------------------------------------------------
    print("\n-- [Transforming Consultations & Calculating Waiting Times] --")
    initial_c_count = len(consultations)
    consultations.drop_duplicates(inplace=True)
    print(f"  • Deduplication: Removed {initial_c_count - len(consultations)} duplicate row(s)")

    consultations["consultation_time"] = pd.to_datetime(consultations["consultation_time"])
    consultations["diagnosis"] = consultations["diagnosis"].str.strip()
    consultations["treatment_notes"] = consultations["treatment_notes"].fillna("Standard clinical evaluation completed.")

    # Join with appointments to obtain scheduled_time for waiting time calculation
    merged_appt = pd.merge(
        consultations,
        appointments[["appointment_id", "scheduled_time"]],
        on="appointment_id",
        how="left"
    )

    # Waiting time = Consultation Time - Scheduled Appointment Time (in minutes)
    merged_appt["waiting_time_minutes"] = (
        (merged_appt["consultation_time"] - merged_appt["scheduled_time"]).dt.total_seconds() / 60.0
    ).round(1)

    # Negative waiting time check (e.g. if seen slightly early, minimum 0 mins)
    merged_appt["waiting_time_minutes"] = merged_appt["waiting_time_minutes"].apply(lambda w: max(0.0, w) if pd.notna(w) else 0.0)
    consultations["waiting_time_minutes"] = merged_appt["waiting_time_minutes"]
    consultations["consultation_time"] = consultations["consultation_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    appointments["scheduled_time"] = appointments["scheduled_time"].dt.strftime("%Y-%m-%d %H:%M:%S")

    avg_wait = consultations["waiting_time_minutes"].mean()
    print(f"  • Derived 'waiting_time_minutes': Average waiting time is {avg_wait:.1f} minutes.")

    # --------------------------------------------------------------------------
    # 4. Transform Lab Reports & Calculate Abnormal Indicators
    # --------------------------------------------------------------------------
    print("\n-- [Transforming Lab Reports] --")
    initial_l_count = len(lab_reports)
    lab_reports.drop_duplicates(inplace=True)
    print(f"  • Deduplication: Removed {initial_l_count - len(lab_reports)} duplicate row(s)")

    lab_reports["test_name"] = lab_reports["test_name"].str.strip().str.title()
    lab_reports["test_value"] = pd.to_numeric(lab_reports["test_value"], errors="coerce")
    lab_reports["reference_min"] = pd.to_numeric(lab_reports["reference_min"], errors="coerce")
    lab_reports["reference_max"] = pd.to_numeric(lab_reports["reference_max"], errors="coerce")
    lab_reports["test_unit"] = lab_reports["test_unit"].fillna("units")

    # Flag abnormal lab result: test_value < reference_min OR test_value > reference_max
    lab_reports["is_abnormal"] = (
        (lab_reports["test_value"] < lab_reports["reference_min"]) |
        (lab_reports["test_value"] > lab_reports["reference_max"])
    ).astype(int)

    total_abnormal_tests = lab_reports["is_abnormal"].sum()
    print(f"  • Flagged 'is_abnormal': {total_abnormal_tests} abnormal test results detected out of {len(lab_reports)}.")

    # Aggregate lab indicators per patient
    patient_labs = lab_reports.groupby("patient_id").agg(
        total_lab_tests=("lab_id", "count"),
        abnormal_lab_count=("is_abnormal", "sum")
    ).reset_index()

    # --------------------------------------------------------------------------
    # 5. Transform Wearable Telemetry & Aggregate Biometrics
    # --------------------------------------------------------------------------
    print("\n-- [Transforming Wearable Data] --")
    initial_w_count = len(wearable_data)
    wearable_data.drop_duplicates(inplace=True)
    print(f"  • Deduplication: Removed {initial_w_count - len(wearable_data)} duplicate row(s)")

    # Impute missing values with median (ETLPipeline.ipynb standard)
    if wearable_data["spo2"].isnull().any():
        med_spo2 = wearable_data["spo2"].median()
        wearable_data["spo2"] = wearable_data["spo2"].fillna(med_spo2)
        print(f"  • Imputed missing SpO2 values with median: {med_spo2:.1f}%")

    if wearable_data["daily_steps"].isnull().any():
        med_steps = wearable_data["daily_steps"].median()
        wearable_data["daily_steps"] = wearable_data["daily_steps"].fillna(med_steps)
        print(f"  • Imputed missing daily steps with median: {med_steps:.0f}")

    # Aggregate wearable metrics per patient
    patient_wearables = wearable_data.groupby("patient_id").agg(
        avg_heart_rate=("heart_rate", lambda x: round(x.mean(), 1)),
        avg_systolic_bp=("systolic_bp", lambda x: round(x.mean(), 1)),
        avg_diastolic_bp=("diastolic_bp", lambda x: round(x.mean(), 1)),
        min_spo2=("spo2", lambda x: round(x.min(), 1)),
        total_steps=("daily_steps", lambda x: round(x.max(), 0))
    ).reset_index()

    print(f"  • Aggregated wearable streams into patient biometric profiles ({len(patient_wearables)} patients).")

    # --------------------------------------------------------------------------
    # 6. Build Integrated Patient Health Summary & Clinical Risk Scoring
    # --------------------------------------------------------------------------
    print("\n-- [Building Integrated Master Table & Applying Clinical Risk Rules] --")

    # Merge Patients with Primary Appointment & Consultation
    patient_summary = pd.merge(
        patients[["patient_id", "full_name", "age", "gender", "chronic_condition"]],
        appointments[["appointment_id", "patient_id", "department"]],
        on="patient_id",
        how="left"
    )

    patient_summary = pd.merge(
        patient_summary,
        consultations[["appointment_id", "waiting_time_minutes", "diagnosis"]],
        on="appointment_id",
        how="left"
    )

    # Merge with Wearable Biometrics
    patient_summary = pd.merge(patient_summary, patient_wearables, on="patient_id", how="left")

    # Merge with Lab Aggregates
    patient_summary = pd.merge(patient_summary, patient_labs, on="patient_id", how="left")

    # Fill defaults for patients without lab tests or wearables
    patient_summary["total_lab_tests"] = patient_summary["total_lab_tests"].fillna(0).astype(int)
    patient_summary["abnormal_lab_count"] = patient_summary["abnormal_lab_count"].fillna(0).astype(int)
    patient_summary["waiting_time_minutes"] = patient_summary["waiting_time_minutes"].fillna(0.0)
    patient_summary["diagnosis"] = patient_summary["diagnosis"].fillna("Routine Follow-up")

    # Apply Clinical Risk Scoring Functions
    patient_summary["hr_risk_score"] = patient_summary["avg_heart_rate"].apply(calculate_heart_rate_score)
    patient_summary["bp_risk_score"] = patient_summary["avg_systolic_bp"].apply(calculate_blood_pressure_score)
    patient_summary["spo2_risk_score"] = patient_summary["min_spo2"].apply(calculate_spo2_score)
    patient_summary["lab_risk_score"] = patient_summary["abnormal_lab_count"].apply(calculate_lab_score)
    patient_summary["comorbidity_risk_score"] = patient_summary.apply(
        lambda row: calculate_comorbidity_score(row["chronic_condition"], row["age"]),
        axis=1
    )

    # Total Clinical Risk Score
    patient_summary["total_clinical_risk_score"] = (
        patient_summary["hr_risk_score"] +
        patient_summary["bp_risk_score"] +
        patient_summary["spo2_risk_score"] +
        patient_summary["lab_risk_score"] +
        patient_summary["comorbidity_risk_score"]
    )

    # Maximum single subscore (to catch critical isolated failure, e.g. severe hypoxemia or hypertensive crisis)
    subscore_cols = ["hr_risk_score", "bp_risk_score", "spo2_risk_score", "lab_risk_score"]
    patient_summary["max_vital_subscore"] = patient_summary[subscore_cols].max(axis=1)

    # Derive Clinical Risk Tier, High-Risk Flag & Recommendation
    risk_evaluations = patient_summary.apply(
        lambda r: evaluate_clinical_risk_tier(r["total_clinical_risk_score"], r["max_vital_subscore"]),
        axis=1
    )

    patient_summary["clinical_risk_tier"] = [res[0] for res in risk_evaluations]
    patient_summary["high_risk_flag"] = [res[1] for res in risk_evaluations]
    patient_summary["care_recommendation"] = [res[2] for res in risk_evaluations]

    # Clean up column names for the final summary table
    patient_summary.rename(columns={"full_name": "patient_name"}, inplace=True)
    patient_summary.drop(columns=["max_vital_subscore", "total_steps"], inplace=True, errors="ignore")

    high_risk_count = patient_summary["high_risk_flag"].sum()
    print(f"  • Clinical Risk Stratification completed:")
    print(f"    - High-Risk Patients: {high_risk_count}")
    print(f"    - Moderate-Risk Patients: {(patient_summary['clinical_risk_tier'] == 'Moderate').sum()}")
    print(f"    - Low-Risk Patients: {(patient_summary['clinical_risk_tier'] == 'Low').sum()}")

    transformed_datasets = {
        "patients": patients,
        "appointments": appointments,
        "consultations": consultations,
        "lab_reports": lab_reports,
        "wearable_data": wearable_data,
        "patient_health_summary": patient_summary
    }

    print("\n Transformation Phase Complete: All 6 relational entities created successfully.")
    return transformed_datasets


if __name__ == "__main__":
    import os
    from extract import extract_data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    raw_dfs = extract_data(raw_dir)
    cleaned = transform_data(raw_dfs)
    print("\nSample Health Summary:")
    print(cleaned["patient_health_summary"][["patient_id", "patient_name", "total_clinical_risk_score", "clinical_risk_tier", "high_risk_flag"]].head(10))
