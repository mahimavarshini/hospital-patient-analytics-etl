-- ==========================================================
-- Hospital Patient Care Analytics System - Database Schema (SQLite)
-- ==========================================================

-- 1. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    age INTEGER,
    phone TEXT,
    blood_group TEXT,
    chronic_condition TEXT
);

-- 2. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    department TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
);

-- 3. Consultations Table
CREATE TABLE IF NOT EXISTS consultations (
    consultation_id TEXT PRIMARY KEY,
    appointment_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    consultation_time TEXT NOT NULL,
    waiting_time_minutes REAL,
    diagnosis TEXT,
    treatment_notes TEXT,
    FOREIGN KEY (appointment_id) REFERENCES appointments (appointment_id),
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
);

-- 4. Lab Reports Table
CREATE TABLE IF NOT EXISTS lab_reports (
    lab_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    test_value REAL NOT NULL,
    reference_min REAL NOT NULL,
    reference_max REAL NOT NULL,
    test_unit TEXT,
    test_date TEXT,
    is_abnormal INTEGER NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
);

-- 5. Wearable Telemetry Table
CREATE TABLE IF NOT EXISTS wearable_data (
    device_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    heart_rate REAL NOT NULL,
    systolic_bp REAL NOT NULL,
    diastolic_bp REAL NOT NULL,
    spo2 REAL NOT NULL,
    daily_steps REAL,
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
);

-- 6. Integrated Patient Health Analytics Summary Table
CREATE TABLE IF NOT EXISTS patient_health_summary (
    patient_id TEXT PRIMARY KEY,
    patient_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    department TEXT,
    appointment_id TEXT,
    waiting_time_minutes REAL,
    avg_heart_rate REAL,
    avg_systolic_bp REAL,
    avg_diastolic_bp REAL,
    min_spo2 REAL,
    total_lab_tests INTEGER,
    abnormal_lab_count INTEGER,
    chronic_condition TEXT,
    diagnosis TEXT,
    hr_risk_score INTEGER,
    bp_risk_score INTEGER,
    spo2_risk_score INTEGER,
    lab_risk_score INTEGER,
    comorbidity_risk_score INTEGER,
    total_clinical_risk_score INTEGER,
    clinical_risk_tier TEXT,
    high_risk_flag INTEGER,
    care_recommendation TEXT
);

-- Indexes for Query Performance Optimization
CREATE INDEX IF NOT EXISTS idx_appointments_dept ON appointments(department);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_consultations_patient ON consultations(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_patient ON lab_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_lab_abnormal ON lab_reports(is_abnormal);
CREATE INDEX IF NOT EXISTS idx_wearable_patient ON wearable_data(patient_id);
CREATE INDEX IF NOT EXISTS idx_summary_tier ON patient_health_summary(clinical_risk_tier);
