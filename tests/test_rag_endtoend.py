#!/usr/bin/env python3
"""
RAG End-to-End Tests - FASE II Actions 2.1-2.2
Tests the complete RAG workflow with specific knowledge base files
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.rag_system import rag_system

class RAGEndToEndTests:
    """Comprehensive RAG End-to-End test suite"""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_result(self, test_name, status, details):
        """Log test result"""
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        if status == "PASS":
            self.passed += 1
        else:
            self.failed += 1

    def test_initialization(self):
        """Test 0: RAG System Initialization"""
        print("\n[TEST 0] RAG System Initialization")
        try:
            success = rag_system.initialize()
            if success:
                print("   [PASS] RAG system initialized successfully")
                self.log_result("RAG Initialization", "PASS", f"System initialized with documents")
                return True
            else:
                print("   [FAIL] RAG system failed to initialize")
                self.log_result("RAG Initialization", "FAIL", "System initialization failed")
                return False
        except Exception as e:
            print(f"   [FAIL] Exception during initialization: {e}")
            self.log_result("RAG Initialization", "FAIL", f"Exception: {str(e)}")
            return False

    def test_blog_arriendo_incrementos(self):
        """Test 1: blog_arriendo_incrementos_ley.txt knowledge retrieval"""
        print("\n[TEST 1] Blog Arriendo Incrementos Ley Knowledge Retrieval")
        query = "incrementos de arriendo por ley"

        try:
            context = rag_system.get_context_for_query(query)

            if context is None:
                print("   [FAIL] No context returned")
                self.log_result("Blog Arriendo Incrementos", "FAIL", "No context returned")
                return False

            # Check for relevant content
            context_lower = context.lower()
            relevant_keywords = ["arriendo", "incremento", "ley", "alquiler", "aumento"]
            found_keywords = [kw for kw in relevant_keywords if kw in context_lower]

            if len(found_keywords) >= 2:
                print(f"   [PASS] Relevant content found (keywords: {found_keywords})")
                print(f"   Context length: {len(context)} characters")
                self.log_result("Blog Arriendo Incrementos", "PASS",
                              f"Keywords found: {found_keywords}, Context: {len(context)} chars")
                return True
            else:
                print(f"   [FAIL] Insufficient relevant content (keywords: {found_keywords})")
                self.log_result("Blog Arriendo Incrementos", "FAIL",
                              f"Only {len(found_keywords)} relevant keywords found")
                return False

        except Exception as e:
            print(f"   [FAIL] Exception: {e}")
            self.log_result("Blog Arriendo Incrementos", "FAIL", f"Exception: {str(e)}")
            return False

    def test_general_inmobiliaria_services(self):
        """Test 2: General Inmobiliaria Services Knowledge"""
        print("\n[TEST 2] General Inmobiliaria Services Knowledge")
        query = "servicios inmobiliaria proteger"

        try:
            context = rag_system.get_context_for_query(query)

            if context is None:
                print("   [FAIL] No context returned")
                self.log_result("General Services", "FAIL", "No context returned")
                return False

            # Check for service-related content
            context_lower = context.lower()
            service_keywords = ["servicio", "proteger", "inmobiliaria", "asesor", "venta", "arriendo"]
            found_keywords = [kw for kw in service_keywords if kw in context_lower]

            if len(found_keywords) >= 3:
                print(f"   [PASS] Service content found (keywords: {found_keywords})")
                print(f"   Context length: {len(context)} characters")
                self.log_result("General Services", "PASS",
                              f"Keywords found: {found_keywords}, Context: {len(context)} chars")
                return True
            else:
                print(f"   [FAIL] Insufficient service content (keywords: {found_keywords})")
                self.log_result("General Services", "FAIL",
                              f"Only {len(found_keywords)} service keywords found")
                return False

        except Exception as e:
            print(f"   [FAIL] Exception: {e}")
            self.log_result("General Services", "FAIL", f"Exception: {str(e)}")
            return False

    def test_soporte_contabilidad_facturas(self):
        """Test 3: soporte_contabilidad_facturas.txt knowledge retrieval"""
        print("\n[TEST 3] Soporte Contabilidad Facturas Knowledge")
        query = "contabilidad facturas soporte"

        try:
            context = rag_system.get_context_for_query(query)

            if context is None:
                print("   [FAIL] No context returned")
                self.log_result("Contabilidad Facturas", "FAIL", "No context returned")
                return False

            # Check for accounting/billing content
            context_lower = context.lower()
            accounting_keywords = ["contabilidad", "factura", "soporte", "billing", "cuenta", "pago"]
            found_keywords = [kw for kw in accounting_keywords if kw in context_lower]

            if len(found_keywords) >= 2:
                print(f"   [PASS] Accounting content found (keywords: {found_keywords})")
                print(f"   Context length: {len(context)} characters")
                self.log_result("Contabilidad Facturas", "PASS",
                              f"Keywords found: {found_keywords}, Context: {len(context)} chars")
                return True
            else:
                print(f"   [FAIL] Insufficient accounting content (keywords: {found_keywords})")
                self.log_result("Contabilidad Facturas", "FAIL",
                              f"Only {len(found_keywords)} accounting keywords found")
                return False

        except Exception as e:
            print(f"   [FAIL] Exception: {e}")
            self.log_result("Contabilidad Facturas", "FAIL", f"Exception: {str(e)}")
            return False

    def test_performance_metrics(self):
        """Test 4: RAG Performance and Metrics"""
        print("\n[TEST 4] RAG Performance and Metrics")

        try:
            # Test response times and quality
            test_queries = [
                "inmobiliaria",
                "arriendo apartamento",
                "venta casa",
                "asesor especializado"
            ]

            successful_queries = 0
            total_chars = 0

            for query in test_queries:
                context = rag_system.get_context_for_query(query)
                if context and len(context) > 50:
                    successful_queries += 1
                    total_chars += len(context)

            success_rate = (successful_queries / len(test_queries)) * 100
            avg_context_length = total_chars / successful_queries if successful_queries > 0 else 0

            if success_rate >= 75 and avg_context_length >= 100:
                print(f"   [PASS] Performance metrics adequate")
                print(f"   Success rate: {success_rate:.1f}%")
                print(f"   Average context length: {avg_context_length:.0f} chars")
                self.log_result("Performance Metrics", "PASS",
                              f"Success: {success_rate:.1f}%, Avg length: {avg_context_length:.0f}")
                return True
            else:
                print(f"   [FAIL] Performance below threshold")
                print(f"   Success rate: {success_rate:.1f}% (need >=75%)")
                print(f"   Average context length: {avg_context_length:.0f} chars (need >=100)")
                self.log_result("Performance Metrics", "FAIL",
                              f"Success: {success_rate:.1f}%, Avg length: {avg_context_length:.0f}")
                return False

        except Exception as e:
            print(f"   [FAIL] Exception: {e}")
            self.log_result("Performance Metrics", "FAIL", f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Execute all RAG End-to-End tests"""
        print("=" * 70)
        print("RAG END-TO-END TESTS - FASE II (Actions 2.1-2.2)")
        print("=" * 70)

        # Initialize system first
        if not self.test_initialization():
            print("\n[CRITICAL] RAG system failed to initialize. Aborting tests.")
            return False

        # Run all tests
        self.test_blog_arriendo_incrementos()
        self.test_general_inmobiliaria_services()
        self.test_soporte_contabilidad_facturas()
        self.test_performance_metrics()

        # Generate final report
        self.generate_report()

        return self.failed == 0

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE RAG TEST REPORT")
        print("=" * 70)

        print(f"\nTEST SUMMARY:")
        print(f"   Total Tests: {self.passed + self.failed}")
        print(f"   Passed: {self.passed}")
        print(f"   Failed: {self.failed}")
        print(f"   Success Rate: {(self.passed/(self.passed + self.failed)*100):.1f}%")

        print(f"\nDETAILED RESULTS:")
        for result in self.results:
            status_symbol = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
            print(f"   {status_symbol} {result['test']}: {result['status']}")
            print(f"      Details: {result['details']}")

        if self.failed == 0:
            print(f"\n[SUCCESS] ALL RAG TESTS PASSED - FASE II Actions 2.1-2.2 COMPLETED")
        else:
            print(f"\n[WARNING] {self.failed} TEST(S) FAILED - REVIEW REQUIRED")

        print("=" * 70)

def main():
    """Main function to run RAG End-to-End tests"""
    test_suite = RAGEndToEndTests()
    success = test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())