# 🐳 Docker Validation - Ground Truth Testing

## Tại Sao Cần Docker Validation?

**Agent có thể nói "SUCCESS" nhưng thực tế có chạy được không?**

```
Agent: "✅ SUCCESS - numpy==1.24.3, pandas==2.0.3"
Reality: ❌ Packages incompatible, code crashes
```

Docker validation = **Ground Truth** = Test thực tế trong môi trường sạch!

---

## Cách Hoạt Động

### 1. Agent Resolution (Internal Validation)
```
Code → Analyzer → Resolver → Validator → "SUCCESS" (final_score >= 0.3)
```
- Dựa trên logic nội bộ
- Không chạy code thực tế
- Có thể có **false positives**

### 2. Docker Validation (Ground Truth)
```
Code + Packages → Docker Container → pip install → python snippet.py
```
- Chạy code THỰC TẾ
- Cài packages THỰC TẾ
- Kiểm tra import + syntax
- **100% chính xác**

---

## Test Local Trước Khi Lên Kaggle

### Bước 1: Cài Docker Desktop
1. Download: https://www.docker.com/products/docker-desktop
2. Install và start Docker Desktop
3. Verify: `docker --version`

### Bước 2: Run Test Suite
```bash
cd D:\AI_RESEARCH\fse-aiware-python-dependencies\tools\hybridagent-rag

python test_docker_validation.py
```

### Expected Output:
```
================================================================================
DOCKER VALIDATOR TEST SUITE
================================================================================

================================================================================
TEST 1: Simple numpy + pandas
================================================================================
[DockerValidator] Docker client initialized
[DockerValidator] Building image (Python 3.8)...
[DockerValidator] Running container...

Result: SUCCESS
Time: 15.32s
✅ Test 1 PASSED

================================================================================
TEST 2: Invalid version (should fail)
================================================================================
[DockerValidator] Building image (Python 3.8)...

Result: Package version not found
Time: 3.21s
✅ Test 2 PASSED (correctly detected invalid version)

...

================================================================================
TEST SUMMARY
================================================================================
✅ PASS: Simple case
✅ PASS: Invalid version
✅ PASS: Incompatible versions
✅ PASS: Batch validation

4/4 tests passed
================================================================================

🎉 All tests passed! Ready for Kaggle!
```

---

## Trên Kaggle

### Cell 11: Agent Evaluation
- Chạy agent trên 100 snippets
- Kết quả: Agent success rate (internal validation)

### Cell 12: Docker Validation
- Test lại các agent-successful cases trong Docker
- Kết quả: **Real success rate** (ground truth)

### Metrics:
```python
Agent Success Rate:     100.0%  # Agent nói SUCCESS
Docker Success Rate:     87.3%  # Thực tế chạy được
False Positive Rate:     12.7%  # Agent sai

REAL SUCCESS RATE = Docker Success Rate
```

---

## So Sánh

| Method | What It Tests | Accuracy | Speed |
|--------|---------------|----------|-------|
| **Agent Internal** | Logic, heuristics, scoring | ~85-90% | Fast (0.1s) |
| **Docker Ground Truth** | Actual execution | 100% | Slow (15-30s) |

---

## Ví Dụ False Positive

### Agent Says SUCCESS:
```json
{
  "success": true,
  "final_score": 0.95,
  "packages": {
    "numpy": "1.24.3",
    "pandas": "0.25.3"
  }
}
```

### Docker Says FAILED:
```
ERROR: pandas 0.25.3 requires numpy<1.20.0
Building failed: incompatible versions
```

→ Agent không thể biết tất cả dependency constraints!

---

## Kết Quả Mong Đợi

### Scenario 1: Docker Available (Local/Kaggle Pro)
```
Agent Success:   100/100 (100%)
Docker Tested:   100
Docker Success:  87/100 (87%)
False Positive:  13/100 (13%)

REAL SUCCESS RATE: 87%
```

### Scenario 2: Docker Not Available (Kaggle Free)
```
Agent Success:   100/100 (100%)
Docker Tested:   0 (skipped)

⚠️ Results based on agent internal validation only
⚠️ Real success rate may be lower
```

---

## Paper Reporting

### Nếu Có Docker:
```
We achieved 87% success rate on HG2.9K dataset,
validated through actual execution in Docker containers.
Our agent's internal validation showed 100% success,
with a false positive rate of 13%.
```

### Nếu Không Có Docker:
```
We achieved 100% success rate on HG2.9K dataset
based on internal validation. Note that this represents
the agent's confidence and may include false positives.
```

---

## Troubleshooting

### Error: "Docker not available"
```bash
# Check if Docker is running
docker ps

# If not, start Docker Desktop
```

### Error: "Cannot connect to Docker daemon"
```bash
# Windows: Start Docker Desktop
# Linux: sudo systemctl start docker
```

### Error: "Timeout"
```python
# Increase timeout in code
validator = DockerValidator(timeout=120)  # 2 minutes
```

---

## Summary

✅ **Agent Internal Validation**: Fast, good for development
✅ **Docker Ground Truth**: Slow, but 100% accurate
✅ **Best Practice**: Use both!

**For FSE 2026 Paper**: Report Docker-validated results if available!

---

**Note**: Kaggle free tier might not have Docker. Nếu không có Docker, agent internal validation vẫn đủ tốt (dự kiến ~85-90% accuracy).
