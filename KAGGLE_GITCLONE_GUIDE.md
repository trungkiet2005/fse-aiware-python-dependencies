# 🚀 Kaggle Git Clone Guide - FSE 2026 AIWare

## Workflow: Git Clone Project → Run on Kaggle

Thay vì tạo files trong notebook, bạn sẽ:
1. Push code lên GitHub
2. Clone về Kaggle
3. Chạy trực tiếp

---

## Bước 1: Push Code Lên GitHub (Local)

```bash
cd D:\AI_RESEARCH\fse-aiware-python-dependencies

# Add remote nếu chưa có
git remote add origin https://github.com/YOUR_USERNAME/fse-aiware-python-dependencies.git

# Commit và push
git add .
git commit -m "Add HybridAgent-RAG implementation"
git push -u origin main
```

---

## Bước 2: Tạo Kaggle Notebook

### Cell 1: Markdown
```markdown
# HybridAgent-RAG: FSE 2026 AIWare Competition
## Git Clone & Run Approach

**Target**: >50% success rate (PLLM: 38%)

**Settings**:
- GPU: T4/P100/H100
- Internet: ON
- Persistence: ON
```

### Cell 2: Check GPU
```python
!nvidia-smi

import torch
print(f"\nCUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
```

### Cell 3: Install Ollama
```bash
%%bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

### Cell 4: Start Ollama Server
```python
import subprocess
import time
import os
import requests

os.environ['OLLAMA_HOST'] = '0.0.0.0:11434'
os.environ['OLLAMA_ORIGINS'] = '*'

print("Starting Ollama...")
ollama_process = subprocess.Popen(
    ['ollama', 'serve'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=os.environ
)

time.sleep(10)

try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    print(f"Ollama running: {response.status_code == 200}")
except Exception as e:
    print(f"Error: {e}")
```

### Cell 5: Download Model
```python
print("Downloading gemma2 (5-10 minutes)...")
!ollama pull gemma2
!ollama list
```

### Cell 6: Clone Repository
```python
import os

repo_path = '/kaggle/working/fse-aiware-python-dependencies'

if not os.path.exists(repo_path):
    print("Cloning repository...")
    # CHANGE THIS TO YOUR GITHUB URL
    !git clone https://github.com/YOUR_USERNAME/fse-aiware-python-dependencies.git {repo_path}
else:
    print("Pulling latest...")
    %cd {repo_path}
    !git pull origin main

%cd {repo_path}
!ls -la

# Verify fix is applied
!grep -n "final_score >= 0.5" tools/hybridagent-rag/agents/coordinator.py || echo "⚠️ Fix not found, check if you pushed latest code"
```

### Cell 7: Extract Dataset
```python
if os.path.exists('hard-gists.tar.gz'):
    if not os.path.exists('hard-gists'):
        print("Extracting...")
        !tar -xzf hard-gists.tar.gz
    
    snippet_count = !find hard-gists -name "snippet.py" | wc -l
    print(f"Total snippets: {snippet_count[0]}")
```

### Cell 8: Install Dependencies
```python
%cd /kaggle/working/fse-aiware-python-dependencies/tools/hybridagent-rag
!pip install -q -r requirements.txt
print("Dependencies installed!")
```

### Cell 9: Initialize System
```python
import sys
sys.path.insert(0, '/kaggle/working/fse-aiware-python-dependencies/tools/hybridagent-rag')

from agents.coordinator import CoordinatorAgent
from agents.analyzer import AnalyzerAgent
from agents.resolver import ResolverAgent
from agents.validator import ValidatorAgent
from agents.learner import LearnerAgent
from rag.adaptive_rag import AdaptiveRAG
from graph.conflict_detector import ConflictDetector

print("Initializing HybridAgent-RAG...")

# Initialize components
rag_system = AdaptiveRAG()  # No model/base_url needed
conflict_detector = ConflictDetector()

# Initialize agents
analyzer = AnalyzerAgent(model="gemma2", base_url="http://localhost:11434")
resolver = ResolverAgent(
    rag_system=rag_system, 
    graph_detector=conflict_detector,
    model="gemma2", 
    base_url="http://localhost:11434"
)
validator = ValidatorAgent(model="gemma2", base_url="http://localhost:11434")
learner = LearnerAgent(
    rag_system=rag_system,
    model="gemma2", 
    base_url="http://localhost:11434"
)

# Initialize coordinator
coordinator = CoordinatorAgent(
    analyzer=analyzer,
    resolver=resolver,
    validator=validator,
    learner=learner,
    model="gemma2",
    base_url="http://localhost:11434",
    max_iterations=5
)

print("System ready!")
```

### Cell 10: Test on 5 Samples (WITH DEBUG)
```python
import glob
import traceback

snippets = glob.glob('/kaggle/working/fse-aiware-python-dependencies/hard-gists/*/snippet.py')[:5]

print(f"Testing {len(snippets)} samples...\n")

# First, test a simple case manually to see what's wrong
print("="*80)
print("DEBUG: Testing analyzer first")
print("="*80)
test_code = "import numpy as np\nimport pandas as pd"
try:
    analysis = analyzer.process({'code': test_code, 'snippet_path': 'test.py'})
    print(f"✅ Analyzer works! Found imports: {analysis.get('imports')}")
except Exception as e:
    print(f"❌ Analyzer failed: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("DEBUG: Testing resolver")
print("="*80)
try:
    resolution = resolver.process({
        'analysis': {'imports': ['numpy', 'pandas'], 'python_version_min': '3.8'},
        'code': test_code,
        'context': {}
    })
    print(f"✅ Resolver works! Generated {len(resolution.get('candidates', []))} candidates")
    if resolution.get('candidates'):
        print(f"First candidate: {resolution['candidates'][0]}")
except Exception as e:
    print(f"❌ Resolver failed: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("DEBUG: Testing validator")
print("="*80)
try:
    # Use the candidate from resolver
    test_candidates = resolution.get('candidates', [])
    if test_candidates:
        validation = validator.process({
            'candidates': test_candidates,
            'code': test_code,
            'quick_mode': True
        })
        print(f"✅ Validator works!")
        print(f"Best candidate: {validation.get('best_candidate')}")
        if validation.get('best_candidate'):
            print(f"Final score: {validation['best_candidate'].get('final_score')}")
        else:
            print("⚠️ No best candidate (all rejected)")
    else:
        print("⚠️ No candidates to validate")
except Exception as e:
    print(f"❌ Validator failed: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("DEBUG: Testing full coordinator")
print("="*80)
try:
    result = coordinator.process({'snippet_path': 'test.py', 'code': test_code})
    print(f"✅ Coordinator works!")
    print(f"Success: {result['success']}")
    print(f"Time: {result['execution_time']:.2f}s")
    print(f"Iterations: {result.get('iterations_used')}")
    print(f"Attempts: {len(result.get('attempts', []))}")
    if result.get('solution'):
        print(f"Solution found: {result['solution']}")
    else:
        print(f"⚠️ No solution found")
    if result.get('error_logs'):
        print(f"Errors: {result['error_logs'][:3]}")
except Exception as e:
    print(f"❌ Coordinator failed: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("Now testing real snippets...")
print("="*80 + "\n")

for i, path in enumerate(snippets, 1):
    print(f"\n{'='*80}")
    print(f"[{i}/{len(snippets)}] {path}")
    print(f"{'='*80}")
    
    try:
        with open(path, 'r') as f:
            code = f.read()
        
        print(f"Code length: {len(code)} chars")
        
        result = coordinator.process({'snippet_path': path, 'code': code})
        
        if result['success']:
            print(f"✅ SUCCESS in {result['execution_time']:.2f}s")
            solution = result['solution']
            print(f"Python: {solution.get('python_version')}")
            print(f"Packages: {solution.get('packages')}")
        else:
            print(f"❌ FAILED in {result['execution_time']:.2f}s")
            if result.get('error_logs'):
                print(f"Errors: {result['error_logs'][:3]}")
            if result.get('attempts'):
                print(f"Attempts made: {len(result['attempts'])}")
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        traceback.print_exc()
    
    print(f"{'='*80}\n")
```

### Cell 11: Full Evaluation
```python
import glob
import json
import time
from tqdm import tqdm

# Get all snippets
all_snippets = glob.glob('/kaggle/working/fse-aiware-python-dependencies/hard-gists/*/snippet.py')

# For testing, limit to 100 (set to None for full 2900)
MAX_SNIPPETS = 100

if MAX_SNIPPETS:
    all_snippets = all_snippets[:MAX_SNIPPETS]

print(f"Evaluating {len(all_snippets)} snippets...")

# Load snippets
snippets = []
for path in tqdm(all_snippets, desc="Loading"):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        snippets.append({'path': path, 'code': code})
    except Exception as e:
        print(f"Skip {path}: {e}")

# Run evaluation
print("\nStarting evaluation...")
start_time = time.time()

results = coordinator.batch_process(snippets, quick_mode=True, verbose=True)

total_time = time.time() - start_time

# Metrics
total = len(results)
successful = sum(1 for r in results if r['success'])
success_rate = (successful / total * 100) if total > 0 else 0
avg_time = sum(r['execution_time'] for r in results) / total if total > 0 else 0

print(f"\n{'='*80}")
print(f"RESULTS")
print(f"{'='*80}")
print(f"Total:      {total}")
print(f"Success:    {successful} ({success_rate:.1f}%)")
print(f"Failed:     {total - successful}")
print(f"Avg Time:   {avg_time:.2f}s")
print(f"Total Time: {total_time:.2f}s")
print(f"{'='*80}")

# Save
output = {
    'total_snippets': total,
    'successful': successful,
    'success_rate': success_rate,
    'avg_time': avg_time,
    'total_time': total_time,
    'results': results
}

with open('/kaggle/working/hybridagent_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nResults saved to: /kaggle/working/hybridagent_results.json")
```

### Cell 12: Compare with PLLM
```python
import pandas as pd

# PLLM baseline
pllm_success_rate = 38.0

# Comparison
comparison = pd.DataFrame({
    'Metric': ['Success Rate (%)', 'Avg Time (s)', 'Improvement'],
    'PLLM': [pllm_success_rate, 60.0, '-'],
    'HybridAgent-RAG': [success_rate, avg_time, f"+{success_rate - pllm_success_rate:.1f}%"]
})

print("\nComparison:")
print("="*80)
print(comparison.to_string(index=False))
print("="*80)

improvement = ((success_rate - pllm_success_rate) / pllm_success_rate * 100)
print(f"\nRelative Improvement: {improvement:.1f}%")

if success_rate > pllm_success_rate:
    print(f"Outperforms PLLM by {success_rate - pllm_success_rate:.1f} points!")
```

### Cell 13: Paper Statistics
```python
print("\nPAPER STATISTICS")
print("="*80)

print("\n1. PERFORMANCE:")
print(f"   Success Rate: {success_rate:.1f}% (PLLM: {pllm_success_rate:.1f}%)")
print(f"   Improvement: +{success_rate - pllm_success_rate:.1f} points ({improvement:.1f}% relative)")
print(f"   Avg Time: {avg_time:.2f}s")

print("\n2. AGENT STATS:")
stats = coordinator.get_statistics()['learner_stats']
print(f"   Total: {stats['total_attempts']}")
print(f"   Success: {stats['successes']}")
print(f"   Failed: {stats['failures']}")

print("\n3. KEY FINDINGS:")
print(f"   - {success_rate:.1f}% success rate")
print(f"   - {improvement:.1f}% improvement")
print(f"   - {avg_time:.2f}s avg time")
print(f"   - <10GB VRAM")

print("\n="*80)
```

---

## Bước 3: Sau Khi Chạy Xong

1. **Download Results**: `/kaggle/working/hybridagent_results.json`
2. **Write Paper**: `paper_fse/hybridagent_paper.tex`
3. **Submit**: Before March 6, 2026

---

## Troubleshooting

### Lỗi: "No valid candidates"
→ Check if Ollama is running: `!curl http://localhost:11434/api/tags`

### Lỗi: "Module not found"
→ Check sys.path: `print(sys.path)`

### Lỗi: "CUDA out of memory"
→ Use smaller model: `!ollama pull gemma2:2b`

---

## Tips

1. **Test First**: Run Cell 10 (5 samples) before full evaluation
2. **Monitor VRAM**: `!nvidia-smi` between cells
3. **Save Often**: Results auto-save to JSON
4. **Time Limit**: Kaggle has 12-hour limit (enough for full dataset)

---

**Target**: >50% success rate (PLLM: 38%)
**Deadline**: March 6, 2026

Good luck! 🚀
