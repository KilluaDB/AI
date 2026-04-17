"""
Healthcare RAG Retriever for Database Schema Design

This module provides healthcare-specific ground-truth knowledge for designing
relational database schemas in the healthcare domain. It includes:
- Entity definitions and standard attributes
- Relationship patterns and cardinalities
- Data type mappings to PostgreSQL
- Normalization rules specific to healthcare
- Best practices and constraints
"""

from typing import List, Optional, Dict, Any

from ...base_rag import BaseRAGRetriever, RAGChunk, RAGConfig, ChunkType, generate_chunk_id
from .healthcare_config import (
    HealthcareConfig,
    HEALTHCARE_POSTGRES_TYPE_MAP,
    HEALTHCARE_CARDINALITY_MAP,
    HEALTHCARE_ENTITY_TYPES,
    HEALTHCARE_LOOKUP_TABLES,
    HEALTHCARE_RELATIONSHIPS,
)


class HealthcareRAGRetriever(BaseRAGRetriever):
    """
    Healthcare Domain RAG Retriever for database schema design.
    
    Provides ground-truth knowledge including:
    - Standard entity definitions (Patient, Provider, Encounter, etc.)
    - Healthcare data relationship patterns
    - Data type mappings to PostgreSQL
    - Cardinality and constraint rules
    - Healthcare-specific normalization guidelines
    """
    
    def __init__(self, config: Optional[RAGConfig] = None, healthcare_config: Optional[HealthcareConfig] = None):
        super().__init__(config)
        self.healthcare_config = healthcare_config or HealthcareConfig()
    
    def get_domain(self) -> str:
        return "healthcare"
    
    def _load_domain_knowledge(self) -> List[RAGChunk]:
        """Load healthcare-specific knowledge chunks"""
        chunks = []
        
        # Add entity definitions
        chunks.extend(self._get_entity_definitions())
        
        # Add relationship patterns
        chunks.extend(self._get_relationship_patterns())
        
        # Add datatype guidelines
        chunks.extend(self._get_datatype_guidelines())
        
        # Add cardinality rules
        chunks.extend(self._get_cardinality_rules())
        
        # Add normalization rules
        chunks.extend(self._get_normalization_rules())
        
        # Add healthcare design patterns
        chunks.extend(self._get_healthcare_patterns())
        
        # Add constraint rules
        chunks.extend(self._get_constraint_rules())
        
        return chunks
    
    def _get_entity_definitions(self) -> List[RAGChunk]:
        """Get healthcare entity definitions (ground truth)"""
        chunks = []
        
        # ==================== PATIENT ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("patient-entity", "Patient", "healthcare"),
            content="""
HEALTHCARE ENTITY: Patient
==========================
The Patient entity represents an individual receiving or registered to receive healthcare services.

REQUIRED ATTRIBUTES:
- patient_id: SERIAL PRIMARY KEY - Unique system identifier
- medical_record_number (MRN): VARCHAR(50) UNIQUE NOT NULL - Hospital/facility identifier
- first_name: VARCHAR(100) NOT NULL
- last_name: VARCHAR(100) NOT NULL
- date_of_birth: DATE NOT NULL - Critical for patient identification and age calculation

RECOMMENDED ATTRIBUTES:
- middle_name: VARCHAR(100)
- gender: VARCHAR(20) - Values: male, female, other, unknown (consider lookup table)
- ssn: VARCHAR(11) UNIQUE - Social Security Number (encrypted in production)
- marital_status: VARCHAR(30)
- race: VARCHAR(50)
- ethnicity: VARCHAR(50)
- primary_language: VARCHAR(50)
- is_deceased: BOOLEAN DEFAULT FALSE
- deceased_date: DATE

CONTACT INFORMATION (Consider separate table for multiple addresses):
- phone_number: VARCHAR(20)
- email: VARCHAR(255)
- street_address: VARCHAR(255)
- city: VARCHAR(100)
- state: VARCHAR(50)
- zip_code: VARCHAR(20)

AUDIT FIELDS:
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- active: BOOLEAN DEFAULT TRUE

RELATIONSHIPS:
- Patient 1:N Encounter (A patient can have many encounters)
- Patient 1:N Appointment (A patient can have many appointments)
- Patient M:N Provider (Patients have multiple providers, providers have multiple patients)
- Patient M:N Insurance (Patients can have multiple insurance coverages)
- Patient 1:N Prescription (A patient can have many prescriptions)
- Patient 1:N Allergy (A patient can have multiple allergies documented)

PRIMARY KEY: patient_id (surrogate key recommended)
BUSINESS KEY: medical_record_number (unique within facility)

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_patient_mrn ON patient(medical_record_number);
- CREATE INDEX idx_patient_name ON patient(last_name, first_name);
- CREATE INDEX idx_patient_dob ON patient(date_of_birth);
- CREATE INDEX idx_patient_ssn ON patient(ssn) WHERE ssn IS NOT NULL;
""",
            domain="healthcare",
            resource_type="Patient",
            chunk_type=ChunkType.DEFINITION,
            tags=["patient", "entity", "core", "demographics", "administrative"],
            trust_level=1.0
        ))
        
        # ==================== PROVIDER/PRACTITIONER ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("provider-entity", "Provider", "healthcare"),
            content="""
HEALTHCARE ENTITY: Provider (also called Practitioner, Physician, Clinician)
============================================================================
The Provider entity represents healthcare professionals who deliver care.

REQUIRED ATTRIBUTES:
- provider_id: SERIAL PRIMARY KEY
- first_name: VARCHAR(100) NOT NULL
- last_name: VARCHAR(100) NOT NULL
- npi: VARCHAR(10) UNIQUE - National Provider Identifier (10 digits, required in US)

RECOMMENDED ATTRIBUTES:
- middle_name: VARCHAR(100)
- credentials: VARCHAR(50) - MD, DO, NP, PA, RN, etc.
- specialty: VARCHAR(100) - Primary specialty
- subspecialty: VARCHAR(100)
- dea_number: VARCHAR(9) - For prescribing controlled substances
- license_number: VARCHAR(50)
- license_state: VARCHAR(2)
- license_expiration: DATE
- gender: VARCHAR(20)
- phone_number: VARCHAR(20)
- email: VARCHAR(255)
- active: BOOLEAN DEFAULT TRUE

RELATIONSHIPS:
- Provider M:N Patient (through care relationship)
- Provider M:N Encounter (providers participate in encounters)
- Provider M:N Organization (providers can work at multiple facilities)
- Provider 1:N Prescription (provider writes prescriptions)
- Provider 1:N Order (provider creates orders)

PRIMARY KEY: provider_id
BUSINESS KEY: npi (unique nationally in US healthcare)

SPECIAL CONSIDERATIONS:
- NPI is 10 digits, validate format: CHECK (npi ~ '^[0-9]{10}$')
- Consider separate table for multiple specialties
- Consider separate table for credentials/qualifications
- Providers may have multiple licenses in different states

INDEXING RECOMMENDATIONS:
- CREATE UNIQUE INDEX idx_provider_npi ON provider(npi);
- CREATE INDEX idx_provider_name ON provider(last_name, first_name);
- CREATE INDEX idx_provider_specialty ON provider(specialty);
""",
            domain="healthcare",
            resource_type="Provider",
            chunk_type=ChunkType.DEFINITION,
            tags=["provider", "practitioner", "physician", "entity", "core"],
            trust_level=1.0
        ))
        
        # ==================== ENCOUNTER/VISIT ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("encounter-entity", "Encounter", "healthcare"),
            content="""
HEALTHCARE ENTITY: Encounter (also called Visit, Admission)
===========================================================
The Encounter entity represents an interaction between patient and healthcare provider(s).

REQUIRED ATTRIBUTES:
- encounter_id: SERIAL PRIMARY KEY
- patient_id: INTEGER NOT NULL REFERENCES patient(id)
- encounter_type: VARCHAR(30) NOT NULL - inpatient, outpatient, emergency, observation, telehealth
- encounter_status: VARCHAR(30) NOT NULL - planned, arrived, in-progress, completed, cancelled
- admission_date: TIMESTAMP NOT NULL - Start of encounter

RECOMMENDED ATTRIBUTES:
- visit_number: VARCHAR(50) - Facility-assigned visit identifier
- discharge_date: TIMESTAMP - End of encounter (NULL if ongoing)
- attending_provider_id: INTEGER REFERENCES provider(id)
- department: VARCHAR(100)
- facility_id: INTEGER REFERENCES facility(id)
- room_number: VARCHAR(20)
- bed_number: VARCHAR(20)
- admit_source: VARCHAR(50) - physician referral, emergency, transfer, etc.
- discharge_disposition: VARCHAR(50) - home, SNF, AMA, expired, etc.
- chief_complaint: TEXT
- primary_diagnosis_id: INTEGER REFERENCES diagnosis(id)
- acuity_level: VARCHAR(20) - For emergency visits (1-5 ESI scale)
- length_of_stay: INTEGER - Calculated field or stored

AUDIT FIELDS:
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

RELATIONSHIPS:
- Encounter N:1 Patient (many encounters belong to one patient)
- Encounter M:N Provider (multiple providers per encounter)
- Encounter M:N Diagnosis (multiple diagnoses per encounter)
- Encounter 1:N Procedure (multiple procedures during encounter)
- Encounter 1:N Observation (vital signs, lab results)
- Encounter 1:N Order (orders placed during encounter)
- Encounter N:1 Facility (encounter occurs at one facility)

PRIMARY KEY: encounter_id
FOREIGN KEYS:
- patient_id REFERENCES patient(id) ON DELETE RESTRICT
- attending_provider_id REFERENCES provider(id)

CONSTRAINTS:
- CHECK (discharge_date IS NULL OR discharge_date >= admission_date)
- CHECK (encounter_status IN ('planned', 'arrived', 'in-progress', 'on-hold', 'completed', 'cancelled'))

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_encounter_patient ON encounter(patient_id);
- CREATE INDEX idx_encounter_date ON encounter(admission_date);
- CREATE INDEX idx_encounter_status ON encounter(encounter_status);
- CREATE INDEX idx_encounter_type ON encounter(encounter_type);
- CREATE INDEX idx_encounter_provider ON encounter(attending_provider_id);
""",
            domain="healthcare",
            resource_type="Encounter",
            chunk_type=ChunkType.DEFINITION,
            tags=["encounter", "visit", "admission", "entity", "clinical"],
            trust_level=1.0
        ))
        
        # ==================== DIAGNOSIS/CONDITION ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("diagnosis-entity", "Diagnosis", "healthcare"),
            content="""
HEALTHCARE ENTITY: Diagnosis (also called Condition, Problem)
=============================================================
The Diagnosis entity represents clinical conditions, problems, or diagnoses.

REQUIRED ATTRIBUTES:
- diagnosis_id: SERIAL PRIMARY KEY
- diagnosis_code: VARCHAR(20) NOT NULL - ICD-10 code (e.g., 'J18.9' for pneumonia)
- diagnosis_description: TEXT NOT NULL - Human-readable description
- code_system: VARCHAR(20) DEFAULT 'ICD-10' - ICD-10, ICD-9, SNOMED-CT

RECOMMENDED ATTRIBUTES:
- diagnosis_name: VARCHAR(255) - Short name
- category: VARCHAR(100) - Diagnosis category
- is_chronic: BOOLEAN DEFAULT FALSE
- is_active: BOOLEAN DEFAULT TRUE

DIAGNOSIS INSTANCE (When linking to patient/encounter):
Create a junction table 'patient_diagnosis' or 'encounter_diagnosis' with:
- patient_id / encounter_id: INTEGER REFERENCES
- diagnosis_id: INTEGER REFERENCES diagnosis(id)
- onset_date: DATE - When condition started
- resolution_date: DATE - When condition resolved
- clinical_status: VARCHAR(30) - active, recurrence, relapse, inactive, remission, resolved
- verification_status: VARCHAR(30) - confirmed, provisional, differential, refuted
- is_primary: BOOLEAN - Primary diagnosis for encounter
- sequence_number: SMALLINT - Diagnosis ranking
- diagnosed_by: INTEGER REFERENCES provider(id)
- notes: TEXT

RELATIONSHIPS:
- Diagnosis M:N Patient (through patient_diagnosis)
- Diagnosis M:N Encounter (through encounter_diagnosis)
- Diagnosis N:1 Provider (who made the diagnosis)

SPECIAL CONSIDERATIONS:
- ICD-10 codes have specific format: Letter + 2 digits + optional decimal + up to 4 more characters
- Example: A00.0, J18.9, M54.5
- Consider separate lookup table for ICD-10 codes with full hierarchy
- Primary diagnosis is important for billing

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_diagnosis_code ON diagnosis(diagnosis_code);
- CREATE INDEX idx_patient_diagnosis_patient ON patient_diagnosis(patient_id);
- CREATE INDEX idx_encounter_diagnosis_encounter ON encounter_diagnosis(encounter_id);
""",
            domain="healthcare",
            resource_type="Diagnosis",
            chunk_type=ChunkType.DEFINITION,
            tags=["diagnosis", "condition", "problem", "entity", "clinical", "icd10"],
            trust_level=1.0
        ))
        
        # ==================== MEDICATION ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("medication-entity", "Medication", "healthcare"),
            content="""
HEALTHCARE ENTITY: Medication (Drug)
====================================
The Medication entity represents drugs and medications that can be prescribed.

REQUIRED ATTRIBUTES:
- medication_id: SERIAL PRIMARY KEY
- medication_name: VARCHAR(255) NOT NULL
- generic_name: VARCHAR(255) NOT NULL

RECOMMENDED ATTRIBUTES:
- brand_name: VARCHAR(255)
- ndc_code: VARCHAR(20) UNIQUE - National Drug Code (11 digits: 5-4-2 or 4-4-2 format)
- rxnorm_code: VARCHAR(20) - RxNorm identifier
- drug_class: VARCHAR(100) - Therapeutic class
- form: VARCHAR(50) - tablet, capsule, injection, liquid, etc.
- strength: VARCHAR(100) - e.g., "500mg", "10mg/5mL"
- manufacturer: VARCHAR(255)
- is_controlled: BOOLEAN DEFAULT FALSE
- dea_schedule: VARCHAR(5) - I, II, III, IV, V for controlled substances
- is_active: BOOLEAN DEFAULT TRUE

PRESCRIPTION (Linking medication to patient):
Create a 'prescription' or 'medication_order' table:
- prescription_id: SERIAL PRIMARY KEY
- patient_id: INTEGER NOT NULL REFERENCES patient(id)
- medication_id: INTEGER NOT NULL REFERENCES medication(id)
- prescriber_id: INTEGER NOT NULL REFERENCES provider(id)
- encounter_id: INTEGER REFERENCES encounter(id)
- order_date: TIMESTAMP NOT NULL
- start_date: DATE
- end_date: DATE
- dose_amount: DECIMAL(10,3)
- dose_unit: VARCHAR(50)
- frequency: VARCHAR(100) - BID, TID, Q4H, PRN, etc.
- route: VARCHAR(50) - oral, IV, IM, topical, etc.
- quantity: INTEGER
- refills_allowed: SMALLINT
- refills_remaining: SMALLINT
- instructions: TEXT - SIG (directions for use)
- status: VARCHAR(30) - active, completed, cancelled, on-hold
- pharmacy_id: INTEGER REFERENCES pharmacy(id)
- is_prn: BOOLEAN DEFAULT FALSE - As needed

RELATIONSHIPS:
- Medication M:N Patient (through prescription)
- Prescription N:1 Patient
- Prescription N:1 Medication
- Prescription N:1 Provider (prescriber)
- Prescription N:1 Encounter (optional - where prescribed)

SPECIAL CONSIDERATIONS:
- Controlled substances require DEA number from prescriber
- Drug-drug interactions should be checked
- Allergy checking is critical
- Consider medication history table for tracking changes

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_medication_name ON medication(medication_name);
- CREATE INDEX idx_medication_generic ON medication(generic_name);
- CREATE UNIQUE INDEX idx_medication_ndc ON medication(ndc_code) WHERE ndc_code IS NOT NULL;
- CREATE INDEX idx_prescription_patient ON prescription(patient_id);
- CREATE INDEX idx_prescription_status ON prescription(status);
""",
            domain="healthcare",
            resource_type="Medication",
            chunk_type=ChunkType.DEFINITION,
            tags=["medication", "drug", "prescription", "pharmacy", "entity"],
            trust_level=1.0
        ))
        
        # ==================== OBSERVATION/VITAL SIGNS ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("observation-entity", "Observation", "healthcare"),
            content="""
HEALTHCARE ENTITY: Observation (Vital Signs, Lab Results, Test Results)
=======================================================================
The Observation entity represents clinical measurements and findings.

FOR VITAL SIGNS:
Table: vital_sign
- vital_sign_id: SERIAL PRIMARY KEY
- patient_id: INTEGER NOT NULL REFERENCES patient(id)
- encounter_id: INTEGER REFERENCES encounter(id)
- recorded_at: TIMESTAMP NOT NULL
- recorded_by: INTEGER REFERENCES provider(id)
- blood_pressure_systolic: SMALLINT - mmHg (normal: 90-120)
- blood_pressure_diastolic: SMALLINT - mmHg (normal: 60-80)
- heart_rate: SMALLINT - beats per minute (normal: 60-100)
- respiratory_rate: SMALLINT - breaths per minute (normal: 12-20)
- temperature: DECIMAL(4,1) - Fahrenheit (normal: 97.8-99.1)
- temperature_unit: VARCHAR(1) DEFAULT 'F' - F or C
- oxygen_saturation: DECIMAL(5,2) - percentage (normal: 95-100)
- weight: DECIMAL(6,2) - kg or lbs
- weight_unit: VARCHAR(3) DEFAULT 'kg'
- height: DECIMAL(5,2) - cm or inches
- height_unit: VARCHAR(2) DEFAULT 'cm'
- bmi: DECIMAL(4,1) - calculated
- pain_level: SMALLINT - 0-10 scale
- notes: TEXT

FOR LAB RESULTS:
Table: lab_result
- lab_result_id: SERIAL PRIMARY KEY
- patient_id: INTEGER NOT NULL REFERENCES patient(id)
- encounter_id: INTEGER REFERENCES encounter(id)
- order_id: INTEGER REFERENCES lab_order(id)
- test_code: VARCHAR(20) NOT NULL - LOINC code
- test_name: VARCHAR(255) NOT NULL
- result_value: VARCHAR(255) - Can be numeric or text
- result_numeric: DECIMAL(12,4) - For numeric values
- result_unit: VARCHAR(50)
- reference_range_low: DECIMAL(12,4)
- reference_range_high: DECIMAL(12,4)
- reference_range_text: VARCHAR(100)
- abnormal_flag: VARCHAR(10) - H (high), L (low), N (normal), A (abnormal)
- result_status: VARCHAR(30) - preliminary, final, corrected, cancelled
- specimen_type: VARCHAR(50) - blood, urine, etc.
- specimen_collected_at: TIMESTAMP
- result_date: TIMESTAMP
- performing_lab: VARCHAR(255)
- notes: TEXT

RELATIONSHIPS:
- Observation N:1 Patient
- Observation N:1 Encounter (optional)
- Observation N:1 Provider (who recorded)
- Lab Result N:1 Order (what was ordered)

SPECIAL CONSIDERATIONS:
- LOINC codes are standard for lab tests
- Consider separate table for test catalog
- Abnormal flags trigger clinical alerts
- Results may be amended/corrected (track history)

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_vital_patient ON vital_sign(patient_id);
- CREATE INDEX idx_vital_encounter ON vital_sign(encounter_id);
- CREATE INDEX idx_vital_recorded ON vital_sign(recorded_at);
- CREATE INDEX idx_lab_patient ON lab_result(patient_id);
- CREATE INDEX idx_lab_test ON lab_result(test_code);
- CREATE INDEX idx_lab_abnormal ON lab_result(abnormal_flag) WHERE abnormal_flag != 'N';
""",
            domain="healthcare",
            resource_type="Observation",
            chunk_type=ChunkType.DEFINITION,
            tags=["observation", "vital-signs", "lab", "result", "clinical", "entity"],
            trust_level=1.0
        ))
        
        # ==================== APPOINTMENT ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("appointment-entity", "Appointment", "healthcare"),
            content="""
HEALTHCARE ENTITY: Appointment (Scheduling)
==========================================
The Appointment entity represents scheduled healthcare visits.

REQUIRED ATTRIBUTES:
- appointment_id: SERIAL PRIMARY KEY
- patient_id: INTEGER NOT NULL REFERENCES patient(id)
- provider_id: INTEGER NOT NULL REFERENCES provider(id)
- appointment_datetime: TIMESTAMP NOT NULL
- appointment_status: VARCHAR(30) NOT NULL DEFAULT 'scheduled'

RECOMMENDED ATTRIBUTES:
- appointment_type: VARCHAR(50) - new patient, follow-up, procedure, telehealth
- duration_minutes: INTEGER DEFAULT 30
- end_datetime: TIMESTAMP - calculated from start + duration
- department: VARCHAR(100)
- facility_id: INTEGER REFERENCES facility(id)
- room: VARCHAR(20)
- reason: TEXT - Reason for visit
- chief_complaint: TEXT
- priority: VARCHAR(20) - routine, urgent
- notes: TEXT
- created_by: INTEGER REFERENCES user(id)
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- cancelled_at: TIMESTAMP
- cancellation_reason: TEXT
- checked_in_at: TIMESTAMP
- encounter_id: INTEGER REFERENCES encounter(id) - Link to resulting encounter

APPOINTMENT STATUS VALUES:
- scheduled: Appointment is booked
- confirmed: Patient confirmed attendance
- checked-in: Patient has arrived
- in-progress: Patient is being seen
- completed: Appointment finished
- cancelled: Cancelled before occurrence
- no-show: Patient did not show up
- rescheduled: Moved to different time

RELATIONSHIPS:
- Appointment N:1 Patient
- Appointment N:1 Provider
- Appointment N:1 Facility
- Appointment 0..1:1 Encounter (may generate encounter when completed)

SPECIAL CONSIDERATIONS:
- Check for scheduling conflicts
- Consider recurring appointments
- Track wait times (checked_in_at to actual start)
- May need slot/availability management

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_appointment_patient ON appointment(patient_id);
- CREATE INDEX idx_appointment_provider ON appointment(provider_id);
- CREATE INDEX idx_appointment_datetime ON appointment(appointment_datetime);
- CREATE INDEX idx_appointment_status ON appointment(appointment_status);
- CREATE INDEX idx_appointment_date ON appointment(DATE(appointment_datetime));
""",
            domain="healthcare",
            resource_type="Appointment",
            chunk_type=ChunkType.DEFINITION,
            tags=["appointment", "scheduling", "visit", "entity"],
            trust_level=1.0
        ))
        
        # ==================== INSURANCE/COVERAGE ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("insurance-entity", "Insurance", "healthcare"),
            content="""
HEALTHCARE ENTITY: Insurance (Coverage, Payer)
==============================================
The Insurance entity represents health insurance coverage.

INSURANCE/PAYER TABLE:
- insurance_id: SERIAL PRIMARY KEY
- payer_name: VARCHAR(255) NOT NULL
- payer_type: VARCHAR(50) - commercial, medicare, medicaid, tricare, self-pay
- payer_code: VARCHAR(50)
- phone_number: VARCHAR(20)
- claims_address: TEXT
- is_active: BOOLEAN DEFAULT TRUE

PATIENT COVERAGE TABLE (Junction):
- coverage_id: SERIAL PRIMARY KEY
- patient_id: INTEGER NOT NULL REFERENCES patient(id)
- insurance_id: INTEGER NOT NULL REFERENCES insurance(id)
- policy_number: VARCHAR(50) NOT NULL
- group_number: VARCHAR(50)
- member_id: VARCHAR(50)
- subscriber_id: VARCHAR(50)
- subscriber_relationship: VARCHAR(30) - self, spouse, child, other
- subscriber_name: VARCHAR(255)
- subscriber_dob: DATE
- coverage_type: VARCHAR(30) - medical, dental, vision, pharmacy
- coverage_start_date: DATE NOT NULL
- coverage_end_date: DATE
- is_primary: BOOLEAN DEFAULT FALSE
- is_active: BOOLEAN DEFAULT TRUE
- copay_amount: DECIMAL(10,2)
- deductible_amount: DECIMAL(10,2)
- deductible_met: DECIMAL(10,2)
- out_of_pocket_max: DECIMAL(10,2)
- out_of_pocket_met: DECIMAL(10,2)
- verification_date: DATE
- verification_status: VARCHAR(30)
- authorization_required: BOOLEAN DEFAULT FALSE

RELATIONSHIPS:
- Insurance M:N Patient (through patient_coverage)
- Coverage N:1 Patient
- Coverage N:1 Insurance
- Encounter N:1 Coverage (which insurance to bill)
- Claim N:1 Coverage

SPECIAL CONSIDERATIONS:
- Patients often have multiple coverages (coordination of benefits)
- Primary vs secondary insurance determination
- Insurance eligibility verification is critical
- Coverage changes over time - track history
- Consider separate table for insurance plans

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_coverage_patient ON patient_coverage(patient_id);
- CREATE INDEX idx_coverage_insurance ON patient_coverage(insurance_id);
- CREATE INDEX idx_coverage_policy ON patient_coverage(policy_number);
- CREATE INDEX idx_coverage_dates ON patient_coverage(coverage_start_date, coverage_end_date);
""",
            domain="healthcare",
            resource_type="Insurance",
            chunk_type=ChunkType.DEFINITION,
            tags=["insurance", "coverage", "payer", "billing", "entity"],
            trust_level=1.0
        ))
        
        # ==================== ORGANIZATION/FACILITY ENTITY ====================
        chunks.append(RAGChunk(
            id=generate_chunk_id("organization-entity", "Organization", "healthcare"),
            content="""
HEALTHCARE ENTITY: Organization (Facility, Hospital, Clinic)
============================================================
The Organization entity represents healthcare facilities and organizations.

REQUIRED ATTRIBUTES:
- organization_id: SERIAL PRIMARY KEY
- organization_name: VARCHAR(255) NOT NULL
- organization_type: VARCHAR(50) NOT NULL - hospital, clinic, laboratory, pharmacy, imaging

RECOMMENDED ATTRIBUTES:
- npi: VARCHAR(10) UNIQUE - Organization NPI
- tax_id: VARCHAR(15) UNIQUE
- parent_organization_id: INTEGER REFERENCES organization(id) - For hierarchies
- phone_number: VARCHAR(20)
- fax_number: VARCHAR(20)
- email: VARCHAR(255)
- website: VARCHAR(255)
- street_address: VARCHAR(255)
- city: VARCHAR(100)
- state: VARCHAR(50)
- zip_code: VARCHAR(20)
- country: VARCHAR(100) DEFAULT 'USA'
- is_active: BOOLEAN DEFAULT TRUE
- license_number: VARCHAR(50)
- accreditation: VARCHAR(100) - Joint Commission, etc.

DEPARTMENT TABLE (Child of Organization):
- department_id: SERIAL PRIMARY KEY
- organization_id: INTEGER NOT NULL REFERENCES organization(id)
- department_name: VARCHAR(255) NOT NULL
- department_code: VARCHAR(20)
- cost_center: VARCHAR(20)
- is_active: BOOLEAN DEFAULT TRUE

RELATIONSHIPS:
- Organization 1:N Department
- Organization 1:N Encounter (encounters happen at facilities)
- Organization M:N Provider (providers work at organizations)
- Organization N:1 Organization (parent-child for hierarchies)

HIERARCHICAL STRUCTURE:
Example: Health System → Hospital → Department → Unit
- Use parent_organization_id for self-referential relationship
- Use recursive CTE for hierarchy queries

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_org_name ON organization(organization_name);
- CREATE INDEX idx_org_type ON organization(organization_type);
- CREATE INDEX idx_org_parent ON organization(parent_organization_id);
- CREATE UNIQUE INDEX idx_org_npi ON organization(npi) WHERE npi IS NOT NULL;
""",
            domain="healthcare",
            resource_type="Organization",
            chunk_type=ChunkType.DEFINITION,
            tags=["organization", "facility", "hospital", "clinic", "entity"],
            trust_level=1.0
        ))
        
        return chunks
    
    def _get_relationship_patterns(self) -> List[RAGChunk]:
        """Get healthcare relationship patterns"""
        chunks = []
        
        chunks.append(RAGChunk(
            id=generate_chunk_id("relationship-patterns", "Relationships", "healthcare"),
            content="""
HEALTHCARE RELATIONSHIP PATTERNS (Ground Truth)
===============================================

1. PATIENT-ENCOUNTER (1:N)
   - One patient has many encounters
   - Each encounter belongs to one patient
   - Implementation: patient_id in encounter table
   ```sql
   CREATE TABLE encounter (
       encounter_id SERIAL PRIMARY KEY,
       patient_id INTEGER NOT NULL REFERENCES patient(id),
       -- other columns
   );
   ```

2. ENCOUNTER-DIAGNOSIS (M:N)
   - An encounter can have multiple diagnoses
   - A diagnosis can appear in multiple encounters
   - Implementation: Junction table with attributes
   ```sql
   CREATE TABLE encounter_diagnosis (
       encounter_id INTEGER NOT NULL REFERENCES encounter(id),
       diagnosis_id INTEGER NOT NULL REFERENCES diagnosis(id),
       is_primary BOOLEAN DEFAULT FALSE,
       sequence_number SMALLINT,
       diagnosed_by INTEGER REFERENCES provider(id),
       diagnosis_date DATE,
       PRIMARY KEY (encounter_id, diagnosis_id)
   );
   ```

3. PATIENT-PROVIDER (M:N)
   - Patients have multiple providers (PCP, specialists)
   - Providers have multiple patients
   - Implementation: Junction table with relationship details
   ```sql
   CREATE TABLE patient_provider (
       patient_id INTEGER NOT NULL REFERENCES patient(id),
       provider_id INTEGER NOT NULL REFERENCES provider(id),
       relationship_type VARCHAR(50), -- PCP, specialist, surgeon
       is_primary BOOLEAN DEFAULT FALSE,
       start_date DATE,
       end_date DATE,
       PRIMARY KEY (patient_id, provider_id, relationship_type)
   );
   ```

4. ENCOUNTER-PROVIDER (M:N)
   - Multiple providers participate in an encounter
   - Providers participate in multiple encounters
   - Implementation: Junction table with role
   ```sql
   CREATE TABLE encounter_provider (
       encounter_id INTEGER NOT NULL REFERENCES encounter(id),
       provider_id INTEGER NOT NULL REFERENCES provider(id),
       role VARCHAR(50) NOT NULL, -- attending, consulting, referring
       PRIMARY KEY (encounter_id, provider_id, role)
   );
   ```

5. PATIENT-MEDICATION (M:N via Prescription)
   - Patients take multiple medications
   - Medications are prescribed to multiple patients
   - Implementation: Prescription table as association
   ```sql
   CREATE TABLE prescription (
       prescription_id SERIAL PRIMARY KEY,
       patient_id INTEGER NOT NULL REFERENCES patient(id),
       medication_id INTEGER NOT NULL REFERENCES medication(id),
       prescriber_id INTEGER NOT NULL REFERENCES provider(id),
       encounter_id INTEGER REFERENCES encounter(id),
       -- prescription details
   );
   ```

6. ORGANIZATION HIERARCHY (Self-referential 1:N)
   - Organizations can have sub-organizations
   - Implementation: Self-referential foreign key
   ```sql
   CREATE TABLE organization (
       organization_id SERIAL PRIMARY KEY,
       organization_name VARCHAR(255) NOT NULL,
       parent_organization_id INTEGER REFERENCES organization(id),
       -- other columns
   );
   ```

7. ENCOUNTER-PROCEDURE (M:N)
   ```sql
   CREATE TABLE encounter_procedure (
       encounter_id INTEGER NOT NULL REFERENCES encounter(id),
       procedure_id INTEGER NOT NULL REFERENCES procedure(id),
       performed_by INTEGER REFERENCES provider(id),
       performed_at TIMESTAMP,
       outcome TEXT,
       PRIMARY KEY (encounter_id, procedure_id)
   );
   ```
""",
            domain="healthcare",
            resource_type="Relationship",
            chunk_type=ChunkType.PATTERN,
            tags=["relationship", "pattern", "cardinality", "foreign-key"],
            trust_level=1.0
        ))
        
        return chunks
    
    def _get_datatype_guidelines(self) -> List[RAGChunk]:
        """Get healthcare data type mapping guidelines"""
        chunks = []
        
        chunks.append(RAGChunk(
            id=generate_chunk_id("datatype-mapping", "DataType", "healthcare"),
            content="""
HEALTHCARE DATA TYPE MAPPING TO POSTGRESQL
==========================================

IDENTIFIERS:
- patient_id, provider_id, etc. → SERIAL PRIMARY KEY (auto-increment)
- medical_record_number (MRN) → VARCHAR(50) UNIQUE NOT NULL
- npi (National Provider Identifier) → VARCHAR(10) with CHECK constraint
- ssn (Social Security Number) → VARCHAR(11) (format: XXX-XX-XXXX)
- policy_number, member_id → VARCHAR(50)

NAMES AND TEXT:
- first_name, last_name → VARCHAR(100) NOT NULL
- middle_name → VARCHAR(100) (nullable)
- full_name → VARCHAR(255)
- description, notes, comments → TEXT
- chief_complaint, assessment → TEXT

DATES AND TIMES:
- date_of_birth → DATE NOT NULL
- admission_date, discharge_date → TIMESTAMP (with timezone consideration)
- appointment_datetime → TIMESTAMP NOT NULL
- created_at, updated_at → TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- service_date → DATE

STATUS FIELDS:
- status → VARCHAR(30) NOT NULL (use lookup table or CHECK constraint)
- is_active, is_primary → BOOLEAN DEFAULT FALSE/TRUE
- is_deceased → BOOLEAN DEFAULT FALSE

CLINICAL CODES:
- diagnosis_code (ICD-10) → VARCHAR(20)
- procedure_code (CPT) → VARCHAR(20)
- test_code (LOINC) → VARCHAR(20)
- medication_code (NDC) → VARCHAR(20)
- code_system → VARCHAR(20) (ICD-10, SNOMED, LOINC, etc.)

VITAL SIGNS:
- blood_pressure_systolic/diastolic → SMALLINT (mmHg)
- heart_rate, respiratory_rate → SMALLINT
- temperature → DECIMAL(4,1)
- oxygen_saturation → DECIMAL(5,2)
- weight → DECIMAL(6,2)
- height → DECIMAL(5,2)
- bmi → DECIMAL(4,1)

LAB VALUES:
- result_value → DECIMAL(12,4) for numerics, VARCHAR(255) for text
- reference_range_low/high → DECIMAL(12,4)

FINANCIAL:
- amount, charge, payment → DECIMAL(12,2)
- percentage (coinsurance) → DECIMAL(5,2)

CONTACT INFORMATION:
- phone_number → VARCHAR(20)
- email → VARCHAR(255)
- address fields → VARCHAR(255) or TEXT
- zip_code → VARCHAR(20) (international support)
- state → VARCHAR(50)

GENDER/STATUS ENUMS (Use lookup table or VARCHAR with CHECK):
- gender → VARCHAR(20) CHECK (gender IN ('male', 'female', 'other', 'unknown'))
- encounter_status → VARCHAR(30) CHECK (...)

CODE FORMAT VALIDATIONS:
- NPI: 10 digits → CHECK (npi ~ '^[0-9]{10}$')
- ICD-10: Letter + digits → CHECK (code ~ '^[A-Z][0-9]')
- SSN: XXX-XX-XXXX → CHECK (ssn ~ '^[0-9]{3}-[0-9]{2}-[0-9]{4}$')
""",
            domain="healthcare",
            resource_type="DataType",
            chunk_type=ChunkType.GUIDELINE,
            tags=["datatype", "mapping", "postgresql", "validation"],
            trust_level=1.0
        ))
        
        return chunks
    
    def _get_cardinality_rules(self) -> List[RAGChunk]:
        """Get cardinality to SQL constraint rules"""
        chunks = []
        
        chunks.append(RAGChunk(
            id=generate_chunk_id("cardinality-rules", "Cardinality", "healthcare"),
            content="""
HEALTHCARE CARDINALITY RULES AND SQL IMPLEMENTATION
===================================================

CARDINALITY NOTATION:
- 0..1 : Zero or one (optional single value)
- 1..1 : Exactly one (required single value)
- 0..* : Zero or more (optional multiple values)
- 1..* : One or more (required, at least one)
- N:1  : Many-to-One relationship
- 1:N  : One-to-Many relationship
- M:N  : Many-to-Many relationship

SQL IMPLEMENTATION RULES:

1. 0..1 (Optional, single value)
   - Column in same table, NULLABLE
   ```sql
   middle_name VARCHAR(100)  -- No NOT NULL
   ```

2. 1..1 (Required, single value)
   - Column in same table, NOT NULL
   ```sql
   first_name VARCHAR(100) NOT NULL
   date_of_birth DATE NOT NULL
   ```

3. 0..* (Optional, multiple values)
   - Separate child table with nullable foreign key or no constraint
   ```sql
   CREATE TABLE patient_address (
       address_id SERIAL PRIMARY KEY,
       patient_id INTEGER REFERENCES patient(id),
       -- Patient can have 0 or more addresses
   );
   ```

4. 1..* (Required, at least one)
   - Separate child table
   - Application logic or trigger must enforce "at least one"
   ```sql
   CREATE TABLE patient_identifier (
       identifier_id SERIAL PRIMARY KEY,
       patient_id INTEGER NOT NULL REFERENCES patient(id),
       -- Must have at least one identifier
   );
   -- Add trigger or application logic to enforce
   ```

5. N:1 (Many-to-One)
   - Foreign key in the "many" side table
   ```sql
   CREATE TABLE encounter (
       patient_id INTEGER NOT NULL REFERENCES patient(id)
       -- Many encounters per patient
   );
   ```

6. 1:N (One-to-Many)
   - Same as N:1, viewed from opposite direction
   - Foreign key in child table
   ```sql
   CREATE TABLE prescription (
       patient_id INTEGER NOT NULL REFERENCES patient(id)
       -- One patient has many prescriptions
   );
   ```

7. M:N (Many-to-Many)
   - Junction/association table required
   ```sql
   CREATE TABLE encounter_diagnosis (
       encounter_id INTEGER NOT NULL REFERENCES encounter(id),
       diagnosis_id INTEGER NOT NULL REFERENCES diagnosis(id),
       PRIMARY KEY (encounter_id, diagnosis_id)
   );
   ```

FOREIGN KEY ACTIONS:
- ON DELETE RESTRICT : Prevent deletion if children exist (default, safest)
- ON DELETE CASCADE  : Delete children when parent deleted (use carefully)
- ON DELETE SET NULL : Set FK to NULL when parent deleted
- ON UPDATE CASCADE  : Update FK when parent PK changes
""",
            domain="healthcare",
            resource_type="Cardinality",
            chunk_type=ChunkType.RULE,
            tags=["cardinality", "foreign-key", "constraint", "rule"],
            trust_level=1.0
        ))
        
        return chunks
    
    def _get_normalization_rules(self) -> List[RAGChunk]:
        """Get healthcare-specific normalization rules"""
        chunks = []
        
        chunks.append(RAGChunk(
            id=generate_chunk_id("normalization-rules", "Normalization", "healthcare"),
            content="""
HEALTHCARE DATABASE NORMALIZATION RULES
=======================================

FIRST NORMAL FORM (1NF):
- Eliminate repeating groups
- Each column contains atomic values

HEALTHCARE 1NF VIOLATIONS TO FIX:
❌ BAD: phone_numbers VARCHAR(255) -- "555-1234, 555-5678"
✅ GOOD: Separate patient_phone table with one number per row

❌ BAD: diagnoses TEXT -- "J18.9, E11.9, I10"
✅ GOOD: Separate encounter_diagnosis junction table

❌ BAD: allergies VARCHAR(500) -- "Penicillin, Aspirin, Shellfish"  
✅ GOOD: Separate patient_allergy table

SECOND NORMAL FORM (2NF):
- Must be in 1NF
- All non-key attributes fully dependent on entire primary key

HEALTHCARE 2NF VIOLATIONS TO FIX:
❌ BAD: encounter_diagnosis with columns depending only on diagnosis_id
  (encounter_id, diagnosis_id, diagnosis_name, diagnosis_description)
  -- diagnosis_name depends only on diagnosis_id, not full key
  
✅ GOOD: Separate diagnosis table for diagnosis attributes
  diagnosis(diagnosis_id, diagnosis_name, diagnosis_description)
  encounter_diagnosis(encounter_id, diagnosis_id, is_primary)

THIRD NORMAL FORM (3NF):
- Must be in 2NF
- No transitive dependencies (non-key → non-key)

HEALTHCARE 3NF VIOLATIONS TO FIX:
❌ BAD: patient table with provider_name depending on provider_id
  patient(patient_id, ..., provider_id, provider_name, provider_npi)
  -- provider_name depends on provider_id, not patient_id
  
✅ GOOD: Separate provider table
  provider(provider_id, provider_name, npi, ...)
  patient(patient_id, ..., primary_provider_id REFERENCES provider)

❌ BAD: encounter with facility details
  encounter(encounter_id, facility_id, facility_name, facility_address)
  
✅ GOOD: Separate facility table
  facility(facility_id, facility_name, address, ...)
  encounter(encounter_id, facility_id REFERENCES facility)

HEALTHCARE-SPECIFIC NORMALIZATION PATTERNS:

1. CODE TABLES (Lookup Tables):
   - Create separate tables for standard codes
   ```sql
   CREATE TABLE icd10_code (
       code VARCHAR(20) PRIMARY KEY,
       description TEXT NOT NULL,
       category VARCHAR(100)
   );
   ```

2. PATIENT DEMOGRAPHICS:
   - Addresses, phones, identifiers → separate tables (1NF)
   - Emergency contacts → separate table

3. CLINICAL HISTORY:
   - Problem list, medication history → temporal tables with dates

4. HIERARCHICAL DATA:
   - Organization structure → self-referential with parent_id
   - Diagnosis categories → consider closure table or nested sets

DENORMALIZATION CONSIDERATIONS:
Sometimes denormalization is acceptable for:
- Frequently accessed derived data (e.g., age calculated from DOB)
- Read-heavy reporting tables
- Audit/history tables (snapshot data)

Always document denormalization decisions!
""",
            domain="healthcare",
            resource_type="Normalization",
            chunk_type=ChunkType.RULE,
            tags=["normalization", "1nf", "2nf", "3nf", "rule"],
            trust_level=1.0
        ))
        
        return chunks
    
    def _get_healthcare_patterns(self) -> List[RAGChunk]:
        """Get healthcare database design patterns"""
        chunks = []
        
        chunks.append(RAGChunk(
            id=generate_chunk_id("design-patterns", "Pattern", "healthcare"),
            content="""
HEALTHCARE DATABASE DESIGN PATTERNS
===================================

1. TEMPORAL DATA PATTERN
   Track historical changes in healthcare data:
   ```sql
   CREATE TABLE patient_insurance_history (
       history_id SERIAL PRIMARY KEY,
       patient_id INTEGER NOT NULL REFERENCES patient(id),
       insurance_id INTEGER NOT NULL REFERENCES insurance(id),
       policy_number VARCHAR(50),
       effective_date DATE NOT NULL,
       termination_date DATE,
       is_current BOOLEAN DEFAULT TRUE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. AUDIT TRAIL PATTERN
   Track all changes for compliance (HIPAA):
   ```sql
   CREATE TABLE audit_log (
       audit_id SERIAL PRIMARY KEY,
       table_name VARCHAR(100) NOT NULL,
       record_id INTEGER NOT NULL,
       action VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
       old_values JSONB,
       new_values JSONB,
       changed_by INTEGER REFERENCES user(id),
       changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       ip_address INET,
       reason TEXT
   );
   ```

3. CLINICAL STATUS HISTORY PATTERN
   Track condition/order status changes:
   ```sql
   CREATE TABLE order_status_history (
       history_id SERIAL PRIMARY KEY,
       order_id INTEGER NOT NULL REFERENCES clinical_order(id),
       old_status VARCHAR(30),
       new_status VARCHAR(30) NOT NULL,
       changed_by INTEGER REFERENCES provider(id),
       changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       reason TEXT
   );
   ```

4. EFFECTIVE DATING PATTERN
   For insurance, medications, problems:
   ```sql
   CREATE TABLE medication_order (
       ...
       start_date DATE NOT NULL,
       end_date DATE, -- NULL means ongoing
       discontinued_date DATE,
       discontinued_reason TEXT
   );
   -- Query active: WHERE start_date <= CURRENT_DATE 
   --               AND (end_date IS NULL OR end_date >= CURRENT_DATE)
   ```

5. POLYMORPHIC RESULT PATTERN
   Lab results can be numeric, text, or coded:
   ```sql
   CREATE TABLE lab_result (
       result_id SERIAL PRIMARY KEY,
       result_type VARCHAR(20) NOT NULL, -- numeric, text, coded
       result_numeric DECIMAL(12,4),
       result_text TEXT,
       result_code VARCHAR(50),
       result_unit VARCHAR(50)
   );
   ```

6. CONTACT INFORMATION PATTERN
   Flexible multiple contacts:
   ```sql
   CREATE TABLE entity_contact (
       contact_id SERIAL PRIMARY KEY,
       entity_type VARCHAR(30) NOT NULL, -- patient, provider, organization
       entity_id INTEGER NOT NULL,
       contact_type VARCHAR(30) NOT NULL, -- phone, email, fax
       contact_value VARCHAR(255) NOT NULL,
       contact_use VARCHAR(30), -- home, work, mobile
       is_primary BOOLEAN DEFAULT FALSE,
       is_active BOOLEAN DEFAULT TRUE
   );
   CREATE INDEX idx_contact_entity ON entity_contact(entity_type, entity_id);
   ```

7. ADDRESS PATTERN
   Multiple addresses with types:
   ```sql
   CREATE TABLE address (
       address_id SERIAL PRIMARY KEY,
       entity_type VARCHAR(30) NOT NULL,
       entity_id INTEGER NOT NULL,
       address_type VARCHAR(30), -- home, work, billing, mailing
       street_line_1 VARCHAR(255),
       street_line_2 VARCHAR(255),
       city VARCHAR(100),
       state VARCHAR(50),
       zip_code VARCHAR(20),
       country VARCHAR(100) DEFAULT 'USA',
       is_primary BOOLEAN DEFAULT FALSE,
       effective_date DATE,
       end_date DATE
   );
   ```
""",
            domain="healthcare",
            resource_type="Pattern",
            chunk_type=ChunkType.PATTERN,
            tags=["pattern", "audit", "temporal", "design"],
            trust_level=1.0
        ))
        
        return chunks
    
    def _get_constraint_rules(self) -> List[RAGChunk]:
        """Get healthcare-specific constraint rules"""
        chunks = []
        
        chunks.append(RAGChunk(
            id=generate_chunk_id("constraint-rules", "Constraint", "healthcare"),
            content="""
HEALTHCARE DATABASE CONSTRAINTS AND VALIDATION RULES
===================================================

1. PATIENT IDENTIFICATION CONSTRAINTS:
   ```sql
   -- MRN must be unique within facility
   ALTER TABLE patient ADD CONSTRAINT uk_patient_mrn 
       UNIQUE (facility_id, medical_record_number);
   
   -- SSN format validation
   ALTER TABLE patient ADD CONSTRAINT ck_patient_ssn 
       CHECK (ssn IS NULL OR ssn ~ '^[0-9]{3}-[0-9]{2}-[0-9]{4}$');
   
   -- Date of birth cannot be in future
   ALTER TABLE patient ADD CONSTRAINT ck_patient_dob 
       CHECK (date_of_birth <= CURRENT_DATE);
   ```

2. PROVIDER CONSTRAINTS:
   ```sql
   -- NPI format validation (10 digits)
   ALTER TABLE provider ADD CONSTRAINT ck_provider_npi 
       CHECK (npi ~ '^[0-9]{10}$');
   
   -- DEA number format (2 letters + 7 characters)
   ALTER TABLE provider ADD CONSTRAINT ck_provider_dea 
       CHECK (dea_number IS NULL OR dea_number ~ '^[A-Z]{2}[0-9A-Z]{7}$');
   ```

3. ENCOUNTER CONSTRAINTS:
   ```sql
   -- Discharge must be after admission
   ALTER TABLE encounter ADD CONSTRAINT ck_encounter_dates 
       CHECK (discharge_date IS NULL OR discharge_date >= admission_date);
   
   -- Valid encounter status
   ALTER TABLE encounter ADD CONSTRAINT ck_encounter_status 
       CHECK (encounter_status IN ('planned', 'arrived', 'in-progress', 
                                   'on-hold', 'completed', 'cancelled'));
   
   -- Valid encounter type
   ALTER TABLE encounter ADD CONSTRAINT ck_encounter_type 
       CHECK (encounter_type IN ('inpatient', 'outpatient', 'emergency', 
                                 'observation', 'telehealth'));
   ```

4. VITAL SIGN CONSTRAINTS:
   ```sql
   -- Realistic vital sign ranges
   ALTER TABLE vital_sign ADD CONSTRAINT ck_bp_systolic 
       CHECK (blood_pressure_systolic IS NULL OR 
              blood_pressure_systolic BETWEEN 40 AND 300);
   
   ALTER TABLE vital_sign ADD CONSTRAINT ck_bp_diastolic 
       CHECK (blood_pressure_diastolic IS NULL OR 
              blood_pressure_diastolic BETWEEN 20 AND 200);
   
   ALTER TABLE vital_sign ADD CONSTRAINT ck_heart_rate 
       CHECK (heart_rate IS NULL OR heart_rate BETWEEN 20 AND 300);
   
   ALTER TABLE vital_sign ADD CONSTRAINT ck_temperature 
       CHECK (temperature IS NULL OR temperature BETWEEN 85.0 AND 115.0);
   
   ALTER TABLE vital_sign ADD CONSTRAINT ck_oxygen_sat 
       CHECK (oxygen_saturation IS NULL OR 
              oxygen_saturation BETWEEN 0 AND 100);
   ```

5. MEDICATION CONSTRAINTS:
   ```sql
   -- Refills cannot be negative
   ALTER TABLE prescription ADD CONSTRAINT ck_refills 
       CHECK (refills_allowed >= 0 AND refills_remaining >= 0);
   
   -- End date must be after start date
   ALTER TABLE prescription ADD CONSTRAINT ck_prescription_dates 
       CHECK (end_date IS NULL OR end_date >= start_date);
   
   -- Controlled substance constraints
   ALTER TABLE prescription ADD CONSTRAINT ck_controlled 
       CHECK (NOT (is_controlled = TRUE AND refills_allowed > 5));
   ```

6. APPOINTMENT CONSTRAINTS:
   ```sql
   -- Appointment must be in the future when created (optional)
   -- Duration must be positive
   ALTER TABLE appointment ADD CONSTRAINT ck_duration 
       CHECK (duration_minutes > 0);
   
   -- Valid appointment status
   ALTER TABLE appointment ADD CONSTRAINT ck_appointment_status 
       CHECK (appointment_status IN ('scheduled', 'confirmed', 'checked-in', 
                                     'in-progress', 'completed', 'cancelled', 
                                     'no-show', 'rescheduled'));
   ```

7. INSURANCE/FINANCIAL CONSTRAINTS:
   ```sql
   -- Coverage dates
   ALTER TABLE patient_coverage ADD CONSTRAINT ck_coverage_dates 
       CHECK (coverage_end_date IS NULL OR 
              coverage_end_date >= coverage_start_date);
   
   -- Positive amounts
   ALTER TABLE charge ADD CONSTRAINT ck_charge_amount 
       CHECK (charge_amount >= 0);
   ```

8. REFERENTIAL INTEGRITY:
   ```sql
   -- Use RESTRICT to prevent orphan records
   ALTER TABLE encounter ADD CONSTRAINT fk_encounter_patient 
       FOREIGN KEY (patient_id) REFERENCES patient(id) 
       ON DELETE RESTRICT ON UPDATE CASCADE;
   ```
""",
            domain="healthcare",
            resource_type="Constraint",
            chunk_type=ChunkType.CONSTRAINT,
            tags=["constraint", "validation", "check", "rule"],
            trust_level=1.0
        ))
        
        return chunks
    
    # Additional helper methods
    
    def get_datatype_mapping(self, attribute_name: str) -> str:
        """Get PostgreSQL type for a healthcare attribute"""
        attribute_lower = attribute_name.lower().replace(" ", "_")
        return HEALTHCARE_POSTGRES_TYPE_MAP.get(
            attribute_lower, 
            "VARCHAR(255)"  # Default
        )
    
    def get_cardinality_constraint(self, cardinality: str) -> Dict[str, Any]:
        """Get SQL constraint info for a cardinality"""
        return HEALTHCARE_CARDINALITY_MAP.get(
            cardinality,
            {"nullable": True, "constraint": None}
        )
    
    def get_lookup_values(self, field_name: str) -> List[str]:
        """Get lookup values for a field"""
        return HEALTHCARE_LOOKUP_TABLES.get(field_name, [])
