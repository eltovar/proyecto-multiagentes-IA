"""
Unit Tests for InformationAnalyzer
Tests for analyze_completeness and extract_key_information methods
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.leadsales.analyzers import InformationAnalyzer


def test_analyze_completeness_high_quality():
    """Test completeness analysis with high quality message"""
    message = "Busco apartamento para comprar en el poblado de 3 habitaciones con presupuesto de 500 millones"

    result = InformationAnalyzer.analyze_completeness(message)

    assert result == True
    print("   [OK] High quality message correctly identified as complete")


def test_analyze_completeness_low_quality():
    """Test completeness analysis with low quality message"""
    message = "Hola, estoy interesado"

    result = InformationAnalyzer.analyze_completeness(message)

    assert result == False
    print("   [OK] Low quality message correctly identified as incomplete")


def test_analyze_completeness_medium_quality():
    """Test completeness analysis with medium quality message"""
    message = "Necesito casa en el norte"  # Only location + property type = 2 categories

    result = InformationAnalyzer.analyze_completeness(message)

    assert result == True  # Should be True with 2 categories
    print("   [OK] Medium quality message correctly identified as complete")


def test_extract_key_information_apartment():
    """Test key information extraction for apartment"""
    message = "Busco apartamento de 3 habitaciones con 2 baños"

    result = InformationAnalyzer.extract_key_information(message)

    assert result["property_type"] == "apartamento"
    assert "3" in result["numbers_mentioned"]
    assert "2" in result["numbers_mentioned"]
    print("   [OK] Apartment information correctly extracted")


def test_extract_key_information_casa():
    """Test key information extraction for house"""
    message = "Necesito una casa con 4 habitaciones"

    result = InformationAnalyzer.extract_key_information(message)

    assert result["property_type"] == "casa"
    assert "4" in result["numbers_mentioned"]
    print("   [OK] House information correctly extracted")


def test_extract_key_information_comercial():
    """Test key information extraction for commercial property"""
    message = "Estoy buscando un local comercial de 100 metros"

    result = InformationAnalyzer.extract_key_information(message)

    assert result["property_type"] == "local"
    assert "100" in result["numbers_mentioned"]
    print("   [OK] Commercial property information correctly extracted")


def test_extract_key_information_no_property_type():
    """Test key information extraction with no property type"""
    message = "Tengo un presupuesto de 300 millones"

    result = InformationAnalyzer.extract_key_information(message)

    assert "property_type" not in result
    assert "300" in result["numbers_mentioned"]
    print("   [OK] No property type correctly handled")


def test_extract_key_information_no_numbers():
    """Test key information extraction with no numbers"""
    message = "Busco apartamento en el centro"

    result = InformationAnalyzer.extract_key_information(message)

    assert result["property_type"] == "apartamento"
    assert "numbers_mentioned" not in result
    print("   [OK] No numbers correctly handled")


def test_quality_indicators_coverage():
    """Test that all quality indicator categories are working"""

    # Test property_type
    assert InformationAnalyzer.analyze_completeness("apartamento para comprar") == True

    # Test transaction_type + location
    assert InformationAnalyzer.analyze_completeness("vender en poblado") == True

    # Test specs + budget
    assert InformationAnalyzer.analyze_completeness("3 habitaciones, 400 millones") == True

    print("   [OK] All quality indicator categories working correctly")


if __name__ == "__main__":
    print("=" * 70)
    print("UNIT TESTS - INFORMATION ANALYZER")
    print("=" * 70)

    try:
        test_analyze_completeness_high_quality()
        test_analyze_completeness_low_quality()
        test_analyze_completeness_medium_quality()
        test_extract_key_information_apartment()
        test_extract_key_information_casa()
        test_extract_key_information_comercial()
        test_extract_key_information_no_property_type()
        test_extract_key_information_no_numbers()
        test_quality_indicators_coverage()

        print("\n" + "=" * 70)
        print("[OK] ALL INFORMATION ANALYZER TESTS PASSED")
        print("=" * 70)
        print("InformationAnalyzer funcionality validated:")
        print("- analyze_completeness method working correctly")
        print("- extract_key_information method working correctly")
        print("- All quality indicators functioning properly")
        print("- Edge cases handled appropriately")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()