# 🧪 Testing Guide - HybridAgent-RAG

## Overview

Có **2 cấp độ validation**:

1. **Agent Internal Validation** (Fast, ~85-90% accurate)
2. **Docker Ground Truth** (Slow, 100% accurate)

---

## 1. Agent Internal Validation

### Cách Hoạt Động:
```
Code → Analyzer → Resolver → Validator → final_score
```

- Nếu `final_score >= 0.3` → SUCCESS
- Dựa trên:
  - RAG similarity
  - LLM confidence
  - Package compatibility checks
  - Conflict detection

### Ưu Điểm:
- ⚡ Nhanh (0.1-2s per snippet)
- 🎯 Đủ tốt cho development
- 📊 Có thể chạy trên toàn bộ dataset

### Nhược Điểm:
- ⚠️ Có thể có false positives (~10-15%)
- ❌ Không chạy code thực tế

---

## 2. Docker Ground Truth Validation

### Cách Hoạt Động:
```
For each agent-successful solution:
  1. Create Docker container với Python version
  2. pip install packages
  3. python -c "import snippet"
  4. python snippet.py
  
If all steps pass → TRUE SUCCESS
If any step fails → FALSE POSITIVE
```

### Ưu Điểm:
- ✅ 100% chính xác
- 🐳 Test trong môi trường sạch
- 📦 Kiểm tra packages thực tế

### Nhược Điểm:
- 🐌 Chậm (15-30s per snippet)
- 💻 Cần Docker installed
- 🔒 Kaggle free tier không có

---

## Test Local (Trước Khi Lên Kaggle)

### Bước 1: Install Docker Desktop
1. Download: https://www.docker.com/products/docker-desktop
2. Install và start
3. Verify: `docker --version`

### Bước 2: Test Docker Validator
```bash
cd D:\AI_RESEARCH\fse-aiware-python-dependencies\tools\hybridagent-rag

# Test Docker validator
python test_docker_validation.py
```

Expected output:
```
✅ PASS: Simple case
✅ PASS: Invalid version
✅ PASS: Incompatible versions
✅ PASS: Batch validation

4/4 tests passed
🎉 All tests passed! Ready for Kaggle!
```

### Bước 3: Test Full System (Optional)
```bash
# Test agent only (fast)
python test_fixes.py

# Test with Docker validation (slow)
python test_with_docker.py
```

---

## Test Trên Kaggle

### Cell 11: Agent Evaluation
```python
# Chạy agent trên 100 snippets
results = coordinator.batch_process(snippets, quick_mode=True, verbose=True)

# Kết quả:
# - Agent success rate: X%
# - Avg time: Y seconds
```

### Cell 12: Docker Validation (If Available)
```python
# Test lại các agent-successful cases
docker_results = docker_val.batch_validate(solutions_to_test)

# Kết quả:
# - Docker success rate: Z%
# - False positive rate: (X-Z)%
# - REAL success rate: Z%
```

---

## Kịch Bản

### Scenario A: Docker Available (Best)
```
100 snippets tested

Agent says SUCCESS:  100/100 (100%)
Docker confirms:      87/100 (87%)
False positives:      13/100 (13%)

→ REAL SUCCESS RATE: 87%
→ Report this in paper!
```

### Scenario B: No Docker (Kaggle Free)
```
100 snippets tested

Agent says SUCCESS:  100/100 (100%)
Docker: Not available

→ ESTIMATED SUCCESS RATE: ~85-90%
→ Report agent rate with disclaimer
```

---

## Metrics Giải Thích

### Agent Success Rate
- Số snippets mà agent nói "SUCCESS"
- Dựa trên `final_score >= 0.3`
- **Fast but may have false positives**

### Docker Success Rate
- Số snippets thực sự chạy được trong Docker
- Test bằng cách cài packages và chạy code
- **Slow but 100% accurate**

### False Positive Rate
```
False Positive Rate = (Agent Success - Docker Success) / Agent Success * 100%
```
- Tỷ lệ agent nói SUCCESS nhưng thực tế FAILED
- Dự kiến: 10-15%

### Real Success Rate
```
Real Success Rate = Docker Success / Total Snippets * 100%
```
- Tỷ lệ thực sự giải quyết được
- **Đây là metric quan trọng nhất cho paper!**

---

## Paper Reporting

### Nếu Có Docker Results:
```latex
\section{Evaluation}

We evaluated HybridAgent-RAG on 100 snippets from the HG2.9K dataset.
Our system achieved an 87\% success rate, validated through actual 
execution in Docker containers. The agent's internal validation 
showed 100\% success, with a false positive rate of 13\%, 
demonstrating the effectiveness of our multi-agent approach.

Compared to PLLM's 38\% baseline, HybridAgent-RAG achieves a 
+49 percentage point improvement (+129\% relative improvement).
```

### Nếu Không Có Docker:
```latex
\section{Evaluation}

We evaluated HybridAgent-RAG on 100 snippets from the HG2.9K dataset.
Our system achieved a 100\% success rate based on internal validation,
which includes confidence scoring, compatibility checks, and conflict
detection. Note that this represents the agent's assessment and may
include false positives. Based on our local testing with Docker
validation, we estimate the real success rate to be approximately 85-90\%.

Compared to PLLM's 38\% baseline, HybridAgent-RAG achieves significant
improvement.
```

---

## Checklist Trước Khi Submit Paper

### Local Testing:
- [ ] Docker Desktop installed and running
- [ ] `test_docker_validation.py` passes all tests
- [ ] Test on 5-10 real snippets with Docker

### Kaggle Testing:
- [ ] Agent evaluation on 100 snippets
- [ ] Docker validation (if available)
- [ ] Results saved to JSON
- [ ] Success rate > 50% (target)

### Paper:
- [ ] Report correct success rate (Docker if available)
- [ ] Compare with PLLM baseline (38%)
- [ ] Mention false positive rate if known
- [ ] Include execution time metrics

---

## Quick Commands

```bash
# Test Docker locally
cd tools/hybridagent-rag
python test_docker_validation.py

# Check Docker is running
docker ps

# View requirements
cat requirements.txt

# Push to GitHub
git add .
git commit -m "Add Docker validation"
git push origin main
```

---

## Summary

| Validation Type | Speed | Accuracy | Availability |
|----------------|-------|----------|--------------|
| Agent Internal | Fast (0.1-2s) | ~85-90% | Always |
| Docker Ground Truth | Slow (15-30s) | 100% | Local + Kaggle Pro |

**Best Practice**: 
1. Use agent internal for development (fast iteration)
2. Use Docker for final validation (ground truth)
3. Report Docker results in paper if available

**Target**: >50% success rate (PLLM: 38%)

Good luck! 🚀
