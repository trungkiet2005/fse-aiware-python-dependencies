"""
Analyzer Agent: Deep code analysis and dependency extraction
"""

import re
import ast
from typing import Dict, List, Set, Any, Optional
from .base_agent import BaseAgent


class AnalyzerAgent(BaseAgent):
    """
    Analyzes Python code to extract dependencies, detect patterns,
    and estimate Python version requirements
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="Analyzer", **kwargs)
        
        # Python version indicators
        self.version_indicators = {
            'f"': '3.6+',  # f-strings
            'async def': '3.5+',
            'await ': '3.5+',
            ':=': '3.8+',  # walrus operator
            'match ': '3.10+',  # pattern matching
            'type ': '3.12+',  # type statement
            '|': '3.10+',  # union types (context-dependent)
        }
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Python code snippet
        
        Args:
            input_data: {
                'code': str - Python code to analyze
                'snippet_path': str - Path to snippet file
            }
            
        Returns:
            {
                'imports': List[str] - Extracted imports
                'python_version_min': str - Minimum Python version
                'syntax_features': List[str] - Detected syntax features
                'api_patterns': List[str] - API usage patterns
                'inline_hints': Dict - Version hints from comments
                'complexity': Dict - Code complexity metrics
                'llm_analysis': str - LLM's understanding
            }
        """
        code = input_data.get('code', '')
        snippet_path = input_data.get('snippet_path', 'unknown')
        
        self.log(f"Analyzing snippet: {snippet_path}")
        
        # Extract imports
        imports = self._extract_imports(code)
        self.log(f"Found {len(imports)} imports: {', '.join(imports)}")
        
        # Detect Python version requirements
        python_version = self._detect_python_version(code)
        self.log(f"Estimated Python version: {python_version}")
        
        # Extract syntax features
        syntax_features = self._detect_syntax_features(code)
        
        # Detect API usage patterns
        api_patterns = self._detect_api_patterns(code, imports)
        
        # Extract inline version hints
        inline_hints = self._extract_inline_hints(code)
        
        # Calculate complexity
        complexity = self._calculate_complexity(code)
        
        # Get LLM analysis
        llm_analysis = self._get_llm_analysis(code, imports)
        
        return {
            'imports': imports,
            'python_version_min': python_version,
            'syntax_features': syntax_features,
            'api_patterns': api_patterns,
            'inline_hints': inline_hints,
            'complexity': complexity,
            'llm_analysis': llm_analysis,
            'code_length': len(code),
            'code_lines': len(code.splitlines())
        }
    
    def _extract_imports(self, code: str) -> List[str]:
        """
        Extract all import statements from code
        """
        imports = set()
        
        # Regex patterns for imports
        patterns = [
            r'^import\s+([\w.]+)',
            r'^from\s+([\w.]+)\s+import',
        ]
        
        for line in code.split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1)
                    # Get top-level package
                    top_level = module.split('.')[0]
                    imports.add(top_level)
        
        return sorted(list(imports))
    
    def _detect_python_version(self, code: str) -> str:
        """
        Detect minimum Python version based on syntax features
        """
        detected_versions = []
        
        for feature, version in self.version_indicators.items():
            if feature in code:
                detected_versions.append(version)
        
        # Return highest version requirement
        if detected_versions:
            # Extract version numbers and find max
            versions = [v.replace('+', '') for v in detected_versions]
            max_version = max(versions)
            return max_version
        
        return "3.6"  # Default minimum
    
    def _detect_syntax_features(self, code: str) -> List[str]:
        """
        Detect modern Python syntax features
        """
        features = []
        
        if 'f"' in code or "f'" in code:
            features.append('f-strings')
        if 'async def' in code or 'await ' in code:
            features.append('async/await')
        if ':=' in code:
            features.append('walrus operator')
        if 'match ' in code and 'case ' in code:
            features.append('pattern matching')
        if '@dataclass' in code:
            features.append('dataclasses')
        if 'typing.' in code or 'from typing import' in code:
            features.append('type hints')
        
        return features
    
    def _detect_api_patterns(self, code: str, imports: List[str]) -> List[str]:
        """
        Detect specific API usage patterns that may indicate version requirements
        """
        patterns = []
        
        # NumPy patterns
        if 'numpy' in imports or 'np' in code:
            if 'np.random.Generator' in code:
                patterns.append('numpy>=1.17 (Generator API)')
            if 'dtype=np.float' in code and 'np.float' in code:
                patterns.append('numpy<1.20 (np.float deprecated)')
        
        # Pandas patterns
        if 'pandas' in imports or 'pd' in code:
            if '.append(' in code:
                patterns.append('pandas<2.0 (append deprecated)')
            if '.concat(' in code:
                patterns.append('pandas>=0.23 (concat)')
        
        # Scikit-learn patterns
        if 'sklearn' in imports:
            if 'from sklearn.cross_validation' in code:
                patterns.append('sklearn<0.20 (cross_validation deprecated)')
            if 'from sklearn.model_selection' in code:
                patterns.append('sklearn>=0.18 (model_selection)')
        
        return patterns
    
    def _extract_inline_hints(self, code: str) -> Dict[str, Any]:
        """
        Extract version hints from comments and docstrings
        """
        hints = {
            'python_version': None,
            'package_versions': {},
            'requirements': []
        }
        
        # Look for version comments
        version_patterns = [
            r'#.*python\s*([0-9.]+)',
            r'#.*requires?\s*([a-zA-Z0-9_-]+)\s*([<>=!]+)\s*([0-9.]+)',
        ]
        
        for line in code.split('\n'):
            line_lower = line.lower()
            
            # Python version hints
            match = re.search(r'#.*python\s*([0-9.]+)', line_lower)
            if match:
                hints['python_version'] = match.group(1)
            
            # Package version hints
            match = re.search(r'#.*requires?\s*([a-zA-Z0-9_-]+)\s*([<>=!]+)\s*([0-9.]+)', line_lower)
            if match:
                package, operator, version = match.groups()
                hints['package_versions'][package] = f"{operator}{version}"
        
        return hints
    
    def _calculate_complexity(self, code: str) -> Dict[str, int]:
        """
        Calculate code complexity metrics
        """
        return {
            'lines': len(code.splitlines()),
            'characters': len(code),
            'imports': len(self._extract_imports(code)),
            'functions': code.count('def '),
            'classes': code.count('class '),
        }
    
    def _get_llm_analysis(self, code: str, imports: List[str]) -> str:
        """
        Get LLM's analysis of the code
        """
        system_prompt = """You are a Python dependency expert. Analyze code and identify:
1. What the code is trying to do
2. Key dependencies and their likely version requirements
3. Potential compatibility issues
Be concise and specific."""
        
        prompt = f"""Analyze this Python code:

Imports: {', '.join(imports)}

Code snippet (first 500 chars):
```python
{code[:500]}
```

Provide brief analysis of dependencies and version requirements."""
        
        analysis = self.query_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for analysis
            max_tokens=300
        )
        
        return analysis
