#!/usr/bin/env python3
"""
NHS Compliance Demo Server

A simple HTTP server to demonstrate NHS compliance features without Django dependencies.
"""

import json
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import os

# Load mock data
def load_mock_data():
    try:
        with open('nhs_mock_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

class NHSComplianceHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for NHS compliance demo endpoints."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # NHS Compliance Dashboard
        if path == '/api/nhs-compliance/dashboard/':
            self.handle_dashboard()

        # NHS Compliance Status
        elif path == '/api/nhs-compliance/status/':
            self.handle_status()

        # DSPT Assessment
        elif path == '/api/nhs-compliance/dspt/':
            self.handle_dspt()

        # Audit Trails
        elif path == '/api/nhs-compliance/audit/':
            self.handle_audit()

        # Safety Incidents
        elif path == '/api/nhs-compliance/incidents/':
            self.handle_incidents()

        # Compliance Checklist
        elif path == '/api/nhs-compliance/checklists/':
            self.handle_checklists()

        # Health Check
        elif path == '/health/':
            self.handle_health()

        # Root endpoint
        elif path == '/' or path == '/api/':
            self.handle_root()

        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # Healthcare Data Validation
        if path == '/api/nhs-compliance/validate/':
            self.handle_validation()

        # Patient Data Encryption
        elif path == '/api/nhs-compliance/encrypt/':
            self.handle_encryption()

        else:
            self.send_error(404, "Endpoint not found")

    def handle_dashboard(self):
        """Handle dashboard request."""
        mock_data = load_mock_data()
        if not mock_data:
            self.send_json_response({"error": "Mock data not available"}, 500)
            return

        dashboard_data = mock_data['dashboard_data']
        self.send_json_response(dashboard_data)

    def handle_status(self):
        """Handle status request."""
        mock_data = load_mock_data()
        if not mock_data:
            self.send_json_response({"error": "Mock data not available"}, 500)
            return

        status_data = {
            "status": "NHS_COMPLIANT",
            "compliance_grade": mock_data['compliance_score']['grade'],
            "compliance_percentage": mock_data['compliance_score']['percentage'],
            "dspt_status": mock_data['organization']['dspt_status'],
            "last_updated": datetime.now().isoformat(),
            "features": {
                "nhs_number_validation": True,
                "hl7_validation": True,
                "fhir_validation": True,
                "dicom_validation": True,
                "aes_256_encryption": True,
                "audit_logging": True,
                "patient_safety_monitoring": True,
                "dspt_compliance": True
            }
        }
        self.send_json_response(status_data)

    def handle_dspt(self):
        """Handle DSPT assessment request."""
        mock_data = load_mock_data()
        if not mock_data:
            self.send_json_response({"error": "Mock data not available"}, 500)
            return

        dspt_data = mock_data['dspt_assessment']
        self.send_json_response(dspt_data)

    def handle_audit(self):
        """Handle audit trails request."""
        mock_data = load_mock_data()
        if not mock_data:
            self.send_json_response({"error": "Mock data not available"}, 500)
            return

        audit_data = {
            "audit_trails": mock_data['audit_trails'],
            "summary": mock_data['dashboard_data']['audit_summary']
        }
        self.send_json_response(audit_data)

    def handle_incidents(self):
        """Handle safety incidents request."""
        mock_data = load_mock_data()
        if not mock_data:
            self.send_json_response({"error": "Mock data not available"}, 500)
            return

        incidents_data = {
            "safety_incidents": mock_data['safety_incidents'],
            "summary": mock_data['dashboard_data']['safety_incidents']
        }
        self.send_json_response(incidents_data)

    def handle_checklists(self):
        """Handle compliance checklist request."""
        mock_data = load_mock_data()
        if not mock_data:
            self.send_json_response({"error": "Mock data not available"}, 500)
            return

        checklist_data = mock_data['compliance_checklist']
        self.send_json_response(checklist_data)

    def handle_validation(self):
        """Handle healthcare data validation request."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            request_data = json.loads(post_data.decode('utf-8'))
            data_type = request_data.get('data_type', 'NHS')

            # Simulate validation
            validation_result = {
                "valid": True,
                "data_type": data_type,
                "validation_timestamp": datetime.now().isoformat(),
                "errors": [],
                "message": f"{data_type} data validation successful"
            }

            if data_type == "NHS":
                validation_result["nhs_number_valid"] = True
                validation_result["checksum_verified"] = True
            elif data_type == "HL7":
                validation_result["message_structure_valid"] = True
                validation_result["segments_validated"] = True
            elif data_type == "FHIR":
                validation_result["resource_valid"] = True
                validation_result["nhs_extensions_valid"] = True

            self.send_json_response(validation_result)

        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)

    def handle_encryption(self):
        """Handle patient data encryption request."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            request_data = json.loads(post_data.decode('utf-8'))
            nhs_number = request_data.get('nhs_number')

            # Simulate encryption
            encryption_result = {
                "encrypted": True,
                "algorithm": "AES-256-GCM",
                "nhs_number_entropy": True,
                "encryption_timestamp": datetime.now().isoformat(),
                "encrypted_data": {
                    "ciphertext": "encrypted_patient_data_base64...",
                    "iv": "random_iv_base64...",
                    "tag": "auth_tag_base64...",
                    "nhs_number_hash": "sha256_hash_of_nhs_number..."
                }
            }

            self.send_json_response(encryption_result)

        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)

    def handle_health(self):
        """Handle health check request."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "nhs_compliance": "enabled",
            "services": {
                "encryption": "operational",
                "validation": "operational",
                "audit_logging": "operational",
                "dspt_monitoring": "operational"
            }
        }
        self.send_json_response(health_data)

    def handle_root(self):
        """Handle root request."""
        root_data = {
            "service": "MigrateIQ NHS Compliance API",
            "version": "1.0.0",
            "status": "NHS_COMPLIANT",
            "compliance_grade": "A",
            "endpoints": {
                "dashboard": "/api/nhs-compliance/dashboard/",
                "status": "/api/nhs-compliance/status/",
                "dspt": "/api/nhs-compliance/dspt/",
                "audit": "/api/nhs-compliance/audit/",
                "incidents": "/api/nhs-compliance/incidents/",
                "checklists": "/api/nhs-compliance/checklists/",
                "validate": "/api/nhs-compliance/validate/ (POST)",
                "encrypt": "/api/nhs-compliance/encrypt/ (POST)",
                "health": "/health/"
            },
            "features": [
                "NHS Number validation with Modulus 11 checksum",
                "HL7/FHIR/DICOM healthcare data validation",
                "AES-256 patient data encryption",
                "CQC-compliant audit trails",
                "Patient safety incident tracking",
                "DSPT compliance monitoring"
            ],
            "documentation": "See NHS_COMPLIANCE_COMPLETE.md for full details"
        }
        self.send_json_response(root_data)

    def send_json_response(self, data, status_code=200):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        json_data = json.dumps(data, indent=2, default=str)
        self.wfile.write(json_data.encode('utf-8'))

    def log_message(self, format, *args):
        """Custom log message format."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] NHS Compliance API: {format % args}")

def main():
    """Start the NHS compliance demo server."""
    PORT = 8001

    print("="*60)
    print("🏥 MigrateIQ NHS Compliance Demo Server")
    print("="*60)
    print(f"Starting server on http://localhost:{PORT}")
    print("\n📡 Available Endpoints:")
    print(f"  • Dashboard: http://localhost:{PORT}/api/nhs-compliance/dashboard/")
    print(f"  • Status: http://localhost:{PORT}/api/nhs-compliance/status/")
    print(f"  • DSPT: http://localhost:{PORT}/api/nhs-compliance/dspt/")
    print(f"  • Audit: http://localhost:{PORT}/api/nhs-compliance/audit/")
    print(f"  • Incidents: http://localhost:{PORT}/api/nhs-compliance/incidents/")
    print(f"  • Health: http://localhost:{PORT}/health/")
    print(f"  • Root: http://localhost:{PORT}/")

    # Check if mock data exists
    if os.path.exists('nhs_mock_data.json'):
        print("\n✅ Mock data loaded successfully")
        mock_data = load_mock_data()
        if mock_data:
            print(f"   Organization: {mock_data['organization']['organization_name']}")
            print(f"   Compliance Grade: {mock_data['compliance_score']['grade']}")
    else:
        print("\n⚠️  Mock data not found. Run setup_nhs_mock_data.py first.")

    print(f"\n🚀 Server starting... Press Ctrl+C to stop")
    print("="*60)

    try:
        with socketserver.TCPServer(("", PORT), NHSComplianceHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("🏥 NHS Compliance Demo Server shutdown complete")

if __name__ == "__main__":
    main()
