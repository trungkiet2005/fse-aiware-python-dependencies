# 🐛 Debug Cell for Kaggle Notebook

## Thêm cell này vào Kaggle để debug chi tiết

```python
# ============================================================================
# DEBUG CELL - Add this BEFORE your test loop
# ============================================================================

import glob

# Get ONE snippet to test
test_snippet = glob.glob('/kaggle/working/fse-aiware-python-dependencies/hard-gists/*/snippet.py')[0]

print(f"Testing: {test_snippet}")
print("="*80)

# Read code
with open(test_snippet, 'r') as f:
    code = f.read()

print(f"Code length: {len(code)} chars")
print(f"First 200 chars:\n{code[:200]}")
print("="*80)

# ============================================================================
# Step 1: Test Analyzer
# ============================================================================
print("\n[1] Testing Analyzer...")
try:
    analysis = analyzer.process({
        'code': code,
        'snippet_path': test_snippet
    })
    
    print(f"✅ Analyzer SUCCESS")
    print(f"   Imports: {analysis.get('imports', [])}")
    print(f"   Python version: {analysis.get('python_version_min')}")
    print(f"   Code lines: {analysis.get('code_lines')}")
    
    if not analysis.get('imports'):
        print("   ⚠️ WARNING: No imports detected!")
        
except Exception as e:
    print(f"❌ Analyzer FAILED: {e}")
    import traceback
    traceback.print_exc()
    raise

# ============================================================================
# Step 2: Test Resolver
# ============================================================================
print("\n[2] Testing Resolver...")
try:
    resolution = resolver.process({
        'analysis': analysis,
        'code': code,
        'context': {}
    })
    
    candidates = resolution.get('candidates', [])
    print(f"✅ Resolver SUCCESS")
    print(f"   Candidates generated: {len(candidates)}")
    
    if candidates:
        best = candidates[0]
        print(f"   Best candidate:")
        print(f"     - Source: {best.get('source')}")
        print(f"     - Python: {best.get('python_version')}")
        print(f"     - Packages: {len(best.get('packages', {}))} packages")
        print(f"     - Confidence: {best.get('confidence')}")
        
        if best.get('packages'):
            print(f"     - Package list: {list(best.get('packages', {}).keys())}")
        else:
            print(f"     ⚠️ WARNING: No packages in candidate!")
            
        if 'unknown_packages' in best:
            print(f"     - Unknown: {best.get('unknown_packages')}")
    else:
        print("   ❌ ERROR: No candidates generated!")
        
except Exception as e:
    print(f"❌ Resolver FAILED: {e}")
    import traceback
    traceback.print_exc()
    raise

# ============================================================================
# Step 3: Test Validator
# ============================================================================
print("\n[3] Testing Validator...")
try:
    validation = validator.process({
        'candidates': candidates,
        'code': code,
        'quick_mode': True
    })
    
    best_candidate = validation.get('best_candidate')
    print(f"✅ Validator SUCCESS")
    
    if best_candidate:
        print(f"   Best candidate after validation:")
        print(f"     - Packages: {len(best_candidate.get('packages', {}))} packages")
        print(f"     - Validation passed: {best_candidate.get('validation', {}).get('passed')}")
        print(f"     - Validation score: {best_candidate.get('validation', {}).get('score')}")
        print(f"     - Final score: {best_candidate.get('final_score')}")
        print(f"     - Issues: {best_candidate.get('validation', {}).get('issues')}")
        print(f"     - Warnings: {best_candidate.get('validation', {}).get('warnings')}")
    else:
        print("   ❌ ERROR: No best candidate!")
        
except Exception as e:
    print(f"❌ Validator FAILED: {e}")
    import traceback
    traceback.print_exc()
    raise

# ============================================================================
# Step 4: Test Full Coordinator
# ============================================================================
print("\n[4] Testing Full Coordinator...")
try:
    result = coordinator.process({
        'snippet_path': test_snippet,
        'code': code
    })
    
    print(f"Coordinator result:")
    print(f"   Success: {result['success']}")
    print(f"   Execution time: {result['execution_time']:.3f}s")
    print(f"   Iterations: {result.get('iterations_used')}")
    
    solution = result.get('solution')
    if solution:
        print(f"   Solution found:")
        print(f"     - Python: {solution.get('python_version')}")
        print(f"     - Packages: {len(solution.get('packages', {}))} packages")
        print(f"     - Final score: {solution.get('final_score')}")
        print(f"     - Package list: {list(solution.get('packages', {}).keys())}")
        
        # ============================================================================
        # CRITICAL DEBUG: Check success criteria
        # ============================================================================
        print(f"\n   🔍 SUCCESS CRITERIA CHECK:")
        print(f"     - solution is not None: {solution is not None}")
        print(f"     - len(packages) > 0: {len(solution.get('packages', {})) > 0} (count: {len(solution.get('packages', {}))})")
        print(f"     - final_score >= 0.3: {solution.get('final_score', 0) >= 0.3} (score: {solution.get('final_score', 0):.3f})")
        
        expected_success = (
            solution is not None 
            and len(solution.get('packages', {})) > 0
            and solution.get('final_score', 0) >= 0.3
        )
        print(f"     - Expected success: {expected_success}")
        print(f"     - Actual success: {result['success']}")
        
        if expected_success != result['success']:
            print(f"     ❌ MISMATCH! Success criteria not working correctly!")
        else:
            print(f"     ✅ Success criteria working correctly")
    else:
        print(f"   ❌ No solution found")
        print(f"   Error logs: {result.get('error_logs', [])}")
    
    if result['success']:
        print(f"\n✅ OVERALL: Test PASSED!")
    else:
        print(f"\n❌ OVERALL: Test FAILED!")
        print(f"\nDEBUG INFO:")
        print(f"   - Analysis imports: {analysis.get('imports', [])}")
        print(f"   - Candidates generated: {len(candidates)}")
        print(f"   - Best candidate packages: {len(best_candidate.get('packages', {})) if best_candidate else 0}")
        print(f"   - Final score: {best_candidate.get('final_score') if best_candidate else 'N/A'}")
        
except Exception as e:
    print(f"❌ Coordinator FAILED: {e}")
    import traceback
    traceback.print_exc()
    raise

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)
```

## Chạy cell này và gửi output cho tôi!
