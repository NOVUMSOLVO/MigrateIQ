#!/usr/bin/env python3
"""
Simple development server for MigrateIQ dashboard
Provides mock API endpoints for testing the frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Mock data
MOCK_PROJECTS = [
    {
        "id": 1,
        "name": "Customer Data Migration",
        "source_system": "MySQL",
        "target_system": "PostgreSQL",
        "status": "COMPLETED",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-20T15:45:00Z"
    },
    {
        "id": 2,
        "name": "Legacy System Modernization",
        "source_system": "Oracle",
        "target_system": "MongoDB",
        "status": "IN_PROGRESS",
        "created_at": "2024-02-01T09:00:00Z",
        "updated_at": "2024-02-10T14:30:00Z"
    },
    {
        "id": 3,
        "name": "E-commerce Platform Migration",
        "source_system": "SQL Server",
        "target_system": "AWS RDS",
        "status": "PLANNING",
        "created_at": "2024-02-15T11:15:00Z",
        "updated_at": "2024-02-16T16:20:00Z"
    },
    {
        "id": 4,
        "name": "Analytics Data Warehouse",
        "source_system": "Snowflake",
        "target_system": "BigQuery",
        "status": "DRAFT",
        "created_at": "2024-02-20T08:45:00Z",
        "updated_at": "2024-02-20T08:45:00Z"
    }
]

MOCK_DATA_SOURCES = [
    {
        "id": 1,
        "name": "Production MySQL",
        "source_type": "mysql",
        "connection_string": "mysql://prod-db:3306/main",
        "entities": [
            {"name": "users", "record_count": 15000},
            {"name": "orders", "record_count": 45000},
            {"name": "products", "record_count": 2500}
        ],
        "created_at": "2024-01-10T12:00:00Z"
    },
    {
        "id": 2,
        "name": "Legacy Oracle System",
        "source_type": "oracle",
        "connection_string": "oracle://legacy-db:1521/ORCL",
        "entities": [
            {"name": "customers", "record_count": 8500},
            {"name": "transactions", "record_count": 125000}
        ],
        "created_at": "2024-01-12T14:30:00Z"
    },
    {
        "id": 3,
        "name": "Analytics PostgreSQL",
        "source_type": "postgresql",
        "connection_string": "postgresql://analytics-db:5432/analytics",
        "entities": [
            {"name": "events", "record_count": 500000},
            {"name": "sessions", "record_count": 75000},
            {"name": "metrics", "record_count": 25000}
        ],
        "created_at": "2024-02-01T10:15:00Z"
    }
]

@app.route('/')
def root():
    return jsonify({
        "service": "MigrateIQ Development Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/health/",
            "/api/orchestrator/projects/",
            "/api/analyzer/data-sources/"
        ]
    })

@app.route('/api/health/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "MigrateIQ",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "cache": "connected"
    })

@app.route('/api/orchestrator/projects/', methods=['GET'])
def get_projects():
    return jsonify(MOCK_PROJECTS)

@app.route('/api/orchestrator/projects/<int:project_id>/', methods=['GET'])
def get_project(project_id):
    project = next((p for p in MOCK_PROJECTS if p['id'] == project_id), None)
    if project:
        return jsonify(project)
    return jsonify({"error": "Project not found"}), 404

@app.route('/api/orchestrator/projects/', methods=['POST'])
def create_project():
    data = request.get_json()
    new_project = {
        "id": len(MOCK_PROJECTS) + 1,
        "name": data.get('name', ''),
        "description": data.get('description', ''),
        "source_system": data.get('source_system', ''),
        "target_system": data.get('target_system', ''),
        "status": "DRAFT",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    MOCK_PROJECTS.append(new_project)
    return jsonify(new_project), 201

@app.route('/api/orchestrator/projects/<int:project_id>/start/', methods=['POST'])
def start_migration(project_id):
    project = next((p for p in MOCK_PROJECTS if p['id'] == project_id), None)
    if project:
        project['status'] = 'IN_PROGRESS'
        project['updated_at'] = datetime.now().isoformat()
        return jsonify({"message": "Migration started successfully", "project": project})
    return jsonify({"error": "Project not found"}), 404

@app.route('/api/analyzer/data-sources/', methods=['GET'])
def get_data_sources():
    return jsonify(MOCK_DATA_SOURCES)

@app.route('/api/analyzer/data-sources/', methods=['POST'])
def create_data_source():
    data = request.get_json()
    new_source = {
        "id": len(MOCK_DATA_SOURCES) + 1,
        "name": data.get('name', ''),
        "source_type": data.get('source_type', 'csv'),
        "connection_string": data.get('connection_string', ''),
        "entities": [],
        "created_at": datetime.now().isoformat()
    }
    MOCK_DATA_SOURCES.append(new_source)
    return jsonify(new_source), 201

@app.route('/api/analyzer/data-sources/<int:source_id>/', methods=['GET'])
def get_data_source(source_id):
    source = next((s for s in MOCK_DATA_SOURCES if s['id'] == source_id), None)
    if source:
        return jsonify(source)
    return jsonify({"error": "Data source not found"}), 404

@app.route('/api/analyzer/data-sources/<int:source_id>/analyze/', methods=['POST'])
def analyze_data_source(source_id):
    source = next((s for s in MOCK_DATA_SOURCES if s['id'] == source_id), None)
    if source:
        # Simulate analysis by adding some mock entities
        source['entities'] = [
            {"name": "table_1", "record_count": random.randint(1000, 50000)},
            {"name": "table_2", "record_count": random.randint(500, 25000)}
        ]
        return jsonify({"message": "Analysis completed successfully", "entities_found": len(source['entities'])})
    return jsonify({"error": "Data source not found"}), 404

@app.route('/api/metrics/', methods=['GET'])
def get_metrics():
    return jsonify({
        "total_projects": len(MOCK_PROJECTS),
        "total_data_sources": len(MOCK_DATA_SOURCES),
        "completed_projects": len([p for p in MOCK_PROJECTS if p['status'] == 'COMPLETED']),
        "in_progress_projects": len([p for p in MOCK_PROJECTS if p['status'] == 'IN_PROGRESS']),
        "total_entities": sum(len(ds.get('entities', [])) for ds in MOCK_DATA_SOURCES),
        "success_rate": 95.5,
        "avg_migration_time": "2.5 hours"
    })

@app.route('/api/analytics/dashboard/', methods=['GET'])
def get_analytics_dashboard():
    return jsonify({
        "metrics": {
            "total_projects": len(MOCK_PROJECTS),
            "total_data_sources": len(MOCK_DATA_SOURCES),
            "completed_projects": len([p for p in MOCK_PROJECTS if p['status'] == 'COMPLETED']),
            "in_progress_projects": len([p for p in MOCK_PROJECTS if p['status'] == 'IN_PROGRESS']),
            "total_entities": sum(len(ds.get('entities', [])) for ds in MOCK_DATA_SOURCES),
            "success_rate": 95.5,
            "avg_migration_time": "2.5 hours"
        },
        "charts": {
            "project_status": [
                {"status": "COMPLETED", "count": len([p for p in MOCK_PROJECTS if p['status'] == 'COMPLETED'])},
                {"status": "IN_PROGRESS", "count": len([p for p in MOCK_PROJECTS if p['status'] == 'IN_PROGRESS'])},
                {"status": "PLANNING", "count": len([p for p in MOCK_PROJECTS if p['status'] == 'PLANNING'])},
                {"status": "DRAFT", "count": len([p for p in MOCK_PROJECTS if p['status'] == 'DRAFT'])}
            ],
            "data_source_types": [
                {"type": "mysql", "count": len([ds for ds in MOCK_DATA_SOURCES if ds['source_type'] == 'mysql'])},
                {"type": "oracle", "count": len([ds for ds in MOCK_DATA_SOURCES if ds['source_type'] == 'oracle'])},
                {"type": "postgresql", "count": len([ds for ds in MOCK_DATA_SOURCES if ds['source_type'] == 'postgresql'])}
            ]
        },
        "recent_activity": [
            {"action": "Project created", "project": "Customer Data Migration", "timestamp": "2024-02-20T10:30:00Z"},
            {"action": "Migration completed", "project": "Legacy System Modernization", "timestamp": "2024-02-19T15:45:00Z"},
            {"action": "Data source analyzed", "source": "Analytics PostgreSQL", "timestamp": "2024-02-18T14:20:00Z"}
        ]
    })

@app.route('/api/monitoring/system-health/', methods=['GET'])
def system_health():
    return jsonify({
        "status": "healthy",
        "checks": {
            "database": {"status": "ok", "message": "Database connection successful"},
            "cache": {"status": "ok", "message": "Cache connection successful"},
            "storage": {"status": "ok", "message": "Storage accessible"},
            "cpu": {"status": "ok", "message": "CPU usage normal", "details": {"percent": random.randint(20, 60)}},
            "memory": {"status": "ok", "message": "Memory usage normal", "details": {"percent": random.randint(40, 70)}}
        },
        "metrics": {
            "cpu_usage": random.randint(20, 60),
            "memory_usage": random.randint(40, 70),
            "disk_usage": random.randint(30, 50),
            "active_connections": random.randint(10, 50)
        },
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting MigrateIQ Development Server...")
    print("📊 Dashboard API endpoints available at http://localhost:8000")
    print("🔗 Frontend should connect to http://localhost:8000/api")
    print("💡 Use Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=8000, debug=True)
