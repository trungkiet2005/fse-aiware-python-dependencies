"""
Validator Agent: Test and validate candidate solutions
"""

import subprocess
import tempfile
import os
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent


class ValidatorAgent(BaseAgent):
    """
    Validates candidate solutions by testing package compatibility
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="Validator", **kwargs)
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate candidate solutions
        
        Args:
            input_data: {
                'candidates': List[Dict] - Candidate solutions from Resolver
                'code': str - Original code
                'quick_mode': bool - Skip actual installation (faster)
            }
            
        Returns:
            {
                'validated_candidates': List[Dict] - Candidates with validation results
                'best_candidate': Dict - Highest scoring candidate
                'validation_summary': str - Summary of validation
            }
        """
        candidates = input_data.get('candidates', [])
        code = input_data.get('code', '')
        quick_mode = input_data.get('quick_mode', True)  # Default to quick mode
        
        self.log(f"Validating {len(candidates)} candidates")
        
        validated = []
        for i, candidate in enumerate(candidates):
            self.log(f"Validating candidate {i+1}/{len(candidates)}: {candidate.get('source')}")
            
            validation_result = self._validate_candidate(
                candidate=candidate,
                code=code,
                quick_mode=quick_mode
            )
            
            candidate['validation'] = validation_result
            candidate['final_score'] = self._calculate_final_score(candidate, validation_result)
            validated.append(candidate)
        
        # Sort by final score
        validated.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        best_candidate = validated[0] if validated else None
        
        summary = self._generate_summary(validated)
        
        return {
            'validated_candidates': validated,
            'best_candidate': best_candidate,
            'validation_summary': summary
        }
    
    def _validate_candidate(
        self,
        candidate: Dict,
        code: str,
        quick_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a single candidate solution
        """
        python_version = candidate.get('python_version', '3.8')
        packages = candidate.get('packages', {})
        
        if quick_mode:
            # Quick validation without actual installation
            return self._quick_validate(python_version, packages, code)
        else:
            # Full validation with pip install (slower, more accurate)
            return self._full_validate(python_version, packages, code)
    
    def _quick_validate(
        self,
        python_version: str,
        packages: Dict[str, str],
        code: str
    ) -> Dict[str, Any]:
        """
        Quick validation using heuristics (no actual installation)
        """
        issues = []
        warnings = []
        score = 1.0
        
        # Check Python version compatibility
        try:
            py_major, py_minor = map(int, python_version.split('.')[:2])
            
            # Check if version is reasonable
            if py_major < 3 or (py_major == 3 and py_minor < 6):
                issues.append(f"Python {python_version} is too old")
                score *= 0.5
            elif py_major == 3 and py_minor > 12:
                warnings.append(f"Python {python_version} is very new, may have compatibility issues")
                score *= 0.9
                
        except Exception as e:
            issues.append(f"Invalid Python version format: {python_version}")
            score *= 0.3
        
        # Check if we have any packages at all
        if not packages:
            issues.append("No packages specified")
            score = 0.1
        
        # Check package versions
        for package, version in packages.items():
            # Check version format
            if not version or version == 'latest':
                warnings.append(f"{package}: version not specified")
                score *= 0.95
                continue
            
            # Validate version format (should be x.y.z)
            try:
                parts = version.split('.')
                if len(parts) < 2:
                    warnings.append(f"{package}: unusual version format '{version}'")
                    score *= 0.95
            except:
                warnings.append(f"{package}: invalid version format '{version}'")
                score *= 0.9
            
            # Check for known incompatibilities
            incompatibility = self._check_known_incompatibilities(
                package, version, python_version, packages
            )
            if incompatibility:
                issues.append(incompatibility)
                score *= 0.7
        
        # Check circular dependencies
        if self._has_circular_dependencies(packages):
            warnings.append("Potential circular dependencies detected")
            score *= 0.9
        
        return {
            'method': 'quick',
            'passed': len(issues) == 0,
            'score': max(0.0, min(1.0, score)),
            'issues': issues,
            'warnings': warnings,
            'execution_time': 0.1  # Quick validation is fast
        }
    
    def _full_validate(
        self,
        python_version: str,
        packages: Dict[str, str],
        code: str
    ) -> Dict[str, Any]:
        """
        Full validation with actual pip install (slower but accurate)
        """
        import time
        start_time = time.time()
        
        issues = []
        warnings = []
        
        try:
            # Create temporary virtual environment
            with tempfile.TemporaryDirectory() as tmpdir:
                # Try to install packages
                requirements = [f"{pkg}=={ver}" for pkg, ver in packages.items()]
                
                # Simulate pip install (dry-run)
                result = subprocess.run(
                    ['pip', 'install', '--dry-run', '--no-deps'] + requirements,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    issues.append(f"Installation failed: {result.stderr[:200]}")
                    score = 0.3
                else:
                    score = 1.0
                    
        except subprocess.TimeoutExpired:
            issues.append("Validation timeout")
            score = 0.2
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
            score = 0.1
        
        execution_time = time.time() - start_time
        
        return {
            'method': 'full',
            'passed': len(issues) == 0,
            'score': score,
            'issues': issues,
            'warnings': warnings,
            'execution_time': execution_time
        }
    
    def _check_known_incompatibilities(
        self,
        package: str,
        version: str,
        python_version: str,
        all_packages: Dict[str, str]
    ) -> Optional[str]:
        """
        Check for known incompatibilities between packages
        """
        # Known incompatibility rules
        incompatibilities = {
            'numpy': {
                '1.20+': {'python': '<3.7'},
                '1.24+': {'python': '<3.8'},
            },
            'pandas': {
                '2.0+': {'python': '<3.8', 'numpy': '<1.20'},
            },
            'tensorflow': {
                '2.0+': {'python': '<3.5'},
                '2.10+': {'python': '<3.7'},
            },
            'torch': {
                '2.0+': {'python': '<3.8'},
            }
        }
        
        if package not in incompatibilities:
            return None
        
        try:
            pkg_major, pkg_minor = map(int, version.split('.')[:2])
            py_major, py_minor = map(int, python_version.split('.')[:2])
            
            # Check incompatibilities for this package version
            for ver_constraint, requirements in incompatibilities[package].items():
                # Parse version constraint (simplified)
                if '+' in ver_constraint:
                    min_ver = ver_constraint.replace('+', '')
                    min_major, min_minor = map(int, min_ver.split('.')[:2])
                    
                    if (pkg_major > min_major) or (pkg_major == min_major and pkg_minor >= min_minor):
                        # Check Python version requirement
                        if 'python' in requirements:
                            py_req = requirements['python']
                            if '<' in py_req:
                                max_py = py_req.replace('<', '')
                                max_major, max_minor = map(int, max_py.split('.')[:2])
                                if (py_major > max_major) or (py_major == max_major and py_minor >= max_minor):
                                    return f"{package}>={min_ver} requires Python {py_req}"
                        
                        # Check other package requirements
                        for req_pkg, req_ver in requirements.items():
                            if req_pkg != 'python' and req_pkg in all_packages:
                                # Simplified version check
                                if '<' in req_ver:
                                    return f"{package}>={min_ver} incompatible with {req_pkg} {all_packages[req_pkg]}"
        
        except Exception:
            pass
        
        return None
    
    def _has_circular_dependencies(self, packages: Dict[str, str]) -> bool:
        """
        Check for potential circular dependencies (simplified)
        """
        # In a real implementation, this would build a dependency graph
        # For now, just return False
        return False
    
    def _calculate_final_score(
        self,
        candidate: Dict,
        validation: Dict
    ) -> float:
        """
        Calculate final score combining confidence and validation
        """
        confidence = candidate.get('confidence', 0.5)
        validation_score = validation.get('score', 0.0)
        
        # Weighted combination
        final_score = (confidence * 0.4) + (validation_score * 0.6)
        
        # Penalty for issues
        num_issues = len(validation.get('issues', []))
        if num_issues > 0:
            final_score *= (0.9 ** num_issues)
        
        return final_score
    
    def _generate_summary(self, validated_candidates: List[Dict]) -> str:
        """
        Generate validation summary
        """
        total = len(validated_candidates)
        passed = sum(1 for c in validated_candidates if c.get('validation', {}).get('passed', False))
        
        summary = f"Validated {total} candidates: {passed} passed, {total - passed} failed.\n"
        
        if validated_candidates:
            best = validated_candidates[0]
            summary += f"Best candidate: {best.get('source')} "
            summary += f"(score: {best.get('final_score', 0):.3f}, "
            summary += f"Python {best.get('python_version')}, "
            summary += f"{len(best.get('packages', {}))} packages)"
        
        return summary
