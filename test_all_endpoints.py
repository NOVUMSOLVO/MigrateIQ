#!/usr/bin/env python3
"""
Comprehensive API Testing Script for MigrateIQ
Tests all available endpoints and validates responses.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def test_endpoint(method, endpoint, expected_status=200, data=None):
    """Test a single endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data)
        else:
            return False, f"Unsupported method: {method}"
        
        success = response.status_code == expected_status
        
        if success:
            try:
                json_data = response.json()
                return True, json_data
            except:
                return True, response.text
        else:
            return False, f"Status: {response.status_code}, Expected: {expected_status}"
            
    except Exception as e:
        return False, str(e)

def print_test_result(endpoint, method, success, result):
    """Print formatted test result."""
    status_color = Colors.GREEN if success else Colors.RED
    status_text = "✅ PASS" if success else "❌ FAIL"
    
    print(f"{status_color}{status_text}{Colors.END} {Colors.BOLD}{method} {endpoint}{Colors.END}")
    
    if success and isinstance(result, dict):
        # Print key information from successful responses
        if 'service' in result:
            print(f"  📊 Service: {result['service']} v{result.get('version', 'unknown')}")
        if 'modules' in result:
            print(f"  🔧 Modules: {len(result['modules'])} active")
        if 'projects' in result:
            print(f"  📁 Projects: {len(result['projects'])} found")
        if 'datasources' in result:
            print(f"  🔗 Data Sources: {len(result['datasources'])} configured")
        if 'dashboard' in result:
            dashboard = result['dashboard']
            print(f"  📈 Success Rate: {dashboard.get('success_rate', 'N/A')}%")
        if 'metrics' in result:
            metrics = result['metrics']
            print(f"  💻 CPU: {metrics.get('cpu_usage', 'N/A')}%, Memory: {metrics.get('memory_usage', 'N/A')}%")
    elif not success:
        print(f"  ❌ Error: {result}")
    
    print()

def main():
    """Run comprehensive API tests."""
    print(f"{Colors.BLUE}{Colors.BOLD}🚀 MigrateIQ API Testing Suite{Colors.END}")
    print(f"{Colors.BLUE}Testing all endpoints at {BASE_URL}{Colors.END}")
    print(f"{Colors.BLUE}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print("=" * 60)
    
    # Define all test cases
    test_cases = [
        # Basic endpoints
        ("GET", "/", 200),
        ("GET", "/health/", 200),
        ("GET", "/api/", 200),
        
        # Module status endpoints
        ("GET", "/api/modules/", 200),
        ("GET", "/api/analyzer/status/", 200),
        ("GET", "/api/orchestrator/status/", 200),
        ("GET", "/api/validation/status/", 200),
        ("GET", "/api/transformation/status/", 200),
        ("GET", "/api/mapping/status/", 200),
        ("GET", "/api/ml/status/", 200),
        
        # Data endpoints
        ("GET", "/api/projects/", 200),
        ("GET", "/api/datasources/", 200),
        
        # Authentication endpoints
        ("POST", "/api/auth/login/", 200),
        ("POST", "/api/auth/logout/", 200),
        ("GET", "/api/auth/profile/", 200),
        
        # Analytics endpoints
        ("GET", "/api/analytics/dashboard/", 200),
        ("GET", "/api/system/metrics/", 200),
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for method, endpoint, expected_status in test_cases:
        success, result = test_endpoint(method, endpoint, expected_status)
        print_test_result(endpoint, method, success, result)
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Print summary
    print("=" * 60)
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}📊 Test Summary:{Colors.END}")
    print(f"  Total Tests: {total}")
    print(f"  {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"  {Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"  {Colors.YELLOW}📈 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if success_rate >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT! MigrateIQ API is performing exceptionally well!{Colors.END}")
    elif success_rate >= 75:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}👍 GOOD! MigrateIQ API is working well with minor issues.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  NEEDS ATTENTION! Several endpoints require fixes.{Colors.END}")
    
    print(f"\n{Colors.BLUE}Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
