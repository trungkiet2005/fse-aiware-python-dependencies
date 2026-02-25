# 🚀 Hướng Dẫn Upload Notebook Lên Kaggle

## File Notebook Đã Tạo

✅ **HybridAgent_RAG_Complete.ipynb** - 20 cells hoàn chỉnh

## Bước 1: Upload Lên Kaggle

### Cách 1: Upload Trực Tiếp (Khuyến Nghị)

1. Truy cập: https://www.kaggle.com/code
2. Click **"New Notebook"**
3. Click **"File"** → **"Upload Notebook"**
4. Chọn file `HybridAgent_RAG_Complete.ipynb`
5. Đợi upload xong

### Cách 2: Copy-Paste Từng Cell

1. Tạo notebook mới trên Kaggle
2. Mở file `HybridAgent_RAG_Complete.ipynb` bằng text editor
3. Copy từng cell và paste vào Kaggle

## Bước 2: Cấu Hình Kaggle Notebook

### Settings Bắt Buộc:

1. **Accelerator**: 
   - Click **Settings** (góc phải)
   - Chọn **GPU T4** hoặc **GPU P100** (nếu có H100 thì tốt hơn)
   - Click **Save**

2. **Internet**: 
   - Bật **Internet ON** (để download Ollama và model)

3. **Persistence**:
   - Bật **Persistence ON** (để lưu ChromaDB và model)

## Bước 3: Chạy Notebook

### Chạy Từng Cell Theo Thứ Tự:

1. **Cell 1-4**: Setup môi trường (5-10 phút)
   - Install Ollama
   - Start Ollama server
   - Download model gemma2 (~5GB, mất 5-10 phút)

2. **Cell 5-8**: Clone repo và extract dataset (2-3 phút)

3. **Cell 9-14**: Tạo HybridAgent-RAG system (1 phút)

4. **Cell 15**: Test trên 5 snippets mẫu (2-3 phút)

5. **Cell 16-17**: Full evaluation (tùy MAX_SNIPPETS)
   - 100 snippets: ~15-20 phút
   - Full 2900 snippets: ~2-3 giờ

6. **Cell 18-19**: So sánh với PLLM và tạo statistics

## Bước 4: Lưu Kết Quả

Sau khi chạy xong:

1. **Download Results**:
   - File: `/kaggle/working/hybridagent_results.json`
   - Click vào file → Download

2. **Save Notebook**:
   - Click **Save Version**
   - Chọn **Save & Run All** (nếu muốn chạy lại toàn bộ)

## Bước 5: Sử Dụng Kết Quả Cho Paper

### Kết quả quan trọng:

```python
# Từ Cell 17
success_rate = X%  # Tỷ lệ thành công
avg_time = Y.YYs   # Thời gian trung bình

# Từ Cell 18
improvement = Z%   # So với PLLM baseline (38%)
```

### Đưa vào paper:

1. **Abstract**: 
   - "We achieve X% success rate, improving PLLM by Z%"

2. **Results Section**:
   - Table 1: Performance comparison
   - Figure 1: Success rate by complexity

3. **Discussion**:
   - Analyze why HybridAgent-RAG works better
   - Key innovations: Multi-agent + RAG + Graph

## Tips Quan Trọng

### ⚠️ Lưu Ý:

1. **Model Download**: 
   - gemma2 ~5GB, mất 5-10 phút
   - Nếu timeout, chạy lại cell download

2. **VRAM**:
   - gemma2 cần ~9GB VRAM
   - T4 (16GB) hoặc P100 (16GB) đều đủ
   - H100 (80GB) thì rất dư

3. **Time Limit**:
   - Kaggle free: 12 giờ/session
   - Đủ để chạy full evaluation

4. **Persistence**:
   - Bật để lưu model và ChromaDB
   - Lần sau không cần download lại

### 🔧 Troubleshooting:

**Lỗi: "Ollama not found"**
```bash
# Chạy lại cell install Ollama
!curl -fsSL https://ollama.com/install.sh | sh
```

**Lỗi: "Model not found"**
```bash
# Pull model lại
!ollama pull gemma2
```

**Lỗi: "Connection refused"**
```python
# Restart Ollama server
import subprocess
ollama_process = subprocess.Popen(['ollama', 'serve'])
time.sleep(10)
```

## Bước 6: Tối Ưu Hóa (Nếu Cần)

### Để tăng success rate:

1. **Tăng số lần retry**: 
   - Sửa `max_iterations=5` → `max_iterations=10` trong Cell 14

2. **Thêm training data vào RAG**:
   - Load PLLM successful cases
   - Add vào RAG system trước khi evaluate

3. **Fine-tune prompts**:
   - Sửa prompts trong `agents/*.py`
   - Test lại trên sample snippets

## Checklist Hoàn Thành

- [ ] Upload notebook lên Kaggle
- [ ] Cấu hình GPU + Internet + Persistence
- [ ] Chạy Cell 1-8: Setup environment
- [ ] Chạy Cell 9-14: Create system
- [ ] Chạy Cell 15: Test 5 samples
- [ ] Chạy Cell 17: Full evaluation (100 hoặc full)
- [ ] Chạy Cell 18-19: Compare & statistics
- [ ] Download `hybridagent_results.json`
- [ ] Sử dụng kết quả cho paper
- [ ] Viết paper trong `paper_fse/hybridagent_paper.tex`

## Liên Hệ & Support

Nếu gặp vấn đề:
1. Check Kaggle logs
2. Đọc error message
3. Google error + "Kaggle Ollama"
4. Check Ollama docs: https://ollama.com/

---

**Good luck with your FSE 2026 submission! 🎯**

Target: >50% success rate (vs PLLM 38%)
Deadline: March 6, 2026
