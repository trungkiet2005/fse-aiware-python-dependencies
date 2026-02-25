# 🚀 Kaggle Setup Guide - FSE 2026 AIWare Competition

## Hướng dẫn chi tiết setup Ollama trên Kaggle với H100 80GB

---

## ✅ Về tính hợp lệ của submission

**CÓ, hoàn toàn hợp lệ!** 

- Kaggle chỉ là môi trường development
- Submission cuối cùng là Docker container độc lập
- BTC sẽ chạy tool của bạn trên held-out dataset của họ

**Yêu cầu submission**:
- ✅ Đóng gói trong Docker container
- ✅ Chạy standalone (không phụ thuộc Kaggle)
- ✅ Model phải fit trong 10GB VRAM

---

## 📝 Kaggle Notebook Template - Copy & Paste từng cell

### Cell 1: Markdown - Header

```markdown
# FSE 2026 AIWare - Python Dependency Resolution Competition
## Kaggle Development Template with Ollama

**Competition**: Agentic-based Python Dependency Resolution

**Requirements**:
- GPU: H100 80GB (or T4 16GB minimum)
- VRAM Constraint: 10GB for final submission
- Dataset: HG2.9K (2,900+ Python files)

**Kaggle Settings Required**:
- ✅ GPU: ON (Select H100 if available)
- ✅ Internet: ON
- ✅ Persistence: ON (optional, for faster reruns)

**Deadline**: March 6, 2026 (AoE)
```

---

### Cell 2: Markdown

```markdown
---
## 📋 Step 1: System Setup & GPU Check
```

---

### Cell 3: Python - Check GPU

```python
# Check GPU availability
!nvidia-smi

import torch
print(f"\n🔥 PyTorch CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"📊 GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"💾 Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"✅ CUDA Version: {torch.version.cuda}")
```

---

### Cell 4: Markdown

```markdown
---
## 🔧 Step 2: Install Ollama
```

---

### Cell 5: Python - Install Ollama

```python
%%bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

---

### Cell 6: Markdown

```markdown
---
## 🚀 Step 3: Start Ollama Server
```

---

### Cell 7: Python - Start Ollama

```python
import subprocess
import time
import os
import requests

# Set environment variables
os.environ['OLLAMA_HOST'] = '0.0.0.0:11434'
os.environ['OLLAMA_ORIGINS'] = '*'

# Start Ollama server in background
print("🔄 Starting Ollama server...")
ollama_process = subprocess.Popen(
    ['ollama', 'serve'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=os.environ
)

# Wait for server to start
time.sleep(10)

# Test connection
try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        print("✅ Ollama server is running!")
        print(f"📡 Server URL: http://localhost:11434")
    else:
        print(f"⚠️ Server responded with status: {response.status_code}")
except Exception as e:
    print(f"❌ Error connecting to Ollama: {e}")
    print("Retrying in 5 seconds...")
    time.sleep(5)
```

---

### Cell 8: Markdown

```markdown
---
## 📥 Step 4: Download LLM Models

**Models that fit in 10GB VRAM**:
- `gemma2:2b` (~1.6GB) - Fastest, good for testing
- `gemma2` (9B) (~5.5GB) - Baseline model
- `llama3.1:8b` (~4.7GB) - Good alternative
- `qwen2.5:7b` (~4.7GB) - Strong reasoning
- `mistral` (7B) (~4.1GB) - Fast and efficient
```

---

### Cell 9: Python - Download Models

```python
# Pull baseline model (gemma2)
print("📥 Downloading gemma2 model (baseline)...")
!ollama pull gemma2

# Optional: Pull additional models for comparison
# !ollama pull llama3.1:8b
# !ollama pull qwen2.5:7b
# !ollama pull mistral

# List available models
print("\n📋 Available models:")
!ollama list
```

---

### Cell 10: Markdown

```markdown
---
## 🧪 Step 5: Test Ollama API
```

---

### Cell 11: Python - Test Ollama

```python
import requests
import json

def test_ollama_generation(model="gemma2", prompt="Hello! Can you help me resolve Python dependencies?"):
    """
    Test Ollama API with a simple prompt
    """
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 100
        }
    }
    
    print(f"🤖 Testing {model}...")
    print(f"📝 Prompt: {prompt}\n")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {result['response']}")
            print(f"\n⏱️ Total duration: {result.get('total_duration', 0) / 1e9:.2f}s")
            print(f"🔢 Tokens generated: {result.get('eval_count', 0)}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# Run test
test_ollama_generation()
```

---

### Cell 12: Markdown

```markdown
---
## 📦 Step 6: Clone Competition Repository
```

---

### Cell 13: Python - Clone Repo

```python
import os

# Clone repository
if not os.path.exists('/kaggle/working/fse-aiware-python-dependencies'):
    print("📥 Cloning competition repository...")
    !git clone https://github.com/checkdgt/fse-aiware-python-dependencies.git /kaggle/working/fse-aiware-python-dependencies
else:
    print("✅ Repository already exists")

# Change to repo directory
%cd /kaggle/working/fse-aiware-python-dependencies

# List contents
!ls -la
```

---

### Cell 14: Markdown

```markdown
---
## 📂 Step 7: Extract Dataset (HG2.9K)
```

---

### Cell 15: Python - Extract Dataset

```python
import os
import tarfile

# Check if dataset exists
if os.path.exists('hard-gists.tar.gz'):
    if not os.path.exists('hard-gists'):
        print("📦 Extracting hard-gists dataset...")
        !tar -xzf hard-gists.tar.gz
        print("✅ Dataset extracted!")
    else:
        print("✅ Dataset already extracted")
    
    # Count snippets
    snippet_count = !find hard-gists -name "snippet.py" | wc -l
    print(f"\n📊 Total snippets found: {snippet_count[0]}")
    
    # Show sample structure
    print("\n📁 Sample directory structure:")
    !ls -la hard-gists | head -10
else:
    print("❌ hard-gists.tar.gz not found!")
    print("Please upload the dataset to Kaggle or download it separately.")
```

---

### Cell 16: Markdown

```markdown
---
## 🔍 Step 8: Explore Sample Snippet
```

---

### Cell 17: Python - View Sample

```python
import os
import glob

# Find first snippet
snippets = glob.glob('hard-gists/*/snippet.py')

if snippets:
    sample_snippet = snippets[0]
    print(f"📄 Sample snippet: {sample_snippet}\n")
    print("=" * 80)
    
    with open(sample_snippet, 'r') as f:
        content = f.read()
        print(content)
    
    print("=" * 80)
    print(f"\n📏 File size: {len(content)} characters")
    print(f"📝 Lines: {len(content.splitlines())}")
else:
    print("❌ No snippets found!")
```

---

### Cell 18: Markdown

```markdown
---
## 🎯 Step 9: Create Your Custom Agent (Template)

This is where you develop your innovative approach!
```

---

### Cell 19: Python - Agent Class

```python
import requests
import json
import re
from typing import Dict, List, Optional

class DependencyResolver:
    """
    Custom Agentic-based Python Dependency Resolver
    
    TODO: Implement your innovative approach here!
    Ideas:
    - Multi-agent system
    - RAG with vector database
    - Graph-based dependency analysis
    - Few-shot learning
    - Error log analysis with feedback loop
    """
    
    def __init__(self, model: str = "gemma2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def extract_imports(self, code: str) -> List[str]:
        """
        Extract import statements from Python code
        """
        import_pattern = r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
        imports = []
        
        for line in code.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1) or match.group(2)
                imports.append(module.split('.')[0])
        
        return list(set(imports))
    
    def query_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Query Ollama LLM
        """
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 500
            }
        }
        
        try:
            response = requests.post(self.api_url, json=data, timeout=120)
            if response.status_code == 200:
                return response.json()['response']
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Exception: {str(e)}"
    
    def analyze_dependencies(self, code: str) -> Dict:
        """
        Analyze code and suggest dependency versions
        """
        imports = self.extract_imports(code)
        
        prompt = f"""
You are a Python dependency expert. Analyze the following Python code and suggest compatible package versions.

Code imports:
{', '.join(imports)}

Code snippet:
```python
{code[:500]}  # First 500 chars
```

Please provide:
1. Recommended Python version (e.g., 3.8, 3.9, 3.10)
2. Package versions for each import
3. Any potential conflicts

Format your response as:
Python: X.Y
Packages:
- package_name==version
- ...
"""
        
        response = self.query_llm(prompt)
        
        return {
            'imports': imports,
            'llm_response': response,
            'code_length': len(code)
        }
    
    def resolve_snippet(self, snippet_path: str, max_iterations: int = 10) -> Dict:
        """
        Main resolution function
        
        TODO: Implement your full resolution pipeline here!
        """
        print(f"\n🔍 Resolving: {snippet_path}")
        
        # Read snippet
        with open(snippet_path, 'r') as f:
            code = f.read()
        
        # Analyze
        analysis = self.analyze_dependencies(code)
        
        print(f"\n📦 Found imports: {', '.join(analysis['imports'])}")
        print(f"\n🤖 LLM Analysis:\n{analysis['llm_response']}")
        
        return analysis

# Initialize resolver
resolver = DependencyResolver(model="gemma2")
print("✅ DependencyResolver initialized!")
```

---

### Cell 20: Markdown

```markdown
---
## 🧪 Step 10: Test Your Agent on Sample Snippets
```

---

### Cell 21: Python - Test Agent

```python
import glob
import time

# Get sample snippets (test on 3 snippets)
snippets = glob.glob('/kaggle/working/fse-aiware-python-dependencies/hard-gists/*/snippet.py')[:3]

print(f"🧪 Testing on {len(snippets)} snippets...\n")
print("=" * 80)

results = []

for i, snippet in enumerate(snippets, 1):
    print(f"\n[{i}/{len(snippets)}] Testing: {snippet}")
    
    start_time = time.time()
    
    try:
        result = resolver.resolve_snippet(snippet)
        result['status'] = 'success'
        result['time'] = time.time() - start_time
        results.append(result)
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append({
            'status': 'error',
            'error': str(e),
            'time': time.time() - start_time
        })
    
    print("\n" + "=" * 80)

# Summary
print("\n📊 Test Summary:")
print(f"Total snippets: {len(results)}")
print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
print(f"Failed: {sum(1 for r in results if r['status'] == 'error')}")
print(f"Average time: {sum(r['time'] for r in results) / len(results):.2f}s")
```

---

### Cell 22: Markdown

```markdown
---
## 💾 Step 11: Save Results
```

---

### Cell 23: Python - Save Results

```python
import json
from datetime import datetime

def save_results(results, output_dir='/kaggle/working/results'):
    """
    Save results to JSON files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save detailed results
    results_file = f"{output_dir}/results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to: {results_file}")
    
    return results_file

# Save if you have results
# save_results(results)
```

---

### Cell 24: Markdown

```markdown
---
## 🐳 Step 12: Docker Submission Template

After developing on Kaggle, you'll need to package as Docker for submission.
```

---

### Cell 25: Python - Create Submission Template

```python
# Create submission template files
submission_dir = '/kaggle/working/my_submission'
os.makedirs(submission_dir, exist_ok=True)

# Dockerfile
dockerfile_content = """FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Ollama port
EXPOSE 11434

# Start script
CMD ["bash", "start.sh"]
"""

with open(f"{submission_dir}/Dockerfile", 'w') as f:
    f.write(dockerfile_content)

# requirements.txt
requirements_content = """requests==2.31.0
python-dotenv==1.0.0
tqdm==4.66.1
"""

with open(f"{submission_dir}/requirements.txt", 'w') as f:
    f.write(requirements_content)

# start.sh
start_script = """#!/bin/bash

# Start Ollama server
ollama serve &
sleep 10

# Pull model
ollama pull gemma2

# Run your tool
python main.py "$@"
"""

with open(f"{submission_dir}/start.sh", 'w') as f:
    f.write(start_script)

# README for submission
readme_content = """# My FSE 2026 AIWare Submission

## Build & Run

```bash
# Build Docker image
docker build -t my-dependency-resolver .

# Run on single snippet
docker run -v /path/to/snippets:/snippets my-dependency-resolver -f /snippets/snippet.py

# Run on folder
docker run -v /path/to/snippets:/snippets my-dependency-resolver -d /snippets
```

## Approach

TODO: Describe your innovative approach here!

## Requirements

- VRAM: < 10GB
- Model: gemma2 (or specify your model)
"""

with open(f"{submission_dir}/README.md", 'w') as f:
    f.write(readme_content)

print(f"✅ Submission template created in: {submission_dir}")
print("\n📁 Files created:")
!ls -la {submission_dir}
```

---

### Cell 26: Markdown

```markdown
---
## 📝 Development Notes & Next Steps

## 🎯 Your Development Roadmap:

### Phase 1: Understanding (Current)
- ✅ Setup Ollama on Kaggle
- ✅ Load and explore HG2.9K dataset
- ✅ Test baseline PLLM approach
- ✅ Create basic agent template

### Phase 2: Innovation (Your Work)
- [ ] Implement advanced RAG pipeline
- [ ] Add multi-agent coordination
- [ ] Build error feedback loop
- [ ] Optimize for 10GB VRAM constraint
- [ ] Test on full dataset

### Phase 3: Evaluation
- [ ] Benchmark against PLLM baseline
- [ ] Measure success rate, time, resources
- [ ] Document approach for paper

### Phase 4: Submission
- [ ] Package as Docker container
- [ ] Test Docker locally
- [ ] Fork competition repo
- [ ] Submit PR or email to organizers
- [ ] Write 4-page paper

## 💡 Innovation Ideas:

1. **Multi-Agent System**:
   - Analyzer agent: Extract dependencies
   - Resolver agent: Find compatible versions
   - Validator agent: Test solutions
   - Coordinator: Orchestrate workflow

2. **Advanced RAG**:
   - Build vector DB of PyPI metadata
   - Index successful resolutions
   - Semantic search for similar conflicts

3. **Graph-Based Analysis**:
   - Model dependency graph
   - Find conflict paths
   - Suggest minimal changes

4. **Few-Shot Learning**:
   - Use PLLM results as training examples
   - Fine-tune prompts with successful cases

5. **Error Feedback Loop**:
   - Parse error logs
   - Learn from failures
   - Iterative refinement

## 📚 Resources:

- Original paper: Bartlett et al. 2025 - https://arxiv.org/abs/2501.16191
- Dataset paper: Horton & Parnin 2018 - https://arxiv.org/abs/1808.04919
- Competition repo: https://github.com/checkdgt/fse-aiware-python-dependencies
- Discussions: https://github.com/checkdgt/fse-aiware-python-dependencies/discussions

## 📧 Contact:

- Paper submission: a.j.bartlett@tudelft.nl
- Questions: Use GitHub Discussions

## ⏰ Important Dates:

- **Deadline**: March 6, 2026 (AoE)
- **Notification**: March 26, 2026
- **Camera-Ready**: April 2, 2026
- **Competition**: July 6, 2026

---

**Good luck with your submission! 🚀**
```

---

## 🎯 Cách sử dụng template này:

### Bước 1: Tạo Kaggle Notebook mới
1. Vào Kaggle.com
2. Click "New Notebook"
3. Settings:
   - **Accelerator**: GPU H100 (hoặc T4)
   - **Internet**: ON
   - **Persistence**: ON (optional)

### Bước 2: Copy & Paste từng cell
- Copy từng cell từ guide này
- Paste vào Kaggle notebook theo thứ tự
- Chọn đúng loại cell (Markdown hoặc Code)

### Bước 3: Run từng cell
- Chạy từ cell 1 đến hết
- Kiểm tra output của mỗi cell
- Fix lỗi nếu có

### Bước 4: Develop your solution
- Modify `DependencyResolver` class
- Implement your innovative approach
- Test on dataset

### Bước 5: Submit
- Package as Docker
- Fork competition repo
- Submit PR hoặc email

---

## 🚨 Lưu ý quan trọng:

### ✅ Hợp lệ:
- Develop trên Kaggle với H100
- Test với nhiều models
- Optimize trên full dataset
- Submit Docker container

### ⚠️ Yêu cầu submission:
- Tool phải chạy trong Docker
- Model phải fit trong 10GB VRAM
- Không phụ thuộc vào Kaggle environment
- Có thể chạy standalone

### 📧 Submission options:
1. **Public**: Fork repo → Create PR
2. **Private**: Zip tool → Email với paper

---

## 💪 Lợi thế của H100 80GB:

1. **Development**: Test nhiều models song song
2. **Speed**: Training/inference cực nhanh
3. **Experimentation**: Thử nhiều approaches
4. **Full dataset**: Chạy toàn bộ 2,900 snippets

Nhưng nhớ: **Final submission phải fit trong 10GB VRAM!**

---

## 🤝 Support:

Nếu gặp vấn đề:
1. Check GitHub Discussions
2. Email organizers: a.j.bartlett@tudelft.nl
3. Review baseline PLLM code

---

**Chúc bạn thành công trong cuộc thi! 🎉**
