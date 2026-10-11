# 🏥 Hospital Patient Care Analytics System
### End-to-End ETL (Extract, Transform, Load) Pipeline & Clinical Intelligence Platform

A modular, production-ready Data Engineering pipeline designed for a multi-specialty hospital. The system collects, cleans, transforms, stores, and analyzes patient data from five disconnected clinical systems to reduce outpatient waiting times and prioritize high-risk patients.

---

## 🎯 Objective
The primary objective of this project is to build an automated healthcare data engineering pipeline that integrates fragmented clinical records (patient demographics, clinic appointments, consultations, laboratory reports, and IoT wearable telemetry). The platform calculates departmental outpatient waiting times, flags biochemical lab abnormalities, and computes an automated clinical early-warning risk score (NEWS2-aligned) to alert medical staff to deteriorating patients in real time.

---

## 🛠️ Technologies Used
- **Programming Language:** Python 3.8+
- **Data Engineering & ETL:** Pandas, NumPy
- **Relational Data Warehouse:** SQLite3 (ANSI SQL compliant)
- **Database Architecture:** Relational Schema (DDL with Primary & Foreign Keys, Indexes)
- **Workflow & Architecture:** Standard ETL Pattern (Extract $\to$ Transform $\to$ Load $\to$ Analyze)
- **Data Visualization & Notebooks:** Jupyter Notebook, Mermaid.js

---

## ⚙️ Methodology & Architecture

The pipeline strictly adheres to the standard Data Engineering lifecycle: **Extract $\to$ Transform $\to$ Load $\to$ Analyze**.

```mermaid
flowchart TD
    subgraph S1["1. Raw Data Sources (data/raw/)"]
        R1["patients.csv<br/>Demographics & History"]
        R2["appointments.csv<br/>Schedules & Departments"]
        R3["consultations.csv<br/>Actual Times & Diagnoses"]
        R4["lab_reports.csv<br/>Biochemical Diagnostics"]
        R5["wearable_data.csv<br/>Continuous Telemetry"]
    end

    subgraph S2["2. Ingestion & Extract (src/extract.py)"]
        E["extract_data()<br/>Pandas Ingestion & Health Checks"]
    end

    subgraph S3["3. Transformation Engine (src/transform.py)"]
        T1["Deduplication & ID Validation"]
        T2["Null Handling (Median & Mode Imputation)"]
        T3["Waiting Time Calculation (Consultation - Scheduled)"]
        T4["Telemetry & Lab Aggregations"]
        T5["Multi-Tier Clinical Risk Scoring Engine"]
    end

    subgraph S4["4. Loading & Warehousing (src/load.py)"]
        L1["SQLite Database<br/>(hospital_analytics.db)"]
        L2["Sanitized CSV Data Mart<br/>(data/processed/)"]
    end

    subgraph S5["5. Executive Analytics (src/analytics.py)"]
        A1["Average Waiting Times"]
        A2["Departmental Workload"]
        A3["Abnormal Lab Findings"]
        A4["Clinical Risk Tiers"]
        A5["Emergency Priority Roster"]
    end

    R1 & R2 & R3 & R4 & R5 --> E
    E --> T1 --> T2 --> T3 --> T4 --> T5
    T5 --> L1 & L2
    L1 --> A1 & A2 & A3 & A4 & A5
