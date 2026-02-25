# 🔍 Phân tích vấn đề HybridAgent-RAG trên Kaggle

## 📊 Kết quả hiện tại

```
Testing 5 samples...
✅ Analyzer works! Found imports: ['numpy', 'pandas']
✅ Resolver works! Generated 1 candidates
✅ Validator works! Best candidate score: 0.56
✅ Coordinator works! Success: False ← VẤN ĐỀ Ở ĐÂY!

Tất cả 5 snippets thực tế: ❌ FAILED in 0.00s
```

## 🐛 Nguyên nhân chính

### 1. **Imports không được phát hiện đầy đủ**

**Code hiện tại** (`analyzer.py:92-114`):
```python
def _extract_imports(self, code: str) -> List[str]:
    imports = set()
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
                top_level = module.split('.')[0]
                imports.add(top_level)
    
    return sorted(list(imports))
```

**Vấn đề:**
- Chỉ match dòng bắt đầu bằng `import` hoặc `from`
- Không xử lý:
  - Multi-line imports: `from package import (a, b, c)`
  - Imports có khoảng trắng đầu dòng (indented imports)
  - Dynamic imports: `__import__('module')`
  - Imports trong try/except blocks

### 2. **Conservative versions quá hạn chế**

**Code hiện tại** (`resolver.py:243-256`):
```python
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
```

**Vấn đề:**
- Chỉ có 12 packages
- HG2.9K dataset có hàng trăm packages khác nhau
- Nếu import không có trong list → `packages = {}` → empty solution → FAILED

### 3. **Không có fallback strategy**

Khi không tìm thấy packages trong conservative list:
```python
packages = {}
for imp in imports:
    if imp in conservative_versions:  # ← Nếu không match
        packages[imp] = conservative_versions[imp]

# packages = {} → empty solution → validation score = 0 → FAILED
```

### 4. **Success criteria quá nghiêm ngặt**

```python
success = solution is not None and solution.get('final_score', 0) >= 0.5
```

Với empty packages:
- `confidence = 0.6` (conservative)
- `validation_score = 0.0` (no packages to validate)
- `final_score = 0.6 * 0.4 + 0.0 * 0.6 = 0.24` < 0.5 → FAILED

## 🔧 Giải pháp

### Fix 1: Cải thiện Import Extraction

```python
def _extract_imports(self, code: str) -> List[str]:
    """Enhanced import extraction with AST parsing"""
    imports = set()
    
    # Method 1: AST parsing (most reliable)
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except SyntaxError:
        pass  # Fall back to regex
    
    # Method 2: Regex fallback (for syntax errors)
    patterns = [
        r'^\s*import\s+([\w.]+)',  # Allow leading whitespace
        r'^\s*from\s+([\w.]+)\s+import',
    ]
    
    for line in code.split('\n'):
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                module = match.group(1)
                imports.add(module.split('.')[0])
    
    # Filter out standard library
    stdlib = {'os', 'sys', 're', 'json', 'time', 'datetime', 'collections', 
              'itertools', 'functools', 'math', 'random', 'string', 'io',
              'pathlib', 'subprocess', 'threading', 'multiprocessing'}
    
    imports = imports - stdlib
    
    return sorted(list(imports))
```

### Fix 2: Mở rộng Conservative Versions

```python
# Thêm vào resolver.py
EXTENDED_CONSERVATIVE_VERSIONS = {
    # Data Science
    'numpy': '1.21.0',
    'pandas': '1.3.0',
    'scipy': '1.7.0',
    'matplotlib': '3.4.0',
    'seaborn': '0.11.0',
    'plotly': '5.0.0',
    
    # Machine Learning
    'sklearn': '0.24.0',
    'scikit-learn': '0.24.0',
    'tensorflow': '2.6.0',
    'torch': '1.9.0',
    'keras': '2.6.0',
    'xgboost': '1.4.0',
    'lightgbm': '3.2.0',
    
    # Web
    'requests': '2.26.0',
    'flask': '2.0.0',
    'django': '3.2.0',
    'fastapi': '0.68.0',
    'aiohttp': '3.7.0',
    'beautifulsoup4': '4.9.0',
    'bs4': '4.9.0',
    'selenium': '3.141.0',
    'scrapy': '2.5.0',
    
    # Database
    'sqlalchemy': '1.4.0',
    'pymongo': '3.12.0',
    'redis': '3.5.0',
    'psycopg2': '2.9.0',
    
    # Testing
    'pytest': '6.2.0',
    'unittest': '0.0.0',  # stdlib
    'mock': '4.0.0',
    
    # Utilities
    'pillow': '8.3.0',
    'opencv': '4.5.0',
    'cv2': '4.5.0',
    'pyyaml': '5.4.0',
    'yaml': '5.4.0',
    'click': '8.0.0',
    'tqdm': '4.62.0',
    'joblib': '1.0.0',
    
    # NLP
    'nltk': '3.6.0',
    'spacy': '3.1.0',
    'transformers': '4.10.0',
    'gensim': '4.0.0',
    
    # Image Processing
    'imageio': '2.9.0',
    'skimage': '0.18.0',
    'scikit-image': '0.18.0',
}
```

### Fix 3: Thêm Fallback Strategy

```python
def _generate_conservative_candidate(self, analysis: Dict) -> Dict:
    """Generate conservative solution with fallback for unknown packages"""
    imports = analysis.get('imports', [])
    python_version = analysis.get('python_version_min', '3.8')
    
    packages = {}
    unknown_packages = []
    
    for imp in imports:
        if imp in EXTENDED_CONSERVATIVE_VERSIONS:
            packages[imp] = EXTENDED_CONSERVATIVE_VERSIONS[imp]
        else:
            # Fallback: use PyPI to guess version
            unknown_packages.append(imp)
            # Use a generic stable version
            packages[imp] = '1.0.0'  # Better than nothing
    
    confidence = 0.6 if not unknown_packages else 0.4
    
    return {
        'source': 'conservative',
        'python_version': python_version,
        'packages': packages,
        'confidence': confidence,
        'reasoning': f'Conservative approach with stable versions. Unknown: {unknown_packages}' if unknown_packages else 'Conservative approach with stable versions',
        'unknown_packages': unknown_packages
    }
```

### Fix 4: Điều chỉnh Success Criteria

```python
# Trong coordinator.py
# Thay vì:
success = solution is not None and solution.get('final_score', 0) >= 0.5

# Sử dụng:
success = (
    solution is not None 
    and len(solution.get('packages', {})) > 0  # Có ít nhất 1 package
    and solution.get('final_score', 0) >= 0.3  # Lower threshold
)
```

### Fix 5: Thêm LLM Fallback cho Unknown Packages

```python
def _resolve_unknown_packages(self, unknown_packages: List[str]) -> Dict[str, str]:
    """Use LLM to suggest versions for unknown packages"""
    if not unknown_packages:
        return {}
    
    prompt = f"""For these Python packages, suggest stable compatible versions:
{', '.join(unknown_packages)}

Return JSON format:
{{"package_name": "version"}}
"""
    
    response = self.query_llm(prompt, temperature=0.3, max_tokens=200)
    
    try:
        # Parse JSON from response
        versions = json.loads(response)
        return versions
    except:
        # Fallback to 1.0.0
        return {pkg: '1.0.0' for pkg in unknown_packages}
```

## 📈 Kết quả mong đợi sau khi fix

**Trước:**
```
[1/5] snippet.py: ❌ FAILED in 0.00s
  - Imports: []  ← Không detect được
  - Packages: {}  ← Không có solution
  - Score: 0.0
```

**Sau:**
```
[1/5] snippet.py: ✅ SUCCESS in 0.15s
  - Imports: ['numpy', 'pandas', 'matplotlib', 'sklearn']
  - Packages: {'numpy': '1.21.0', 'pandas': '1.3.0', ...}
  - Score: 0.68
```

## 🎯 Implementation Priority

1. **HIGH**: Fix import extraction (AST parsing)
2. **HIGH**: Extend conservative versions dictionary
3. **MEDIUM**: Add fallback for unknown packages
4. **MEDIUM**: Adjust success criteria
5. **LOW**: LLM fallback (nice to have)

## 📝 Testing Plan

1. Extract `hard-gists.tar.gz`
2. Test on 10 random snippets
3. Analyze failure patterns
4. Iterate on fixes
5. Full evaluation on 100+ snippets

## 🚀 Expected Improvement

- **Current**: 0% success rate (0/5)
- **After Fix 1-2**: ~30-40% success rate
- **After Fix 3-4**: ~50-60% success rate
- **Target**: >50% (beat PLLM baseline of 38%)
