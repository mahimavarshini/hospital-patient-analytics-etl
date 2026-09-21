-- ==========================================================
-- Hospital Patient Care Analytics System - Analytical SQL Queries
-- ==========================================================

-- Query 1: Overall and Department-wise Average Patient Waiting Time
-- Identifies operational bottlenecks and delays in doctor consultations
SELECT 
    a.department,
    COUNT(c.consultation_id) AS total_consultations,
    ROUND(AVG(c.waiting_time_minutes), 1) AS avg_waiting_time_mins,
    ROUND(MIN(c.waiting_time_minutes), 1) AS min_waiting_time_mins,
    ROUND(MAX(c.waiting_time_minutes), 1) AS max_waiting_time_mins
FROM appointments a
JOIN consultations c ON a.appointment_id = c.appointment_id
GROUP BY a.department
ORDER BY avg_waiting_time_mins DESC;


-- Query 2: Appointment Distribution by Department and Status
-- Evaluates department workload and service utilization
SELECT 
    department,
    status,
    COUNT(*) AS appointment_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM appointments), 1) AS percentage_of_total
FROM appointments
GROUP BY department, status
ORDER BY appointment_count DESC;


-- Query 3: Abnormal Lab Results Analysis by Test Category
-- Flags high-frequency clinical abnormalities across the patient cohort
SELECT 
    test_name,
    COUNT(*) AS total_tests_conducted,
    SUM(is_abnormal) AS abnormal_results_count,
    ROUND(100.0 * SUM(is_abnormal) / COUNT(*), 1) AS abnormal_percentage,
    ROUND(AVG(test_value), 2) AS avg_test_value,
    test_unit
FROM lab_reports
GROUP BY test_name, test_unit
ORDER BY abnormal_results_count DESC;


-- Query 4: Clinical Risk Stratification and High-Risk Patient Distribution
-- Aggregates patients across clinical risk tiers (Low, Moderate, High)
SELECT 
    clinical_risk_tier,
    COUNT(*) AS patient_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM patient_health_summary), 1) AS tier_percentage,
    ROUND(AVG(total_clinical_risk_score), 1) AS avg_risk_score,
    ROUND(AVG(avg_heart_rate), 1) AS cohort_avg_heart_rate,
    ROUND(AVG(avg_systolic_bp), 1) AS cohort_avg_systolic_bp
FROM patient_health_summary
GROUP BY clinical_risk_tier
ORDER BY avg_risk_score DESC;


-- Query 5: Biometric Health Overview - Heart Rate and Blood Pressure by Patient
-- Aggregates wearable biometric monitoring readings
SELECT 
    phs.patient_id,
    phs.patient_name,
    phs.age,
    phs.gender,
    phs.avg_heart_rate,
    phs.avg_systolic_bp,
    phs.avg_diastolic_bp,
    phs.min_spo2,
    phs.clinical_risk_tier
FROM patient_health_summary phs
ORDER BY phs.avg_heart_rate DESC;


-- Query 6: Actionable Priority Roster - Patients Requiring Immediate Attention
-- Surfaces patients with high clinical risk, acute diagnoses, abnormal labs, or excessive delays
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
