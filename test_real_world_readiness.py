#!/usr/bin/env python3
"""
MigrateIQ Real-World Readiness Testing Suite

This comprehensive testing suite validates MigrateIQ's readiness for production deployment
across all critical dimensions: functionality, performance, security, and compliance.
"""

import os
import sys
import time
import json
import subprocess
import requests
import psutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResult:
    """Test result container."""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now()

class RealWorldReadinessTest:
    """Comprehensive real-world readiness testing suite."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        
    def log_test_start(self, test_name: str):
        """Log test start."""
        print(f"\n{Colors.BLUE}🧪 Testing: {test_name}{Colors.END}")
        logger.info(f"Starting test: {test_name}")
        
    def log_test_result(self, result: TestResult):
        """Log test result."""
        status = f"{Colors.GREEN}✅ PASS" if result.passed else f"{Colors.RED}❌ FAIL"
        print(f"{status}{Colors.END} {result.name} ({result.duration:.2f}s)")
        if result.message:
            print(f"   {Colors.YELLOW}💬 {result.message}{Colors.END}")
        logger.info(f"Test result: {result.name} - {'PASS' if result.passed else 'FAIL'} - {result.message}")
        self.results.append(result)
        
    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """Run shell command and return success status and output."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, str(e)
            
    def check_service_health(self, url: str, service_name: str) -> TestResult:
        """Check if a service is healthy."""
        start_time = time.time()
        try:
            response = requests.get(url, timeout=10)
            duration = time.time() - start_time
            if response.status_code == 200:
                return TestResult(f"{service_name} Health Check", True, 
                                f"Service responding (HTTP {response.status_code})", duration)
            else:
                return TestResult(f"{service_name} Health Check", False, 
                                f"HTTP {response.status_code}", duration)
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(f"{service_name} Health Check", False, str(e), duration)
            
    def test_environment_setup(self):
        """Test environment setup and dependencies."""
        self.log_test_start("Environment Setup")
        
        # Check Python version
        python_version = sys.version_info
        result = TestResult(
            "Python Version Check",
            python_version >= (3, 8),
            f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        self.log_test_result(result)
        
        # Check required files
        required_files = [
            "backend/manage.py",
            "backend/requirements.txt",
            "frontend/package.json",
            "docker-compose.yml",
            ".env.sample"
        ]
        
        for file_path in required_files:
            exists = Path(file_path).exists()
            result = TestResult(f"Required File: {file_path}", exists, 
                              "Found" if exists else "Missing")
            self.log_test_result(result)
            
        # Check environment variables
        env_vars = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
        for var in env_vars:
            value = os.getenv(var)
            result = TestResult(f"Environment Variable: {var}", 
                              value is not None, 
                              "Set" if value else "Not set")
            self.log_test_result(result)
            
    def test_database_connectivity(self):
        """Test database connectivity and operations."""
        self.log_test_start("Database Connectivity")
        
        # Test Django database connection
        os.chdir("backend")
        success, output = self.run_command("python manage.py check --database default")
        result = TestResult("Django Database Check", success, output.strip())
        self.log_test_result(result)
        
        # Test migrations
        success, output = self.run_command("python manage.py showmigrations")
        result = TestResult("Database Migrations Check", success, 
                          "Migrations status checked" if success else output.strip())
        self.log_test_result(result)
        
        os.chdir("..")
        
    def test_backend_api(self):
        """Test backend API functionality."""
        self.log_test_start("Backend API")
        
        # Test API health
        result = self.check_service_health(f"{self.base_url}/api/", "Backend API")
        self.log_test_result(result)
        
        # Test API documentation
        result = self.check_service_health(f"{self.base_url}/api/docs/", "API Documentation")
        self.log_test_result(result)
        
        # Test authentication endpoints
        auth_endpoints = [
            "/api/auth/login/",
            "/api/auth/logout/",
            "/api/auth/profile/"
        ]
        
        for endpoint in auth_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # For auth endpoints, we expect 401 or 405, not 500
                success = response.status_code in [200, 401, 405]
                result = TestResult(f"Auth Endpoint: {endpoint}", success, 
                                  f"HTTP {response.status_code}")
                self.log_test_result(result)
            except Exception as e:
                result = TestResult(f"Auth Endpoint: {endpoint}", False, str(e))
                self.log_test_result(result)
                
    def test_frontend_application(self):
        """Test frontend application."""
        self.log_test_start("Frontend Application")
        
        # Check if frontend is running
        result = self.check_service_health(self.frontend_url, "Frontend Application")
        self.log_test_result(result)
        
        # Check package.json dependencies
        try:
            with open("frontend/package.json", "r") as f:
                package_data = json.load(f)
                
            required_deps = ["react", "react-dom", "@mui/material", "axios"]
            for dep in required_deps:
                has_dep = dep in package_data.get("dependencies", {})
                result = TestResult(f"Frontend Dependency: {dep}", has_dep,
                                  "Found" if has_dep else "Missing")
                self.log_test_result(result)
        except Exception as e:
            result = TestResult("Frontend Package Check", False, str(e))
            self.log_test_result(result)
            
    def test_docker_infrastructure(self):
        """Test Docker infrastructure."""
        self.log_test_start("Docker Infrastructure")
        
        # Check Docker availability
        success, output = self.run_command("docker --version")
        result = TestResult("Docker Availability", success, output.strip())
        self.log_test_result(result)
        
        # Check Docker Compose
        success, output = self.run_command("docker-compose --version")
        result = TestResult("Docker Compose Availability", success, output.strip())
        self.log_test_result(result)
        
        # Check if containers are running
        success, output = self.run_command("docker-compose ps")
        result = TestResult("Docker Containers Status", success, 
                          "Containers checked" if success else output.strip())
        self.log_test_result(result)
        
    def test_security_basics(self):
        """Test basic security configurations."""
        self.log_test_start("Security Basics")
        
        # Check for debug mode in production
        try:
            response = requests.get(f"{self.base_url}/api/", timeout=5)
            debug_headers = any("debug" in str(v).lower() for v in response.headers.values())
            result = TestResult("Debug Mode Check", not debug_headers,
                              "No debug info in headers" if not debug_headers else "Debug info found")
            self.log_test_result(result)
        except Exception as e:
            result = TestResult("Debug Mode Check", False, str(e))
            self.log_test_result(result)
            
        # Check HTTPS redirect (if applicable)
        # Check CORS headers
        try:
            response = requests.options(f"{self.base_url}/api/", timeout=5)
            has_cors = "Access-Control-Allow-Origin" in response.headers
            result = TestResult("CORS Headers", has_cors,
                              "CORS configured" if has_cors else "CORS not found")
            self.log_test_result(result)
        except Exception as e:
            result = TestResult("CORS Headers", False, str(e))
            self.log_test_result(result)
            
    def test_performance_basics(self):
        """Test basic performance metrics."""
        self.log_test_start("Performance Basics")
        
        # Test API response time
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/", timeout=10)
            response_time = time.time() - start_time
            fast_enough = response_time < 2.0  # 2 second threshold
            result = TestResult("API Response Time", fast_enough,
                              f"{response_time:.2f}s ({'Good' if fast_enough else 'Slow'})")
            self.log_test_result(result)
        except Exception as e:
            result = TestResult("API Response Time", False, str(e))
            self.log_test_result(result)
            
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        result = TestResult("CPU Usage", cpu_percent < 80,
                          f"{cpu_percent:.1f}% ({'Normal' if cpu_percent < 80 else 'High'})")
        self.log_test_result(result)
        
        result = TestResult("Memory Usage", memory_percent < 80,
                          f"{memory_percent:.1f}% ({'Normal' if memory_percent < 80 else 'High'})")
        self.log_test_result(result)
        
    def test_nhs_compliance_basics(self):
        """Test NHS compliance features."""
        self.log_test_start("NHS Compliance Basics")
        
        # Check NHS compliance endpoints
        nhs_endpoints = [
            "/api/nhs-compliance/",
            "/api/nhs-compliance/audit/",
            "/api/nhs-compliance/patient-safety/"
        ]
        
        for endpoint in nhs_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # Expect 401 (unauthorized) or 200, not 404 or 500
                success = response.status_code in [200, 401, 403]
                result = TestResult(f"NHS Endpoint: {endpoint}", success,
                                  f"HTTP {response.status_code}")
                self.log_test_result(result)
            except Exception as e:
                result = TestResult(f"NHS Endpoint: {endpoint}", False, str(e))
                self.log_test_result(result)
                
    def generate_report(self):
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        total_duration = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}🏥 MIGRATEIQ REAL-WORLD READINESS TEST REPORT{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        
        print(f"\n{Colors.CYAN}📊 SUMMARY{Colors.END}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.END}")
        print(f"Failed: {Colors.RED}{failed_tests}{Colors.END}")
        print(f"Success Rate: {Colors.GREEN if success_rate >= 80 else Colors.RED}{success_rate:.1f}%{Colors.END}")
        print(f"Total Duration: {total_duration:.2f}s")
        
        if failed_tests > 0:
            print(f"\n{Colors.RED}❌ FAILED TESTS{Colors.END}")
            for result in self.results:
                if not result.passed:
                    print(f"  • {result.name}: {result.message}")
                    
        print(f"\n{Colors.CYAN}🎯 READINESS ASSESSMENT{Colors.END}")
        if success_rate >= 90:
            print(f"{Colors.GREEN}✅ PRODUCTION READY{Colors.END}")
            print("The application meets high standards for production deployment.")
        elif success_rate >= 70:
            print(f"{Colors.YELLOW}⚠️  NEEDS ATTENTION{Colors.END}")
            print("The application has some issues that should be addressed before production.")
        else:
            print(f"{Colors.RED}❌ NOT READY{Colors.END}")
            print("The application has significant issues that must be resolved.")
            
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_duration": total_duration
            },
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "duration": r.duration,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        with open("test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n{Colors.BLUE}📄 Detailed report saved to: test_report.json{Colors.END}")
        print(f"{Colors.BLUE}📄 Test logs saved to: test_results.log{Colors.END}")
        
    def run_all_tests(self):
        """Run all test suites."""
        print(f"{Colors.BOLD}{Colors.PURPLE}🚀 Starting MigrateIQ Real-World Readiness Testing{Colors.END}")
        print(f"{Colors.PURPLE}Testing comprehensive production readiness...{Colors.END}")
        
        try:
            self.test_environment_setup()
            self.test_database_connectivity()
            self.test_docker_infrastructure()
            self.test_backend_api()
            self.test_frontend_application()
            self.test_security_basics()
            self.test_performance_basics()
            self.test_nhs_compliance_basics()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  Testing interrupted by user{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Testing failed with error: {e}{Colors.END}")
            logger.error(f"Testing failed: {e}")
        finally:
            self.generate_report()

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("MigrateIQ Real-World Readiness Testing Suite")
        print("Usage: python test_real_world_readiness.py")
        print("\nThis script performs comprehensive testing to validate production readiness.")
        return
        
    tester = RealWorldReadinessTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
