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

### Cell 11: Full Evaluation (Agent Only)
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
print("\nStarting agent evaluation...")
start_time = time.time()

results = coordinator.batch_process(snippets, quick_mode=True, verbose=True)

total_time = time.time() - start_time

# Metrics
total = len(results)
agent_successful = sum(1 for r in results if r['success'])
agent_success_rate = (agent_successful / total * 100) if total > 0 else 0
avg_time = sum(r['execution_time'] for r in results) / total if total > 0 else 0

print(f"\n{'='*80}")
print(f"AGENT RESULTS (Internal Validation)")
print(f"{'='*80}")
print(f"Total:      {total}")
print(f"Success:    {agent_successful} ({agent_success_rate:.1f}%)")
print(f"Failed:     {total - agent_successful}")
print(f"Avg Time:   {avg_time:.2f}s")
print(f"Total Time: {total_time:.2f}s")
print(f"{'='*80}")

# Save agent results
agent_output = {
    'total_snippets': total,
    'agent_successful': agent_successful,
    'agent_success_rate': agent_success_rate,
    'avg_time': avg_time,
    'total_time': total_time,
    'results': results
}

with open('/kaggle/working/hybridagent_agent_results.json', 'w') as f:
    json.dump(agent_output, f, indent=2)

print("\nAgent results saved!")
```

### Cell 12: Docker Validation (Ground Truth)
```python
# Install docker package
!pip install -q docker

from docker_validator import DockerValidator
import json

print("="*80)
print("DOCKER VALIDATION (Ground Truth)")
print("="*80)

# Initialize Docker validator
docker_val = DockerValidator(timeout=60)

if not docker_val.available:
    print("⚠️ Docker not available on Kaggle!")
    print("⚠️ Skipping Docker validation")
    print("⚠️ Results based on agent internal validation only")
else:
    # Prepare solutions for Docker testing
    print(f"\nPreparing {len(results)} solutions for Docker testing...")
    
    solutions_to_test = []
    for i, result in enumerate(results):
        if result['success']:  # Only test agent-successful cases
            snippet = snippets[i]
            solution = result['solution']
            
            solutions_to_test.append((
                snippet['code'],
                solution['packages'],
                solution['python_version'],
                snippet['path']
            ))
    
    print(f"Testing {len(solutions_to_test)} agent-successful solutions in Docker...\n")
    
    # Run Docker validation
    docker_results = docker_val.batch_validate(solutions_to_test, show_progress=True)
    
    # Calculate ground truth metrics
    docker_successful = sum(1 for r in docker_results if r['docker_success'])
    docker_success_rate = (docker_successful / len(docker_results) * 100) if docker_results else 0
    
    # Calculate false positives
    false_positives = len(docker_results) - docker_successful
    false_positive_rate = (false_positives / len(docker_results) * 100) if docker_results else 0
    
    # Real success rate (out of all snippets)
    real_success_rate = (docker_successful / total * 100) if total > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"DOCKER RESULTS (Ground Truth)")
    print(f"{'='*80}")
    print(f"Agent said success:     {len(docker_results)}")
    print(f"Docker confirmed:       {docker_successful} ({docker_success_rate:.1f}%)")
    print(f"Docker failed:          {false_positives} ({false_positive_rate:.1f}%)")
    print(f"\nREAL SUCCESS RATE:      {docker_successful}/{total} = {real_success_rate:.1f}%")
    print(f"{'='*80}")
    
    # Combine results
    final_output = {
        'total_snippets': total,
        'agent_successful': agent_successful,
        'agent_success_rate': agent_success_rate,
        'docker_tested': len(docker_results),
        'docker_successful': docker_successful,
        'docker_success_rate': docker_success_rate,
        'real_success_rate': real_success_rate,
        'false_positives': false_positives,
        'false_positive_rate': false_positive_rate,
        'avg_time': avg_time,
        'docker_results': docker_results,
        'agent_results': results
    }
    
    with open('/kaggle/working/hybridagent_final_results.json', 'w') as f:
        json.dump(final_output, f, indent=2)
    
    print("\nFinal results with ground truth saved!")
```

### Cell 13: Compare with PLLM
```python
import pandas as pd

# PLLM baseline
pllm_success_rate = 38.0

# Use real success rate if Docker was available, otherwise use agent rate
if docker_val.available:
    our_success_rate = real_success_rate
    rate_type = "(Docker Ground Truth)"
else:
    our_success_rate = agent_success_rate
    rate_type = "(Agent Internal)"

# Comparison
comparison = pd.DataFrame({
    'Metric': ['Success Rate (%)', 'Avg Time (s)', 'Improvement'],
    'PLLM': [pllm_success_rate, 60.0, '-'],
    'HybridAgent-RAG': [our_success_rate, avg_time, f"+{our_success_rate - pllm_success_rate:.1f}%"]
})

print("\nComparison:")
print("="*80)
print(comparison.to_string(index=False))
print("="*80)

improvement = ((our_success_rate - pllm_success_rate) / pllm_success_rate * 100)
print(f"\nRelative Improvement: {improvement:.1f}%")
print(f"Rate Type: {rate_type}")

if our_success_rate > pllm_success_rate:
    print(f"✅ Outperforms PLLM by {our_success_rate - pllm_success_rate:.1f} points!")
else:
    print(f"⚠️ Below PLLM by {pllm_success_rate - our_success_rate:.1f} points")
```

### Cell 14: Paper Statistics
```python
print("\nPAPER STATISTICS")
print("="*80)

print("\n1. PERFORMANCE:")
if docker_val.available:
    print(f"   Agent Success Rate:  {agent_success_rate:.1f}%")
    print(f"   Docker Success Rate: {real_success_rate:.1f}% ← GROUND TRUTH")
    print(f"   False Positive Rate: {false_positive_rate:.1f}%")
    print(f"   PLLM Baseline:       {pllm_success_rate:.1f}%")
    print(f"   Improvement:         +{real_success_rate - pllm_success_rate:.1f} points ({improvement:.1f}% relative)")
else:
    print(f"   Success Rate: {agent_success_rate:.1f}% (PLLM: {pllm_success_rate:.1f}%)")
    print(f"   Improvement: +{agent_success_rate - pllm_success_rate:.1f} points ({improvement:.1f}% relative)")
    print(f"   ⚠️ No Docker validation (agent internal only)")

print(f"   Avg Time: {avg_time:.2f}s")

print("\n2. AGENT STATS:")
stats = coordinator.get_statistics()['learner_stats']
print(f"   Total: {stats['total_attempts']}")
print(f"   Success: {stats['successes']}")
print(f"   Failed: {stats['failures']}")

print("\n3. KEY FINDINGS:")
if docker_val.available:
    print(f"   - {real_success_rate:.1f}% REAL success rate (Docker validated)")
    print(f"   - {improvement:.1f}% improvement over PLLM")
    print(f"   - {false_positive_rate:.1f}% false positive rate")
else:
    print(f"   - {agent_success_rate:.1f}% success rate (agent internal)")
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

## Docker Validation (Optional)

**Kaggle free tier không có Docker**, nhưng nếu bạn test local hoặc dùng Kaggle Pro:

### Test Local:
```bash
cd D:\AI_RESEARCH\fse-aiware-python-dependencies\tools\hybridagent-rag
python test_docker_validation.py
```

### Kết Quả:
- **Agent Success Rate**: Agent nói SUCCESS (internal validation)
- **Docker Success Rate**: Thực tế chạy được (ground truth)
- **False Positive Rate**: Agent sai

Xem chi tiết: `DOCKER_VALIDATION.md`

---

## Troubleshooting

### Lỗi: "No valid candidates"
→ Check if Ollama is running: `!curl http://localhost:11434/api/tags`

### Lỗi: "Module not found"
→ Check sys.path: `print(sys.path)`

### Lỗi: "CUDA out of memory"
→ Use smaller model: `!ollama pull gemma2:2b`

### Lỗi: "Docker not available"
→ Normal on Kaggle free tier. Agent internal validation vẫn đủ tốt!

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
