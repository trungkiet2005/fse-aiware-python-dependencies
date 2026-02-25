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
        
        system_prompt = """You are a Python dependency resolution expert with deep knowledge of package compatibility.
Your task is to generate SPECIFIC version numbers that are known to work together.

IMPORTANT RULES:
1. Use REAL version numbers (e.g., "1.21.0", not "latest" or "1.x")
2. Consider Python version compatibility
3. Avoid known conflicts (e.g., TensorFlow 2.x needs Python >=3.7)
4. Use stable versions from 2020-2023 era
5. Format response as valid JSON

Response format:
{
    "python_version": "3.8",
    "packages": {
        "numpy": "1.21.0",
        "pandas": "1.3.0"
    },
    "reasoning": "These versions are compatible with Python 3.8 and each other"
}"""
        
        prompt = f"""Resolve dependencies for this Python code:

Required imports: {', '.join(imports)}
Minimum Python version: {python_version}
API patterns detected: {', '.join(api_patterns) if api_patterns else 'None'}
{context_info}
{conflict_info}

Generate a working dependency solution with specific version numbers.
Focus on compatibility and stability."""
        
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
        Generate conservative solution with stable versions + fallback
        """
        imports = analysis.get('imports', [])
        python_version = analysis.get('python_version_min', '3.8')
        
        # Extended conservative version mappings (stable, well-tested versions)
        conservative_versions = {
            # Core Data Science
            'numpy': '1.21.6',
            'pandas': '1.3.5',
            'scipy': '1.7.3',
            'matplotlib': '3.5.3',
            'seaborn': '0.11.2',
            'plotly': '5.3.1',
            'bokeh': '2.4.3',
            
            # Machine Learning
            'sklearn': '1.0.2',
            'scikit-learn': '1.0.2',
            'tensorflow': '2.8.4',
            'torch': '1.11.0',
            'keras': '2.8.0',
            'xgboost': '1.5.2',
            'lightgbm': '3.3.2',
            'catboost': '1.0.4',
            
            # Deep Learning Utilities
            'torchvision': '0.12.0',
            'tensorboard': '2.8.0',
            'tensorboardX': '2.5',
            
            # NLP
            'nltk': '3.7',
            'spacy': '3.2.4',
            'transformers': '4.17.0',
            'gensim': '4.1.2',
            'textblob': '0.17.1',
            
            # Computer Vision
            'opencv-python': '4.5.5.64',
            'cv2': '4.5.5.64',
            'pillow': '9.0.1',
            'PIL': '9.0.1',
            'imageio': '2.16.1',
            'skimage': '0.19.2',
            'scikit-image': '0.19.2',
            
            # Web Frameworks
            'requests': '2.27.1',
            'flask': '2.0.3',
            'django': '3.2.13',
            'fastapi': '0.75.0',
            'aiohttp': '3.8.1',
            'tornado': '6.1',
            'bottle': '0.12.19',
            
            # Web Scraping
            'beautifulsoup4': '4.10.0',
            'bs4': '4.10.0',
            'selenium': '4.1.3',
            'scrapy': '2.6.1',
            'lxml': '4.8.0',
            
            # Database
            'sqlalchemy': '1.4.32',
            'pymongo': '4.0.2',
            'redis': '4.1.4',
            'psycopg2': '2.9.3',
            'psycopg2-binary': '2.9.3',
            'mysql-connector-python': '8.0.28',
            'pymysql': '1.0.2',
            
            # Data Formats
            'pyyaml': '6.0',
            'yaml': '6.0',
            'toml': '0.10.2',
            'xmltodict': '0.12.0',
            'openpyxl': '3.0.9',
            'xlrd': '2.0.1',
            'h5py': '3.6.0',
            
            # Testing
            'pytest': '7.1.1',
            'mock': '4.0.3',
            'coverage': '6.3.2',
            'hypothesis': '6.39.3',
            
            # Utilities
            'click': '8.0.4',
            'tqdm': '4.63.0',
            'joblib': '1.1.0',
            'more-itertools': '8.12.0',
            'python-dateutil': '2.8.2',
            'dateutil': '2.8.2',
            'pytz': '2021.3',
            'six': '1.16.0',
            
            # Async
            'asyncio': '3.4.3',
            'aiofiles': '0.8.0',
            
            # Serialization
            'pickle5': '0.0.11',
            'dill': '0.3.4',
            'cloudpickle': '2.0.0',
            
            # Cryptography
            'cryptography': '36.0.2',
            'pycrypto': '2.6.1',
            
            # Networking
            'paramiko': '2.10.3',
            'fabric': '2.6.0',
            
            # AWS/Cloud
            'boto3': '1.21.21',
            'botocore': '1.24.21',
            'google-cloud-storage': '2.1.0',
            
            # Jupyter
            'jupyter': '1.0.0',
            'ipython': '8.1.1',
            'notebook': '6.4.10',
            'ipykernel': '6.9.2',
            'ipywidgets': '7.7.0',
        }
        
        packages = {}
        unknown_packages = []
        
        for imp in imports:
            if imp in conservative_versions:
                packages[imp] = conservative_versions[imp]
            else:
                # Fallback for unknown packages
                unknown_packages.append(imp)
                # Try to guess a reasonable version
                packages[imp] = self._guess_package_version(imp)
        
        # Adjust confidence based on unknown packages
        if not unknown_packages:
            confidence = 0.7  # High confidence - all known
        elif len(unknown_packages) < len(imports) / 2:
            confidence = 0.5  # Medium confidence - some unknown
        else:
            confidence = 0.3  # Low confidence - mostly unknown
        
        reasoning = 'Conservative approach with stable versions'
        if unknown_packages:
            reasoning += f'. Unknown packages ({len(unknown_packages)}): {", ".join(unknown_packages[:3])}'
            if len(unknown_packages) > 3:
                reasoning += f' and {len(unknown_packages) - 3} more'
        
        return {
            'source': 'conservative',
            'python_version': python_version,
            'packages': packages,
            'confidence': confidence,
            'reasoning': reasoning,
            'unknown_packages': unknown_packages
        }
    
    def _guess_package_version(self, package_name: str) -> str:
        """
        Guess a reasonable version for unknown packages
        """
        # Common patterns for package versions
        version_patterns = {
            # Packages that typically start at 1.x
            'default': '1.0.0',
            # Packages that use 0.x versioning
            'pre_1_0': '0.9.0',
        }
        
        # Some heuristics
        if package_name.startswith('py'):
            return '1.0.0'
        elif any(x in package_name for x in ['alpha', 'beta', 'dev']):
            return '0.5.0'
        else:
            return '1.0.0'  # Safe default
    
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
