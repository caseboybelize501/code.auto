"""
JARVIS Batch Job Runner
Runs 10 diverse projects and tracks code production metrics
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any

# JARVIS API endpoint
API_BASE = "http://localhost:8001"

# 10 ADVANCED difficulty project requirements - testing full JARVIS vision
PROJECTS = [
    {
        "id": 1,
        "name": "Distributed Stream Processing Engine",
        "requirements": "Build a real-time stream processing platform with Kafka integration, windowed aggregations, complex event processing, stateful computations, exactly-once semantics, and horizontal scaling. Support custom operators, backpressure handling, and fault tolerance with checkpointing."
    },
    {
        "id": 2,
        "name": "Multi-Tenant SaaS Platform",
        "requirements": "Create a SaaS backend with tenant isolation, subscription billing, feature flags, usage metering, custom domains, white-labeling, RBAC with tenant-scoped permissions, audit logging, and data export compliance. Support Stripe integration and usage-based pricing."
    },
    {
        "id": 3,
        "name": "AI Model Inference Gateway",
        "requirements": "Build an ML inference serving platform with model versioning, A/B testing, canary deployments, request batching, GPU scheduling, auto-scaling, latency monitoring, and cost optimization. Support multiple model formats (ONNX, PyTorch, TensorFlow) and rate limiting per API key."
    },
    {
        "id": 4,
        "name": "Blockchain Bridge Protocol",
        "requirements": "Create a cross-chain bridge service with multi-signature validation, atomic swaps, liquidity pools, transaction proof verification, slippage protection, and bridge analytics. Support Ethereum, Polygon, and BSC with secure validator consensus and fraud proofs."
    },
    {
        "id": 5,
        "name": "Real-Time Collaborative Editor Backend",
        "requirements": "Build an operational transformation backend for collaborative document editing with conflict resolution, presence indicators, version history, comments/annotations, access control, and offline sync. Support WebSocket connections, CRDT algorithms, and sub-100ms sync latency."
    },
    {
        "id": 6,
        "name": "Video Transcoding Pipeline",
        "requirements": "Create a video processing service with upload streaming, multi-format transcoding (H.264, H.265, VP9), adaptive bitrate generation, thumbnail extraction, watermarking, CDN integration, and progress webhooks. Support S3 storage, queue-based processing, and cost-optimized encoding."
    },
    {
        "id": 7,
        "name": "Identity Provider (IdP) Service",
        "requirements": "Build an OAuth2/OpenID Connect identity provider with SSO, SAML federation, MFA (TOTP, WebAuthn, SMS), passwordless authentication, session management, consent screens, and SCIM provisioning. Support enterprise SSO, JWT/OIDC tokens, and compliance (SOC2, GDPR)."
    },
    {
        "id": 8,
        "name": "Geospatial Analytics Engine",
        "requirements": "Create a location intelligence platform with GeoJSON processing, spatial queries (intersects, contains, within), heat map generation, route optimization, geofencing alerts, and real-time tracking. Support PostGIS, tile generation, and clustering algorithms for millions of points."
    },
    {
        "id": 9,
        "name": "Quantum-Inspired Optimization API",
        "requirements": "Build an optimization service implementing quantum-inspired algorithms (QAOA, VQE simulation, simulated annealing) for combinatorial problems. Support portfolio optimization, logistics routing, scheduling problems, with visualization of energy landscapes and convergence metrics."
    },
    {
        "id": 10,
        "name": "Zero-Knowledge Proof Service",
        "requirements": "Create a ZK-proof generation and verification service with zk-SNARK support, circuit compilation, proof aggregation, and on-chain verification. Support identity proofs, range proofs, membership proofs with privacy-preserving credential verification."
    }
]


class BatchJobRunner:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    def check_health(self) -> bool:
        """Check if JARVIS API is healthy"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def submit_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a single project to JARVIS"""
        print(f"\n{'='*60}")
        print(f"Project {project['id']}: {project['name']}")
        print(f"{'='*60}")

        start = time.time()

        try:
            response = requests.post(
                f"{self.api_base}/api/project/start",
                json={"requirements": project["requirements"]},
                timeout=600  # 10 minute timeout per project
            )

            elapsed = time.time() - start

            if response.status_code == 200:
                result = response.json()
                result["project_name"] = project["name"]
                result["project_id_input"] = project["id"]
                result["elapsed_seconds"] = elapsed
                result["status_code"] = response.status_code
                return result
            else:
                return {
                    "project_name": project["name"],
                    "project_id_input": project["id"],
                    "status": "failed",
                    "status_code": response.status_code,
                    "error": response.text,
                    "elapsed_seconds": elapsed
                }

        except requests.exceptions.Timeout:
            return {
                "project_name": project["name"],
                "project_id_input": project["id"],
                "status": "timeout",
                "error": "Request timed out after 5 minutes",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "project_name": project["name"],
                "project_id_input": project["id"],
                "status": "error",
                "error": str(e),
                "elapsed_seconds": elapsed
            }

    def run_all_projects(self):
        """Run all 10 projects sequentially"""
        print("\n" + "="*60)
        print("JARVIS BATCH JOB RUNNER")
        print("="*60)
        print(f"Starting {len(PROJECTS)} projects...")
        print(f"API: {self.api_base}")

        self.start_time = datetime.now()

        # Check health first
        if not self.check_health():
            print("ERROR: JARVIS API is not healthy. Aborting.")
            return

        print("JARVIS API is healthy. Starting batch jobs...\n")

        # Run each project
        for project in PROJECTS:
            result = self.submit_project(project)
            self.results.append(result)

            # Print summary
            status = result.get("status", "unknown")
            files_count = len(result.get("files", []))
            print(f"  Status: {status}")
            print(f"  Files generated: {files_count}")
            print(f"  Time: {result['elapsed_seconds']:.1f}s")

            # Small delay between projects
            time.sleep(2)

        self.end_time = datetime.now()

    def generate_report(self) -> Dict[str, Any]:
        """Generate production metrics report"""
        total_projects = len(self.results)
        completed = sum(1 for r in self.results if r.get("status") in ["completed", "completed_with_issues"])
        failed = sum(1 for r in self.results if r.get("status") == "failed")
        timeout = sum(1 for r in self.results if r.get("status") == "timeout")
        errors = sum(1 for r in self.results if r.get("status") == "error")

        total_files = sum(len(r.get("files", [])) for r in self.results)
        total_tests = sum(
            r.get("test_results", {}).get("unit", {}).get("test_count", 0)
            for r in self.results
        )
        passed_tests = sum(
            r.get("test_results", {}).get("unit", {}).get("passed", False)
            for r in self.results
        )

        total_time = sum(r.get("elapsed_seconds", 0) for r in self.results)

        # Architecture distribution
        architectures = {}
        languages = {}
        frameworks = {}
        databases = {}

        for r in self.results:
            plan = r.get("plan", {})
            arch = plan.get("architecture", "unknown")
            lang = plan.get("language", "unknown")
            fw = plan.get("framework", "unknown")
            db = plan.get("database", "unknown")

            architectures[arch] = architectures.get(arch, 0) + 1
            languages[lang] = languages.get(lang, 0) + 1
            frameworks[fw] = frameworks.get(fw, 0) + 1
            databases[db] = databases.get(db, 0) + 1

        report = {
            "summary": {
                "total_projects": total_projects,
                "completed": completed,
                "failed": failed,
                "timeout": timeout,
                "errors": errors,
                "success_rate": f"{completed/total_projects*100:.1f}%" if total_projects > 0 else "0%"
            },
            "code_production": {
                "total_files_generated": total_files,
                "avg_files_per_project": f"{total_files/total_projects:.1f}" if total_projects > 0 else "0",
                "total_tests_created": total_tests,
                "tests_passed": passed_tests
            },
            "performance": {
                "total_time_seconds": f"{total_time:.1f}",
                "avg_time_per_project": f"{total_time/total_projects:.1f}s" if total_projects > 0 else "0s",
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None
            },
            "architecture_distribution": architectures,
            "language_distribution": languages,
            "framework_distribution": frameworks,
            "database_distribution": databases,
            "project_details": self.results
        }

        return report

    def print_report(self):
        """Print formatted report"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("CODE PRODUCTION REPORT")
        print("="*60)

        print("\n[SUMMARY]")
        print("-"*40)
        for key, value in report["summary"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\n[CODE PRODUCTION]")
        print("-"*40)
        for key, value in report["code_production"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

        print("\n[PERFORMANCE]")
        print("-"*40)
        for key, value in report["performance"].items():
            if key not in ["start_time", "end_time"]:
                print(f"  {key.replace('_', ' ').title()}: {value}")
        print(f"  Start: {report['performance']['start_time']}")
        print(f"  End: {report['performance']['end_time']}")

        print("\n[ARCHITECTURE DISTRIBUTION]")
        print("-"*40)
        for arch, count in report["architecture_distribution"].items():
            print(f"  {arch}: {count}")

        print("\n[LANGUAGE DISTRIBUTION]")
        print("-"*40)
        for lang, count in report["language_distribution"].items():
            print(f"  {lang}: {count}")

        print("\n[FRAMEWORK DISTRIBUTION]")
        print("-"*40)
        for fw, count in report["framework_distribution"].items():
            print(f"  {fw}: {count}")

        print("\n[DATABASE DISTRIBUTION]")
        print("-"*40)
        for db, count in report["database_distribution"].items():
            print(f"  {db}: {count}")

        print("\n" + "="*60)

        # Save detailed report
        with open("batch_job_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n[OK] Detailed report saved to: batch_job_report.json")


def main(num_projects: int = 10):
    """Run batch jobs with configurable number of projects"""
    global PROJECTS
    if num_projects < len(PROJECTS):
        PROJECTS = PROJECTS[:num_projects]
    
    runner = BatchJobRunner(API_BASE)
    runner.run_all_projects()
    runner.print_report()


if __name__ == "__main__":
    import sys
    # Default to 10 projects, or accept command line arg
    # Can also specify start:end (e.g., 4:10 for projects 4-10)
    arg = sys.argv[1] if len(sys.argv) > 1 else "10"
    if ":" in arg:
        start, end = map(int, arg.split(":"))
        PROJECTS = PROJECTS[start-1:end]
        n = len(PROJECTS)
    else:
        n = int(arg)
    main(n)
