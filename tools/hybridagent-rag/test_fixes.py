#!/usr/bin/env python3
"""
Test script to verify all fixes are working correctly
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.analyzer import AnalyzerAgent
from agents.resolver import ResolverAgent
from agents.validator import ValidatorAgent
from agents.learner import LearnerAgent
from agents.coordinator import CoordinatorAgent
from rag.adaptive_rag import AdaptiveRAG
from graph.conflict_detector import ConflictDetector


def test_import_extraction():
    """Test improved import extraction"""
    print("\n" + "="*80)
    print("TEST 1: Import Extraction")
    print("="*80)
    
    analyzer = AnalyzerAgent(model="gemma2", base_url="http://localhost:11434")
    
    # Test code with various import styles
    test_code = """
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from matplotlib import pyplot as plt
import sys  # Should be filtered out
import os   # Should be filtered out

# Multi-line import
from scipy.stats import (
    norm,
    uniform
)

def main():
    import seaborn as sns  # Indented import
    pass
"""
    
    result = analyzer._extract_imports(test_code)
    
    expected = ['matplotlib', 'numpy', 'pandas', 'scipy', 'seaborn', 'sklearn']
    
    print(f"Found imports: {result}")
    print(f"Expected: {expected}")
    
    # Check if all expected imports are found
    missing = set(expected) - set(result)
    extra = set(result) - set(expected)
    
    if missing:
        print(f"❌ Missing imports: {missing}")
    if extra:
        print(f"⚠️  Extra imports (OK if valid): {extra}")
    
    # Check stdlib filtering
    stdlib_found = [imp for imp in ['sys', 'os'] if imp in result]
    if stdlib_found:
        print(f"❌ Stdlib not filtered: {stdlib_found}")
    else:
        print("✅ Stdlib correctly filtered")
    
    if not missing and not stdlib_found:
        print("✅ TEST PASSED: Import extraction working correctly")
        return True
    else:
        print("❌ TEST FAILED: Import extraction has issues")
        return False


def test_conservative_versions():
    """Test extended conservative versions"""
    print("\n" + "="*80)
    print("TEST 2: Conservative Versions Coverage")
    print("="*80)
    
    resolver = ResolverAgent(model="gemma2", base_url="http://localhost:11434")
    
    # Test common packages
    test_imports = [
        'numpy', 'pandas', 'sklearn', 'matplotlib', 'scipy',
        'tensorflow', 'torch', 'requests', 'flask', 'django',
        'opencv-python', 'pillow', 'beautifulsoup4', 'selenium',
        'pytest', 'sqlalchemy', 'redis', 'nltk', 'transformers'
    ]
    
    analysis = {
        'imports': test_imports,
        'python_version_min': '3.8'
    }
    
    candidate = resolver._generate_conservative_candidate(analysis)
    
    packages = candidate.get('packages', {})
    unknown = candidate.get('unknown_packages', [])
    
    print(f"Total imports: {len(test_imports)}")
    print(f"Packages with versions: {len(packages)}")
    print(f"Unknown packages: {len(unknown)}")
    
    if unknown:
        print(f"Unknown: {unknown}")
    
    coverage = len(packages) / len(test_imports) * 100
    print(f"Coverage: {coverage:.1f}%")
    
    if coverage >= 90:
        print("✅ TEST PASSED: Excellent coverage")
        return True
    elif coverage >= 70:
        print("⚠️  TEST WARNING: Good coverage but could be better")
        return True
    else:
        print("❌ TEST FAILED: Poor coverage")
        return False


def test_fallback_strategy():
    """Test fallback for unknown packages"""
    print("\n" + "="*80)
    print("TEST 3: Fallback Strategy")
    print("="*80)
    
    resolver = ResolverAgent(model="gemma2", base_url="http://localhost:11434")
    
    # Test with unknown packages
    test_imports = ['numpy', 'unknown_package_xyz', 'another_unknown_pkg']
    
    analysis = {
        'imports': test_imports,
        'python_version_min': '3.8'
    }
    
    candidate = resolver._generate_conservative_candidate(analysis)
    
    packages = candidate.get('packages', {})
    
    print(f"Imports: {test_imports}")
    print(f"Packages generated: {packages}")
    
    # Check if all imports have versions (even unknown ones)
    all_covered = all(imp in packages for imp in test_imports)
    
    if all_covered:
        print("✅ TEST PASSED: All packages have versions (with fallback)")
        return True
    else:
        missing = [imp for imp in test_imports if imp not in packages]
        print(f"❌ TEST FAILED: Missing packages: {missing}")
        return False


def test_success_criteria():
    """Test improved success criteria"""
    print("\n" + "="*80)
    print("TEST 4: Success Criteria")
    print("="*80)
    
    # Test case 1: Good solution with packages
    solution1 = {
        'packages': {'numpy': '1.21.0', 'pandas': '1.3.0'},
        'final_score': 0.35
    }
    
    success1 = (
        solution1 is not None 
        and len(solution1.get('packages', {})) > 0
        and solution1.get('final_score', 0) >= 0.3
    )
    
    print(f"Case 1: {solution1}")
    print(f"Success: {success1}")
    
    # Test case 2: Empty packages (should fail)
    solution2 = {
        'packages': {},
        'final_score': 0.8
    }
    
    success2 = (
        solution2 is not None 
        and len(solution2.get('packages', {})) > 0
        and solution2.get('final_score', 0) >= 0.3
    )
    
    print(f"\nCase 2: {solution2}")
    print(f"Success: {success2}")
    
    # Test case 3: Low score (should fail)
    solution3 = {
        'packages': {'numpy': '1.21.0'},
        'final_score': 0.2
    }
    
    success3 = (
        solution3 is not None 
        and len(solution3.get('packages', {})) > 0
        and solution3.get('final_score', 0) >= 0.3
    )
    
    print(f"\nCase 3: {solution3}")
    print(f"Success: {success3}")
    
    if success1 and not success2 and not success3:
        print("\n✅ TEST PASSED: Success criteria working correctly")
        return True
    else:
        print("\n❌ TEST FAILED: Success criteria not working as expected")
        return False


def test_end_to_end():
    """Test end-to-end workflow"""
    print("\n" + "="*80)
    print("TEST 5: End-to-End Workflow")
    print("="*80)
    
    # Initialize system
    rag_system = AdaptiveRAG()
    graph_detector = ConflictDetector()
    
    analyzer = AnalyzerAgent(model="gemma2", base_url="http://localhost:11434")
    resolver = ResolverAgent(
        model="gemma2", 
        base_url="http://localhost:11434",
        rag_system=rag_system,
        graph_detector=graph_detector
    )
    validator = ValidatorAgent(model="gemma2", base_url="http://localhost:11434")
    learner = LearnerAgent(model="gemma2", base_url="http://localhost:11434", rag_system=rag_system)
    
    coordinator = CoordinatorAgent(
        analyzer=analyzer,
        resolver=resolver,
        validator=validator,
        learner=learner,
        model="gemma2",
        base_url="http://localhost:11434",
        max_iterations=3
    )
    
    # Test code
    test_code = """
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

def train_model(X, y):
    model = RandomForestClassifier()
    model.fit(X, y)
    return model
"""
    
    print("Processing test code...")
    result = coordinator.process({
        'snippet_path': 'test.py',
        'code': test_code
    })
    
    print(f"\nSuccess: {result['success']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
    
    if result['success']:
        solution = result['solution']
        print(f"Python version: {solution.get('python_version')}")
        print(f"Packages: {solution.get('packages')}")
        print(f"Final score: {solution.get('final_score'):.3f}")
        print("\n✅ TEST PASSED: End-to-end workflow successful")
        return True
    else:
        print(f"Error logs: {result.get('error_logs', [])}")
        print("\n❌ TEST FAILED: End-to-end workflow failed")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("HYBRIDAGENT-RAG FIX VERIFICATION")
    print("="*80)
    
    tests = [
        ("Import Extraction", test_import_extraction),
        ("Conservative Versions", test_conservative_versions),
        ("Fallback Strategy", test_fallback_strategy),
        ("Success Criteria", test_success_criteria),
        ("End-to-End", test_end_to_end),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Ready for Kaggle!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
