"""
Learner Agent: Learn from successes and failures to improve over time
"""

import json
import time
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent


class LearnerAgent(BaseAgent):
    """
    Learns from resolution attempts to improve future performance
    """
    
    def __init__(self, rag_system=None, **kwargs):
        super().__init__(name="Learner", **kwargs)
        self.rag_system = rag_system
        self.success_count = 0
        self.failure_count = 0
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from resolution attempt
        
        Args:
            input_data: {
                'snippet_path': str - Path to snippet
                'code': str - Original code
                'analysis': Dict - Analyzer output
                'solution': Dict - Final solution
                'success': bool - Whether resolution succeeded
                'error_logs': List[str] - Error messages if failed
            }
            
        Returns:
            {
                'learned': bool - Whether learning was successful
                'knowledge_updated': bool - Whether knowledge base was updated
                'insights': List[str] - Key insights learned
            }
        """
        snippet_path = input_data.get('snippet_path', 'unknown')
        success = input_data.get('success', False)
        
        if success:
            self.success_count += 1
            self.log(f"Learning from SUCCESS: {snippet_path}")
            return self._learn_from_success(input_data)
        else:
            self.failure_count += 1
            self.log(f"Learning from FAILURE: {snippet_path}")
            return self._learn_from_failure(input_data)
    
    def _learn_from_success(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from successful resolution
        """
        snippet_path = input_data.get('snippet_path', 'unknown')
        code = input_data.get('code', '')
        analysis = input_data.get('analysis', {})
        solution = input_data.get('solution', {})
        
        insights = []
        
        # Extract key information
        imports = analysis.get('imports', [])
        python_version = solution.get('python_version', '3.8')
        packages = solution.get('packages', {})
        
        # Store in knowledge base
        knowledge_updated = False
        if self.rag_system:
            try:
                # Create document for RAG
                document = {
                    'snippet_id': snippet_path,
                    'imports': imports,
                    'python_version': python_version,
                    'packages': packages,
                    'success': True,
                    'timestamp': time.time(),
                    'code_snippet': code[:500],  # First 500 chars
                    'syntax_features': analysis.get('syntax_features', []),
                    'api_patterns': analysis.get('api_patterns', [])
                }
                
                self.rag_system.add_document(document)
                knowledge_updated = True
                insights.append(f"Added successful resolution to knowledge base")
                
            except Exception as e:
                self.log(f"Failed to update knowledge base: {e}", "WARNING")
        
        # Analyze what made this solution work
        if packages:
            insights.append(f"Working combination: Python {python_version} with {len(packages)} packages")
            
            # Check for interesting patterns
            if 'numpy' in packages and 'pandas' in packages:
                insights.append(f"NumPy {packages['numpy']} + Pandas {packages.get('pandas')} compatible")
        
        return {
            'learned': True,
            'knowledge_updated': knowledge_updated,
            'insights': insights,
            'total_successes': self.success_count
        }
    
    def _learn_from_failure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from failed resolution
        """
        snippet_path = input_data.get('snippet_path', 'unknown')
        code = input_data.get('code', '')
        analysis = input_data.get('analysis', {})
        error_logs = input_data.get('error_logs', [])
        attempted_solutions = input_data.get('attempted_solutions', [])
        
        insights = []
        
        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(error_logs)
        if error_patterns:
            insights.extend(error_patterns)
        
        # Analyze what didn't work
        if attempted_solutions:
            insights.append(f"Tried {len(attempted_solutions)} solutions, all failed")
            
            # Check for common failure patterns
            python_versions_tried = [s.get('python_version') for s in attempted_solutions]
            if len(set(python_versions_tried)) > 1:
                insights.append(f"Python versions tried: {', '.join(set(python_versions_tried))}")
        
        # Store failure information (for future avoidance)
        knowledge_updated = False
        if self.rag_system:
            try:
                document = {
                    'snippet_id': snippet_path,
                    'imports': analysis.get('imports', []),
                    'success': False,
                    'timestamp': time.time(),
                    'error_patterns': error_patterns,
                    'attempted_solutions': attempted_solutions[:3],  # Store top 3 attempts
                    'code_snippet': code[:500]
                }
                
                self.rag_system.add_document(document)
                knowledge_updated = True
                insights.append("Recorded failure pattern to avoid in future")
                
            except Exception as e:
                self.log(f"Failed to record failure: {e}", "WARNING")
        
        return {
            'learned': True,
            'knowledge_updated': knowledge_updated,
            'insights': insights,
            'total_failures': self.failure_count,
            'error_patterns': error_patterns
        }
    
    def _analyze_error_patterns(self, error_logs: List[str]) -> List[str]:
        """
        Analyze error logs to extract patterns
        """
        patterns = []
        
        for error in error_logs:
            error_lower = error.lower()
            
            # Common error patterns
            if 'modulenotfounderror' in error_lower or 'no module named' in error_lower:
                patterns.append("Missing module error")
            elif 'importerror' in error_lower:
                patterns.append("Import error - possible version incompatibility")
            elif 'attributeerror' in error_lower:
                patterns.append("Attribute error - API changed")
            elif 'syntaxerror' in error_lower:
                patterns.append("Syntax error - Python version mismatch")
            elif 'versionconflict' in error_lower:
                patterns.append("Version conflict detected")
            elif 'deprecation' in error_lower:
                patterns.append("Deprecation warning - outdated API usage")
        
        return list(set(patterns))  # Remove duplicates
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get learning statistics
        """
        total = self.success_count + self.failure_count
        success_rate = self.success_count / total if total > 0 else 0.0
        
        return {
            'total_attempts': total,
            'successes': self.success_count,
            'failures': self.failure_count,
            'success_rate': success_rate
        }
