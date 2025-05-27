"""
Healthcare Standards Module

Support for healthcare interoperability standards including HL7, FHIR, and DICOM.
"""

__version__ = '1.0.0'

# Supported healthcare standards
SUPPORTED_STANDARDS = {
    'HL7_V2': {
        'version': '2.8',
        'description': 'Health Level Seven Version 2',
        'message_types': ['ADT', 'ORM', 'ORU', 'SIU', 'MDM'],
    },
    'HL7_V3': {
        'version': '3.0',
        'description': 'Health Level Seven Version 3',
        'formats': ['CDA', 'CCD', 'CCR'],
    },
    'FHIR': {
        'version': 'R4',
        'description': 'Fast Healthcare Interoperability Resources',
        'resources': ['Patient', 'Observation', 'Encounter', 'Medication', 'DiagnosticReport'],
    },
    'DICOM': {
        'version': '3.0',
        'description': 'Digital Imaging and Communications in Medicine',
        'modalities': ['CT', 'MR', 'US', 'XR', 'CR', 'DR'],
    },
    'SNOMED_CT': {
        'version': 'UK Edition',
        'description': 'Systematized Nomenclature of Medicine Clinical Terms',
        'domains': ['Clinical findings', 'Procedures', 'Body structures'],
    },
    'ICD_10': {
        'version': 'UK Edition',
        'description': 'International Classification of Diseases',
        'chapters': ['Infectious diseases', 'Neoplasms', 'Mental disorders'],
    },
}

# NHS-specific standards
NHS_STANDARDS = {
    'NHS_NUMBER': {
        'format': r'^\d{10}$',
        'checksum': 'modulus_11',
        'description': 'NHS Number validation',
    },
    'CHI_NUMBER': {
        'format': r'^\d{10}$',
        'checksum': 'modulus_11',
        'description': 'Community Health Index Number (Scotland)',
    },
    'H_C_NUMBER': {
        'format': r'^[A-Z]{2}\d{6}[A-Z]$',
        'description': 'Health and Care Number (Northern Ireland)',
    },
}
