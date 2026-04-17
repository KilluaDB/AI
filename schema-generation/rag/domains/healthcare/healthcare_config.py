"""
Healthcare Domain Configuration

Contains healthcare-specific data types, mappings, and configuration for database schema design.
This serves as ground-truth knowledge for healthcare database modeling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class HealthcareStandard(Enum):
    """Healthcare data standards that may inform schema design"""
    GENERAL = "general"
    HL7 = "hl7"
    ICD10 = "icd10"
    SNOMED = "snomed"
    LOINC = "loinc"
    CPT = "cpt"
    NDC = "ndc"


@dataclass
class HealthcareConfig:
    """Configuration for healthcare domain RAG"""
    
    standard: HealthcareStandard = HealthcareStandard.GENERAL
    
    # Whether to include various types of knowledge
    include_entities: bool = True
    include_relationships: bool = True
    include_datatypes: bool = True
    include_constraints: bool = True
    include_normalization: bool = True
    include_patterns: bool = True


# Healthcare attribute to PostgreSQL data type mapping
HEALTHCARE_POSTGRES_TYPE_MAP: Dict[str, str] = {
    # ============== IDENTIFIERS ==============
    "patient_id": "SERIAL PRIMARY KEY",
    "medical_record_number": "VARCHAR(50) UNIQUE NOT NULL",
    "mrn": "VARCHAR(50) UNIQUE NOT NULL",
    "ssn": "VARCHAR(11) UNIQUE",  # Format: XXX-XX-XXXX
    "insurance_id": "VARCHAR(50)",
    "policy_number": "VARCHAR(50)",
    "npi": "VARCHAR(10) UNIQUE",  # National Provider Identifier (10 digits)
    "dea_number": "VARCHAR(9)",  # Drug Enforcement Administration number
    "license_number": "VARCHAR(50)",
    "encounter_id": "SERIAL PRIMARY KEY",
    "visit_number": "VARCHAR(50)",
    "claim_id": "VARCHAR(50)",
    "prescription_id": "SERIAL PRIMARY KEY",
    
    # ============== PERSONAL INFORMATION ==============
    "first_name": "VARCHAR(100) NOT NULL",
    "last_name": "VARCHAR(100) NOT NULL",
    "middle_name": "VARCHAR(100)",
    "full_name": "VARCHAR(255)",
    "date_of_birth": "DATE NOT NULL",
    "dob": "DATE NOT NULL",
    "gender": "VARCHAR(20)",  # male, female, other, unknown
    "sex": "VARCHAR(20)",
    "age": "INTEGER",
    "marital_status": "VARCHAR(30)",
    "race": "VARCHAR(50)",
    "ethnicity": "VARCHAR(50)",
    "language": "VARCHAR(50)",
    "nationality": "VARCHAR(50)",
    
    # ============== CONTACT INFORMATION ==============
    "phone": "VARCHAR(20)",
    "phone_number": "VARCHAR(20)",
    "mobile": "VARCHAR(20)",
    "email": "VARCHAR(255)",
    "address": "TEXT",
    "street_address": "VARCHAR(255)",
    "city": "VARCHAR(100)",
    "state": "VARCHAR(50)",
    "zip_code": "VARCHAR(20)",
    "postal_code": "VARCHAR(20)",
    "country": "VARCHAR(100)",
    
    # ============== CLINICAL DATA ==============
    "diagnosis": "TEXT",
    "diagnosis_code": "VARCHAR(20)",  # ICD-10 codes
    "diagnosis_description": "TEXT",
    "primary_diagnosis": "VARCHAR(20)",
    "secondary_diagnosis": "VARCHAR(20)",
    "condition": "TEXT",
    "symptom": "TEXT",
    "chief_complaint": "TEXT",
    "procedure_code": "VARCHAR(20)",  # CPT codes
    "procedure_description": "TEXT",
    "treatment": "TEXT",
    "treatment_plan": "TEXT",
    "clinical_notes": "TEXT",
    "progress_notes": "TEXT",
    "assessment": "TEXT",
    "plan": "TEXT",
    
    # ============== VITAL SIGNS ==============
    "blood_pressure_systolic": "SMALLINT",  # mmHg
    "blood_pressure_diastolic": "SMALLINT",  # mmHg
    "heart_rate": "SMALLINT",  # bpm
    "pulse": "SMALLINT",  # bpm
    "temperature": "DECIMAL(4,1)",  # Fahrenheit or Celsius
    "respiratory_rate": "SMALLINT",  # breaths per minute
    "oxygen_saturation": "DECIMAL(5,2)",  # percentage
    "spo2": "DECIMAL(5,2)",
    "weight": "DECIMAL(6,2)",  # kg or lbs
    "height": "DECIMAL(5,2)",  # cm or inches
    "bmi": "DECIMAL(4,1)",
    
    # ============== LAB RESULTS ==============
    "lab_value": "DECIMAL(12,4)",
    "lab_result": "VARCHAR(255)",
    "result_value": "DECIMAL(12,4)",
    "result_unit": "VARCHAR(50)",
    "reference_range_low": "DECIMAL(12,4)",
    "reference_range_high": "DECIMAL(12,4)",
    "normal_range": "VARCHAR(100)",
    "test_name": "VARCHAR(255)",
    "test_code": "VARCHAR(20)",  # LOINC codes
    "specimen_type": "VARCHAR(100)",
    
    # ============== MEDICATION ==============
    "medication_name": "VARCHAR(255) NOT NULL",
    "drug_name": "VARCHAR(255)",
    "generic_name": "VARCHAR(255)",
    "brand_name": "VARCHAR(255)",
    "ndc_code": "VARCHAR(20)",  # National Drug Code
    "rxnorm_code": "VARCHAR(20)",
    "dosage": "VARCHAR(100)",
    "dose_amount": "DECIMAL(10,3)",
    "dose_unit": "VARCHAR(50)",
    "frequency": "VARCHAR(100)",
    "route": "VARCHAR(50)",  # oral, IV, IM, etc.
    "strength": "VARCHAR(100)",
    "quantity": "INTEGER",
    "refills": "SMALLINT",
    "instructions": "TEXT",
    "sig": "TEXT",  # Prescription instructions
    
    # ============== DATES AND TIMES ==============
    "admission_date": "TIMESTAMP NOT NULL",
    "discharge_date": "TIMESTAMP",
    "visit_date": "TIMESTAMP NOT NULL",
    "appointment_date": "TIMESTAMP",
    "service_date": "DATE",
    "start_date": "DATE",
    "end_date": "DATE",
    "effective_date": "DATE",
    "expiration_date": "DATE",
    "order_date": "TIMESTAMP",
    "result_date": "TIMESTAMP",
    "specimen_collection_date": "TIMESTAMP",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    
    # ============== STATUS FIELDS ==============
    "status": "VARCHAR(30) NOT NULL",
    "patient_status": "VARCHAR(30)",
    "encounter_status": "VARCHAR(30)",  # planned, in-progress, completed, cancelled
    "order_status": "VARCHAR(30)",
    "appointment_status": "VARCHAR(30)",
    "claim_status": "VARCHAR(30)",
    "active": "BOOLEAN DEFAULT TRUE",
    "is_active": "BOOLEAN DEFAULT TRUE",
    "is_deceased": "BOOLEAN DEFAULT FALSE",
    
    # ============== FINANCIAL ==============
    "charge_amount": "DECIMAL(12,2)",
    "payment_amount": "DECIMAL(12,2)",
    "copay": "DECIMAL(10,2)",
    "deductible": "DECIMAL(10,2)",
    "coinsurance": "DECIMAL(5,2)",
    "allowed_amount": "DECIMAL(12,2)",
    "billed_amount": "DECIMAL(12,2)",
    "balance": "DECIMAL(12,2)",
    
    # ============== MISCELLANEOUS ==============
    "notes": "TEXT",
    "comments": "TEXT",
    "description": "TEXT",
    "reason": "TEXT",
    "priority": "VARCHAR(30)",  # routine, urgent, emergency
    "severity": "VARCHAR(30)",  # mild, moderate, severe
    "acuity": "VARCHAR(30)",
    "room_number": "VARCHAR(20)",
    "bed_number": "VARCHAR(20)",
    "department": "VARCHAR(100)",
    "unit": "VARCHAR(100)",
    "facility": "VARCHAR(255)",
    "location": "VARCHAR(255)",
}


# Healthcare cardinality to SQL constraint mapping
HEALTHCARE_CARDINALITY_MAP: Dict[str, Dict[str, Any]] = {
    "0..1": {
        "nullable": True,
        "is_array": False,
        "constraint": None,
        "description": "Optional, at most one",
        "sql_example": "column_name VARCHAR(100)"
    },
    "0..*": {
        "nullable": True,
        "is_array": True,
        "constraint": None,
        "description": "Optional, many (requires separate table)",
        "sql_example": "-- Create junction/child table"
    },
    "1..1": {
        "nullable": False,
        "is_array": False,
        "constraint": "NOT NULL",
        "description": "Required, exactly one",
        "sql_example": "column_name VARCHAR(100) NOT NULL"
    },
    "1..*": {
        "nullable": False,
        "is_array": True,
        "constraint": "NOT NULL",
        "description": "Required, at least one (requires separate table with constraint)",
        "sql_example": "-- Create child table, add check constraint"
    },
    "N:1": {
        "description": "Many-to-One relationship",
        "implementation": "Foreign key in the 'many' side table",
        "sql_example": "provider_id INTEGER REFERENCES provider(id)"
    },
    "1:N": {
        "description": "One-to-Many relationship",
        "implementation": "Foreign key in the child table",
        "sql_example": "patient_id INTEGER REFERENCES patient(id)"
    },
    "M:N": {
        "description": "Many-to-Many relationship",
        "implementation": "Junction/association table required",
        "sql_example": "CREATE TABLE patient_diagnosis (patient_id, diagnosis_id, PRIMARY KEY)"
    },
}


# Healthcare lookup value sets that should become lookup tables
HEALTHCARE_LOOKUP_TABLES: Dict[str, List[str]] = {
    "gender": ["male", "female", "other", "unknown"],
    "marital_status": ["single", "married", "divorced", "widowed", "separated", "unknown"],
    "patient_status": ["active", "inactive", "deceased", "merged"],
    "encounter_status": ["planned", "arrived", "in-progress", "on-hold", "completed", "cancelled", "no-show"],
    "encounter_type": ["inpatient", "outpatient", "emergency", "observation", "telehealth", "home-health"],
    "appointment_status": ["scheduled", "confirmed", "checked-in", "in-progress", "completed", "cancelled", "no-show"],
    "order_status": ["pending", "active", "completed", "cancelled", "discontinued"],
    "medication_status": ["active", "on-hold", "completed", "cancelled", "stopped"],
    "claim_status": ["submitted", "pending", "approved", "denied", "paid", "appealed"],
    "priority": ["routine", "urgent", "stat", "asap", "emergency"],
    "severity": ["mild", "moderate", "severe", "critical"],
    "route_of_administration": ["oral", "intravenous", "intramuscular", "subcutaneous", "topical", "inhalation", "rectal", "ophthalmic", "otic"],
    "specimen_type": ["blood", "urine", "stool", "saliva", "tissue", "csf", "sputum", "swab"],
}


# Healthcare entity types commonly used in healthcare databases
HEALTHCARE_ENTITY_TYPES: List[str] = [
    # Core Administrative
    "Patient", "Provider", "Practitioner", "Physician", "Nurse",
    "Organization", "Facility", "Hospital", "Clinic", "Department",
    
    # Clinical
    "Encounter", "Visit", "Admission", "Appointment",
    "Diagnosis", "Condition", "Problem",
    "Procedure", "Surgery", "Treatment",
    "Observation", "VitalSign", "LabResult", "TestResult",
    "Allergy", "Immunization", "Vaccination",
    
    # Medication
    "Medication", "Drug", "Prescription", "MedicationOrder",
    "MedicationAdministration", "Dispensation",
    
    # Documentation
    "ClinicalNote", "ProgressNote", "DischargeSummary",
    "Consent", "Document",
    
    # Scheduling
    "Appointment", "Schedule", "Slot", "Availability",
    
    # Insurance/Financial
    "Insurance", "Coverage", "Claim", "Payment",
    "Charge", "Invoice", "Payer",
    
    # Supporting
    "Address", "ContactInfo", "EmergencyContact",
    "NextOfKin", "Guardian", "CareTeam",
]


# Common healthcare relationship patterns
HEALTHCARE_RELATIONSHIPS: Dict[str, Dict[str, Any]] = {
    "patient_encounter": {
        "entities": ["Patient", "Encounter"],
        "cardinality": "1:N",
        "description": "A patient can have many encounters",
        "fk_location": "Encounter",
        "fk_column": "patient_id"
    },
    "encounter_diagnosis": {
        "entities": ["Encounter", "Diagnosis"],
        "cardinality": "M:N",
        "description": "An encounter can have multiple diagnoses, a diagnosis can appear in multiple encounters",
        "junction_table": "encounter_diagnosis",
        "attributes": ["is_primary", "sequence_number", "diagnosis_date"]
    },
    "patient_provider": {
        "entities": ["Patient", "Provider"],
        "cardinality": "M:N",
        "description": "Patients can have multiple providers, providers have multiple patients",
        "junction_table": "patient_provider",
        "attributes": ["relationship_type", "start_date", "end_date", "is_primary"]
    },
    "encounter_provider": {
        "entities": ["Encounter", "Provider"],
        "cardinality": "M:N",
        "description": "Multiple providers can be involved in an encounter",
        "junction_table": "encounter_provider",
        "attributes": ["role", "participation_start", "participation_end"]
    },
    "patient_medication": {
        "entities": ["Patient", "Medication"],
        "cardinality": "M:N",
        "description": "Patients can be on multiple medications, medications can be prescribed to multiple patients",
        "junction_table": "prescription",
        "attributes": ["prescriber_id", "start_date", "end_date", "dosage", "frequency", "status"]
    },
    "encounter_procedure": {
        "entities": ["Encounter", "Procedure"],
        "cardinality": "M:N",
        "description": "Multiple procedures can be performed during an encounter",
        "junction_table": "encounter_procedure",
        "attributes": ["performed_by", "performed_date", "outcome", "notes"]
    },
    "provider_organization": {
        "entities": ["Provider", "Organization"],
        "cardinality": "M:N",
        "description": "Providers can work at multiple organizations",
        "junction_table": "provider_affiliation",
        "attributes": ["start_date", "end_date", "role", "is_active"]
    },
    "patient_insurance": {
        "entities": ["Patient", "Insurance"],
        "cardinality": "M:N",
        "description": "Patients can have multiple insurance coverages",
        "junction_table": "patient_coverage",
        "attributes": ["policy_number", "group_number", "start_date", "end_date", "is_primary"]
    },
}
