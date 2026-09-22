# MT5 Performance Analyzer

Công cụ phân tích hiệu suất giao dịch từ báo cáo export MT5 (Trade History Report),
tập trung vào chiến lược DCA (Dollar-Cost Averaging).

## Vấn đề giải quyết

MT5 tự tính sẵn các chỉ số thống kê (win rate, profit factor, drawdown...) trong báo cáo
export, nhưng các chỉ số này tính theo **từng lệnh riêng lẻ**. Với chiến lược DCA
(nhồi lệnh trung bình giá khi thị trường đi ngược hướng), một lần vào lệnh thực tế có thể
gồm nhiều lệnh (layer) liên tiếp — tính theo lệnh riêng lẻ sẽ cho ra bức tranh sai lệch
về hiệu suất thật của chiến lược. Công cụ này đọc lại báo cáo giao dịch thô, tự động
nhận diện và gộp các lệnh thuộc cùng một chuỗi DCA, để đánh giá đúng bản chất chiến lược
theo từng quyết định giao dịch thực sự, thay vì từng layer riêng lẻ.
     

## Insight chính

- **Tính theo lệnh riêng lẻ vs tính theo chuỗi cho ra 2 bức tranh khác hẳn nhau**: 83 lệnh
  riêng lẻ gộp thành 29 chuỗi giao dịch thực tế. Tỷ lệ thắng tính theo lệnh là 49/34
  (59%), nhưng tính đúng theo chuỗi (đơn vị quyết định thực tế của chiến lược DCA) là
  28/29 (96.6%) — cho thấy chiến lược gần như luôn đóng lệnh có lời nếu tính đủ một chu
  kỳ nhồi lệnh.

- **Cột "profit" trong báo cáo MT5 không bao gồm commission và swap.** Phải cộng thêm
  hai khoản này mới ra đúng lợi nhuận ròng thật — nếu bỏ qua, tổng lợi nhuận tính sai
  lệch tới ~50% so với số liệu MT5 tự báo cáo. Một chi tiết dễ bị bỏ sót nếu không đối
  chiếu chéo với số liệu gốc.

- **Đường cong lợi nhuận tích lũy (equity curve) có thể che giấu rủi ro thật.** Chuỗi
  DCA duy nhất bị lỗ trong dữ liệu chỉ đóng ở mức -17.37 USD, gần như không hiện rõ trên
  equity curve — nhưng phân tích drawdown theo từng chuỗi cho thấy nó từng tạm thời lỗ
  tới -234.37 USD (gấp 13 lần mức lỗ cuối cùng) trước khi thị trường đảo chiều. Đây là
  rủi ro tail risk tiềm ẩn mà các báo cáo trading tiêu chuẩn không thể hiện.

## Cấu trúc project

mt5-performance-analyzer/
├── src/
│ ├── ingest.py # Doc file HTML export MT5, parse bang Positions
│ ├── db.py # Luu du lieu vao SQLite
│ ├── analysis.py # Gom nhom theo chain DCA, tinh drawdown
│ ├── chart.py # Ve bieu do equity curve
│ └── config.py # Duong dan file tap trung
├── tests/
│ └── test_analysis.py
├── data/raw/ # File export MT5 goc (khong dua len Git)
└── README.md

## Cách chạy

```bash
pip install -r requirements.txt

# 1. Dat file export MT5 (.html) vao data/raw/
# 2. Chay pipeline theo thu tu:
python src/ingest.py
python src/db.py
python src/analysis.py
python src/chart.py

# Chay test
python -m pytest tests/
```

## Lưu ý về dữ liệu

Dữ liệu trong repo (nếu có) đã được ẩn danh / là dữ liệu mẫu. File export thật chứa
thông tin tài khoản cá nhân, không được commit lên Git (xem `.gitignore`).