"""
Resolver Agent: Generate candidate dependency solutions
"""

import json
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent


class ResolverAgent(BaseAgent):
    """
    Generates candidate dependency solutions using RAG and LLM reasoning
    """
    
    def __init__(self, rag_system=None, graph_detector=None, **kwargs):
        super().__init__(name="Resolver", **kwargs)
        self.rag_system = rag_system
        self.graph_detector = graph_detector
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate candidate solutions for dependency resolution
        
        Args:
            input_data: {
                'analysis': Dict - Output from AnalyzerAgent
                'code': str - Original code
                'context': Dict - Additional context
            }
            
        Returns:
            {
                'candidates': List[Dict] - List of candidate solutions
                'reasoning': str - Explanation of approach
                'confidence': float - Overall confidence score
            }
        """
        analysis = input_data.get('analysis', {})
        code = input_data.get('code', '')
        context = input_data.get('context', {})
        
        imports = analysis.get('imports', [])
        python_version = analysis.get('python_version_min', '3.8')
        
        self.log(f"Generating solutions for {len(imports)} imports")
        
        # Step 1: Retrieve similar cases from RAG
        similar_cases = self._retrieve_similar_cases(analysis)
        
        # Step 2: Detect conflicts using graph
        conflicts = self._detect_conflicts(imports, python_version)
        
        # Step 3: Generate candidate solutions
        candidates = self._generate_candidates(
            analysis=analysis,
            similar_cases=similar_cases,
            conflicts=conflicts,
            context=context
        )
        
        # Step 4: Rank candidates
        ranked_candidates = self._rank_candidates(candidates, analysis)
        
        # Step 5: Get LLM reasoning
        reasoning = self._get_reasoning(analysis, ranked_candidates)
        
        return {
            'candidates': ranked_candidates[:5],  # Top 5
            'reasoning': reasoning,
            'confidence': self._calculate_confidence(ranked_candidates),
            'similar_cases_found': len(similar_cases),
            'conflicts_detected': len(conflicts)
        }
    
    def _retrieve_similar_cases(self, analysis: Dict) -> List[Dict]:
        """
        Retrieve similar cases from RAG system
        """
        if not self.rag_system:
            return []
        
        try:
            # Query RAG with imports and features
            query = {
                'imports': analysis.get('imports', []),
                'python_version': analysis.get('python_version_min'),
                'features': analysis.get('syntax_features', [])
            }
            
            similar = self.rag_system.retrieve(query, top_k=10)
            self.log(f"Retrieved {len(similar)} similar cases from RAG")
            return similar
            
        except Exception as e:
            self.log(f"RAG retrieval failed: {e}", "WARNING")
            return []
    
    def _detect_conflicts(self, imports: List[str], python_version: str) -> List[Dict]:
        """
        Detect potential conflicts using graph detector
        """
        if not self.graph_detector:
            return []
        
        try:
            conflicts = self.graph_detector.detect_conflicts(
                packages=imports,
                python_version=python_version
            )
            
            if conflicts:
                self.log(f"Detected {len(conflicts)} potential conflicts", "WARNING")
            
            return conflicts
            
        except Exception as e:
            self.log(f"Conflict detection failed: {e}", "WARNING")
            return []
    
    def _generate_candidates(
        self,
        analysis: Dict,
        similar_cases: List[Dict],
        conflicts: List[Dict],
        context: Dict
    ) -> List[Dict]:
        """
        Generate candidate solutions
        """
        candidates = []
        
        # Candidate 1: From similar cases (if available)
        if similar_cases:
            for case in similar_cases[:3]:  # Top 3 similar cases
                candidate = {
                    'source': 'rag_similar',
                    'python_version': case.get('python_version', '3.8'),
                    'packages': case.get('packages', {}),
                    'confidence': case.get('similarity_score', 0.5),
                    'reasoning': f"Based on similar case: {case.get('snippet_id', 'unknown')}"
                }
                candidates.append(candidate)
        
        # Candidate 2: LLM-generated solution
        llm_candidate = self._generate_llm_candidate(analysis, similar_cases, conflicts)
        if llm_candidate:
            candidates.append(llm_candidate)
        
        # Candidate 3: Conservative approach (latest stable versions)
        conservative_candidate = self._generate_conservative_candidate(analysis)
        candidates.append(conservative_candidate)
        
        # Candidate 4: Aggressive approach (latest versions)
        aggressive_candidate = self._generate_aggressive_candidate(analysis)
        candidates.append(aggressive_candidate)
        
        return candidates
    
    def _generate_llm_candidate(
        self,
        analysis: Dict,
        similar_cases: List[Dict],
        conflicts: List[Dict]
    ) -> Optional[Dict]:
        """
        Generate solution using LLM reasoning
        """
        imports = analysis.get('imports', [])
        python_version = analysis.get('python_version_min', '3.8')
        api_patterns = analysis.get('api_patterns', [])
        
        # Build context from similar cases
        context_info = ""
        if similar_cases:
            context_info = "\n\nSimilar successful resolutions:\n"
            for case in similar_cases[:2]:
                context_info += f"- Python {case.get('python_version')}: {case.get('packages')}\n"
        
        # Build conflict info
        conflict_info = ""
        if conflicts:
            conflict_info = "\n\nDetected conflicts:\n"
            for conflict in conflicts:
                conflict_info += f"- {conflict.get('description', 'Unknown conflict')}\n"
        
        system_prompt = """You are a Python dependency resolution expert. 
Generate specific package versions that are compatible with each other.
Format your response as JSON:
{
    "python_version": "3.x",
    "packages": {
        "package_name": "version"
    },
    "reasoning": "brief explanation"
}"""
        
        prompt = f"""Resolve dependencies for this Python code:

Imports: {', '.join(imports)}
Minimum Python version: {python_version}
API patterns detected: {', '.join(api_patterns) if api_patterns else 'None'}
{context_info}
{conflict_info}

Provide compatible package versions."""
        
        response = self.query_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=500
        )
        
        # Parse LLM response
        try:
            # Try to extract JSON from response
            json_match = response.find('{')
            if json_match != -1:
                json_end = response.rfind('}') + 1
                json_str = response[json_match:json_end]
                result = json.loads(json_str)
                
                return {
                    'source': 'llm_reasoning',
                    'python_version': result.get('python_version', python_version),
                    'packages': result.get('packages', {}),
                    'confidence': 0.7,
                    'reasoning': result.get('reasoning', 'LLM-generated solution')
                }
        except Exception as e:
            self.log(f"Failed to parse LLM response: {e}", "WARNING")
        
        return None
    
    def _generate_conservative_candidate(self, analysis: Dict) -> Dict:
        """
        Generate conservative solution with stable versions
        """
        imports = analysis.get('imports', [])
        python_version = analysis.get('python_version_min', '3.8')
        
        # Conservative version mappings (stable, well-tested versions)
        conservative_versions = {
            'numpy': '1.21.0',
            'pandas': '1.3.0',
            'scipy': '1.7.0',
            'matplotlib': '3.4.0',
            'sklearn': '0.24.0',
            'scikit-learn': '0.24.0',
            'requests': '2.26.0',
            'flask': '2.0.0',
            'django': '3.2.0',
            'tensorflow': '2.6.0',
            'torch': '1.9.0',
            'pytest': '6.2.0',
        }
        
        packages = {}
        for imp in imports:
            if imp in conservative_versions:
                packages[imp] = conservative_versions[imp]
        
        return {
            'source': 'conservative',
            'python_version': python_version,
            'packages': packages,
            'confidence': 0.6,
            'reasoning': 'Conservative approach with stable versions'
        }
    
    def _generate_aggressive_candidate(self, analysis: Dict) -> Dict:
        """
        Generate aggressive solution with latest versions
        """
        imports = analysis.get('imports', [])
        python_version = analysis.get('python_version_min', '3.8')
        
        # Latest stable versions (as of training data)
        latest_versions = {
            'numpy': '1.24.0',
            'pandas': '2.0.0',
            'scipy': '1.10.0',
            'matplotlib': '3.7.0',
            'sklearn': '1.2.0',
            'scikit-learn': '1.2.0',
            'requests': '2.31.0',
            'flask': '2.3.0',
            'django': '4.2.0',
            'tensorflow': '2.12.0',
            'torch': '2.0.0',
            'pytest': '7.3.0',
        }
        
        packages = {}
        for imp in imports:
            if imp in latest_versions:
                packages[imp] = latest_versions[imp]
        
        return {
            'source': 'aggressive',
            'python_version': '3.10',  # Use newer Python
            'packages': packages,
            'confidence': 0.5,
            'reasoning': 'Aggressive approach with latest versions'
        }
    
    def _rank_candidates(self, candidates: List[Dict], analysis: Dict) -> List[Dict]:
        """
        Rank candidates by confidence and compatibility
        """
        # Sort by confidence score
        ranked = sorted(candidates, key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Add rank
        for i, candidate in enumerate(ranked):
            candidate['rank'] = i + 1
        
        return ranked
    
    def _calculate_confidence(self, candidates: List[Dict]) -> float:
        """
        Calculate overall confidence in solutions
        """
        if not candidates:
            return 0.0
        
        # Average of top 3 candidates
        top_confidences = [c.get('confidence', 0) for c in candidates[:3]]
        return sum(top_confidences) / len(top_confidences) if top_confidences else 0.0
    
    def _get_reasoning(self, analysis: Dict, candidates: List[Dict]) -> str:
        """
        Generate explanation of resolution approach
        """
        imports = analysis.get('imports', [])
        
        reasoning = f"Analyzed {len(imports)} imports and generated {len(candidates)} candidate solutions.\n"
        reasoning += f"Top candidate (confidence: {candidates[0].get('confidence', 0):.2f}): "
        reasoning += f"{candidates[0].get('source')} - {candidates[0].get('reasoning')}"
        
        return reasoning
