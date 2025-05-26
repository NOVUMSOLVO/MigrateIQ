#!/usr/bin/env python3
"""
Frontend proxy server for MigrateIQ
Serves the built React app and proxies API calls to the backend
"""

from flask import Flask, send_from_directory, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuration
BACKEND_URL = 'http://localhost:8000'
FRONTEND_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'build')

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_api(path):
    """Proxy all API calls to the backend server"""
    try:
        # Forward the request to the backend
        backend_url = f"{BACKEND_URL}/api/{path}"

        # Get request data
        data = None
        headers = {}
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.is_json:
                data = request.get_json()
                headers['Content-Type'] = 'application/json'

        # Make the request to backend
        if data:
            response = requests.request(
                method=request.method,
                url=backend_url,
                json=data,
                params=request.args,
                headers=headers,
                timeout=30
            )
        else:
            response = requests.request(
                method=request.method,
                url=backend_url,
                params=request.args,
                timeout=30
            )

        # Return the response
        return jsonify(response.json()), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend server is not running"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out"}), 504
    except Exception as e:
        return jsonify({"error": f"Proxy error: {str(e)}"}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the React app"""
    if path != "" and os.path.exists(os.path.join(FRONTEND_BUILD_DIR, path)):
        return send_from_directory(FRONTEND_BUILD_DIR, path)
    else:
        return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')

if __name__ == '__main__':
    print("🚀 Starting MigrateIQ Frontend Proxy Server...")
    print(f"📁 Serving frontend from: {FRONTEND_BUILD_DIR}")
    print(f"🔗 Proxying API calls to: {BACKEND_URL}")
    print("🌐 Frontend available at http://localhost:3000")
    print("💡 Use Ctrl+C to stop the server")

    if not os.path.exists(FRONTEND_BUILD_DIR):
        print(f"❌ Error: Frontend build directory not found at {FRONTEND_BUILD_DIR}")
        print("Please build the frontend first with 'npm run build'")
        exit(1)

    app.run(host='0.0.0.0', port=3000, debug=True)
