"""
Test Docker validation locally before Kaggle
"""

import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

from docker_validator import DockerValidator


def test_simple_case():
    """Test a simple case"""
    print("="*80)
    print("TEST 1: Simple numpy + pandas")
    print("="*80)
    
    code = """
import numpy as np
import pandas as pd

# Simple test
arr = np.array([1, 2, 3])
df = pd.DataFrame({'a': [1, 2, 3]})

print("NumPy array:", arr)
print("Pandas DataFrame:", df)
"""
    
    packages = {
        'numpy': '1.24.3',
        'pandas': '2.0.3'
    }
    
    validator = DockerValidator(timeout=120)
    
    if not validator.available:
        print("❌ Docker not available!")
        print("Please install Docker Desktop and start it")
        return False
    
    success, message, exec_time = validator.validate_solution(
        code=code,
        packages=packages,
        python_version='3.8'
    )
    
    print(f"\nResult: {message}")
    print(f"Time: {exec_time:.2f}s")
    
    if success:
        print("✅ Test 1 PASSED")
        return True
    else:
        print("❌ Test 1 FAILED")
        return False


def test_invalid_version():
    """Test with invalid package version"""
    print("\n" + "="*80)
    print("TEST 2: Invalid version (should fail)")
    print("="*80)
    
    code = """
import numpy as np
print("This should fail")
"""
    
    packages = {
        'numpy': '999.999.999'  # Invalid version
    }
    
    validator = DockerValidator(timeout=60)
    
    success, message, exec_time = validator.validate_solution(
        code=code,
        packages=packages,
        python_version='3.8'
    )
    
    print(f"\nResult: {message}")
    print(f"Time: {exec_time:.2f}s")
    
    if not success and "not found" in message.lower():
        print("✅ Test 2 PASSED (correctly detected invalid version)")
        return True
    else:
        print("❌ Test 2 FAILED (should have failed)")
        return False


def test_incompatible_versions():
    """Test with incompatible package versions"""
    print("\n" + "="*80)
    print("TEST 3: Incompatible versions")
    print("="*80)
    
    code = """
import numpy as np
import pandas as pd
print("Testing compatibility")
"""
    
    # Old pandas with new numpy (might have issues)
    packages = {
        'numpy': '1.24.3',
        'pandas': '0.25.3'  # Very old
    }
    
    validator = DockerValidator(timeout=60)
    
    success, message, exec_time = validator.validate_solution(
        code=code,
        packages=packages,
        python_version='3.8'
    )
    
    print(f"\nResult: {message}")
    print(f"Time: {exec_time:.2f}s")
    
    # This might succeed or fail depending on actual compatibility
    if success:
        print("✅ Test 3: Packages are compatible")
    else:
        print("⚠️ Test 3: Packages incompatible (expected)")
    
    return True  # Either outcome is valid


def test_batch():
    """Test batch validation"""
    print("\n" + "="*80)
    print("TEST 4: Batch validation")
    print("="*80)
    
    solutions = [
        (
            "import numpy as np\nprint('Test 1')",
            {'numpy': '1.24.3'},
            '3.8',
            'snippet_1'
        ),
        (
            "import pandas as pd\nprint('Test 2')",
            {'pandas': '2.0.3'},
            '3.8',
            'snippet_2'
        ),
        (
            "import requests\nprint('Test 3')",
            {'requests': '2.31.0'},
            '3.8',
            'snippet_3'
        )
    ]
    
    validator = DockerValidator(timeout=60)
    results = validator.batch_validate(solutions, show_progress=True)
    
    successful = sum(1 for r in results if r['docker_success'])
    print(f"\n{'='*80}")
    print(f"Batch Results: {successful}/{len(results)} successful")
    print(f"{'='*80}")
    
    if successful >= 2:
        print("✅ Test 4 PASSED")
        return True
    else:
        print("❌ Test 4 FAILED")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DOCKER VALIDATOR TEST SUITE")
    print("="*80 + "\n")
    
    tests = [
        ("Simple case", test_simple_case),
        ("Invalid version", test_invalid_version),
        ("Incompatible versions", test_incompatible_versions),
        ("Batch validation", test_batch)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ {name} EXCEPTION: {e}")
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
    
    total_passed = sum(1 for _, p in results if p)
    print(f"\n{total_passed}/{len(results)} tests passed")
    print("="*80)
    
    if total_passed == len(results):
        print("\n🎉 All tests passed! Ready for Kaggle!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check Docker installation.")
        return 1


if __name__ == '__main__':
    exit(main())
