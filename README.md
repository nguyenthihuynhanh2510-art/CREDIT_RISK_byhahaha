# 🏦 SmartCredit AI - Cổng Quản Trị Rủi Ro Tín Dụng & Thẩm Định Đa Mô Hình (Triple-Model Risk Portal)

Hệ thống thẩm định và ra quyết định cấp tín dụng bán lẻ tự động tuân thủ chuẩn mực **Basel II Trụ cột 1 & 2**, **IFRS 9**, và quy đổi sang **Thẻ điểm FICO Scorecard**.

Được xây dựng đồng bộ 100% với Đồ án Tốt nghiệp / Tiểu luận Khoa học Dữ liệu Ứng dụng: *"Xây dựng Hệ thống Chấm điểm Tín dụng Đa tầng và Tối ưu hóa Chính sách Phê duyệt 3 Vùng Đa Sản phẩm theo 3 Bối cảnh Kinh tế Chuẩn Basel II"*.

---

## 🌟 Các Tính Năng & Kiến Trúc Nổi Bật

1. **Bộ 12 Đặc Trưng Đầu Vào & Tiền Xử Lý Chuẩn Mực (Ý tưởng 2):**
   - Tích hợp cờ phân loại rủi ro `Has_Code_96_98` (mã lỗi hệ thống CIC 96/98).
   - Tái lập Thu nhập và `DebtRatio` bằng mô hình hồi quy Ridge hai giai đoạn (**Two-Stage Predictive Imputation**).
   - Đảm bảo chống rò rỉ dữ liệu (**Zero Data Leakage**) 100% giữa tập Train và Test.

2. **Hệ Thống 3 Thế Hệ Mô Hình Học Máy Nâng Cấp:**
   - 🌲 **Cây Quyết Định (Decision Tree - 86 Lá):** Cung cấp bộ quy tắc bạch diện `IF...THEN` minh bạch 100%, kiểm định thống kê khoảng tin cậy Wilson 95%, đóng vai trò *Cẩm nang Tác nghiệp Vùng Xám*.
   - 📈 **Hồi Quy Logistic (Logistic Regression):** Chuẩn mực truyền thống với các hệ số log-odds liên tục, đóng vai trò *Trụ cột Pháp lý & Tính Vốn Tối thiểu (Basel II Pillar 1 & 2 / ICAAP)*.
   - 🚀 **Monotonic XGBoost:** Tối ưu hóa phân tách nợ xấu với ràng buộc đơn điệu và giải trình Tree SHAP, đóng vai trò *Động cơ Phê duyệt Siêu tốc Kênh Số (Digital Lending)*.

3. **Chính Sách Phê Duyệt 3 Vùng (3-Zone Risk Policy) & Hạch Toán P&L Vi Mô:**
   - 🟢 **Vùng Xanh (Duyệt Tự Động):** Cấp 100% hạn mức ($EAD_{\text{std}} = 100$ tr VNĐ). Lãi suất $r=14\%$, chi phí vốn $c=4\%$, tổn thất $LGD=75\%$.
   - 🟡 **Vùng Xám (Tái Thẩm Định Có Điều Kiện):** Cấp 70% hạn mức ($EAD_{\text{grey}} = 70$ tr VNĐ), bổ sung TSBĐ giúp hạ $LGD=35\%$, biên lãi suất rủi ro $r=17\%$ ($r-c=13\%$). Giải cứu hàng nghìn khách hàng tốt, tăng trưởng lợi nhuận ròng từ **+13.46% đến +26.30%**.
   - 🔴 **Vùng Đỏ (Từ Chối Cấp Tín Dụng):** $PD > 20\%$, bảo toàn vốn, ngăn chặn rủi ro tổn thất.

4. **Tờ Trình Thẩm Định Tín Dụng Chuẩn Ngân Hàng (Xuất PDF A4 Trắng - Đen):**
   - Kết xuất file PDF A4 chứa đầy đủ thông tin khách hàng, phân rã thu nhập, danh sách 12 đặc trưng Basel II, kết quả đối sánh 3 mô hình và chữ ký 3 cấp thẩm quyền.

---

## 👥 Tài Khoản Demo (Phân Quyền RBAC):

- **Chuyên viên Tín dụng (Loan Officer):** `officer` / `123` *(Chấm điểm tức thì & In tờ trình thẩm định)*
- **Trưởng phòng Thẩm định (Credit Manager):** `manager` / `123` *(Thêm quyền Chấm điểm danh mục lô Batch)*
- **Giám đốc Quản lý Rủi ro (CRO Admin):** `cro_admin` / `123` *(Toàn quyền truy cập cả 4 Tab bao gồm Điều hành Chính sách & Kiểm toán Basel II)*

*(Màn hình đăng nhập có sẵn 3 nút Đăng nhập Nhanh 1-Chạm thuận tiện cho việc thuyết minh)*

---

## 💻 Hướng Dẫn Thao Tác & Khởi Chạy Website

### 1. Khởi chạy Cục bộ (Local Run)
Mở PowerShell hoặc Terminal tại thư mục `streamlit_deploy`:
```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Khởi chạy ứng dụng Streamlit
streamlit run app.py
```
Ứng dụng sẽ tự động mở tại địa chỉ: `http://localhost:8501`.

### 2. Thao Tác Sửa & Cập Nhật Giao Diện / Thuật Toán
- **Sửa giao diện & logic thẩm định:** Mở file `app.py`.
  - Dòng ~545: Danh sách biến đầu vào `FEATURE_COLS`.
  - Dòng ~760 - ~1060: Các hàm chấm điểm 3 mô hình `score_single_customer_dt`, `score_single_customer_lr`, `score_single_customer_xgb`.
  - Dòng ~1070: Hàm kết xuất Báo cáo PDF ReportLab `generate_bw_credit_appraisal_pdf`.
  - Dòng ~1500: Thiết lập hồ sơ mẫu (Presets).
  - Dòng ~2380: Tab 2 Chấm điểm danh mục lô (Batch).
  - Dòng ~2460: Tab 3 Trung tâm điều hành chính sách (CRO).
  - Dòng ~2550: Tab 4 Báo cáo kiểm toán Basel II Trụ cột 2.
- **Sửa tham số tiền xử lý dữ liệu:** Chỉnh sửa file `preprocessing_params.json` hoặc thuật toán trong `preprocessing.py`.
- **Cập nhật mô hình mới:** Đặt tệp `.pkl` vào thư mục `models/` (và copy 1 bản ở thư mục gốc nếu deploy Cloud).

### 3. Đồng Bộ Lên Streamlit Cloud
Để cập nhật website trên Streamlit Cloud (`https://creditriskbyhahaha-evsncefm6etthmowbqj9bc.streamlit.app/`):
1. Đẩy các file đã cập nhật trong thư mục `streamlit_deploy` lên repository GitHub kết nối với Streamlit Cloud.
2. Streamlit Cloud sẽ tự động phát hiện commit mới và tiến hành auto-reload trong vòng 1-2 phút.
