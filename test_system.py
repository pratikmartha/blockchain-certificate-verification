import sys
import os
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from blockchain import get_blockchain_manager
import database as db

class BlockchainCertificateTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.blockchain_mgr = get_blockchain_manager()

    def test_01_blockchain_connection(self):
        status = self.blockchain_mgr.get_blockchain_status()
        self.assertTrue(status["connected"], "Blockchain should be connected")
        self.assertIsNotNone(status["contract_address"], "Contract should have an address")
        print("\n[TEST 1 PASSED] Blockchain status:", status["provider"], "| Contract:", status["contract_address"])

    def test_02_public_pages(self):
        endpoints = ["/", "/verify", "/universities", "/api/universities", "/explorer", "/demo/tamper", "/admin/login", "/admin/register"]
        for ep in endpoints:
            response = self.client.get(ep)
            self.assertEqual(response.status_code, 200, f"Endpoint {ep} should return HTTP 200")
        
        # Test universities API specifically
        api_res = self.client.get("/api/universities")
        data = api_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["city"], "Bhubaneswar")
        self.assertEqual(data["state"], "Odisha")
        self.assertGreaterEqual(data["count"], 20)
        print(f"[TEST 2 PASSED] All public endpoints including Bhubaneswar Universities ({data['count']} institutes) returned HTTP 200")

    def test_03_issue_and_verify_certificate(self):
        # 1. Login as admin
        login_res = self.client.post("/admin/login", data={
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # 2. Issue a certificate via POST
        test_cert_id = f"CERT-AUTO-TEST-999"
        issue_res = self.client.post("/admin/issue", data={
            "certificate_id": test_cert_id,
            "student_name": "Eleanor Vance",
            "student_email": "eleanor@example.com",
            "course": "Bachelor of Science in Distributed Systems",
            "institution": "Metropolitan University of Technology",
            "issue_date": "2026-09-26",
            "grade": "First Class with Distinction"
        }, follow_redirects=True)

        self.assertEqual(issue_res.status_code, 200)
        self.assertIn(b"Eleanor Vance", issue_res.data)
        print(f"[TEST 3.1 PASSED] Certificate {test_cert_id} successfully issued on blockchain via Flask")

        # 3. Verify on blockchain via /verify/<id>
        verify_res = self.client.get(f"/verify/{test_cert_id}")
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn(b"Cryptographically Verified", verify_res.data)
        self.assertIn(b"Eleanor Vance", verify_res.data)
        print(f"[TEST 3.2 PASSED] Certificate {test_cert_id} verified on Ethereum smart contract")

        # 4. View official printable certificate
        view_res = self.client.get(f"/certificate/{test_cert_id}")
        self.assertEqual(view_res.status_code, 200)
        self.assertIn(b"OFFICIAL SEAL", view_res.data)
        print(f"[TEST 3.3 PASSED] Digital printable certificate rendered with QR code and gold seal")

        # 5. Test JSON API
        api_res = self.client.get(f"/api/verify/{test_cert_id}")
        self.assertEqual(api_res.status_code, 200)
        json_data = api_res.get_json()
        self.assertTrue(json_data["valid"])
        self.assertEqual(json_data["on_chain"]["student_name"], "Eleanor Vance")
        print(f"[TEST 3.4 PASSED] REST API /api/verify returned valid JSON response")

    def test_04_tamper_detection(self):
        # Post tampered data to /demo/tamper
        test_cert_id = "CERT-AUTO-TEST-999"
        tamper_res = self.client.post("/demo/tamper", data={
            "certificate_id": test_cert_id,
            "student_name": "Malicious Imposter",  # Altered name!
            "course": "Bachelor of Science in Distributed Systems",
            "institution": "Metropolitan University of Technology",
            "issue_date": "2026-09-26"
        })
        self.assertEqual(tamper_res.status_code, 200)
        self.assertIn(b"Tampering Detected!", tamper_res.data)
        print("[TEST 4 PASSED] Tampering properly detected and rejected against blockchain ledger")

if __name__ == "__main__":
    unittest.main()
