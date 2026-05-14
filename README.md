# FIT Research Hub - Backend

Đây là backend API của hệ thống FIT Research Hub, được xây dựng trên nền tảng Flask (Python) và cơ sở dữ liệu PostgreSQL.

##  Yêu cầu hệ thống

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:
- **Python**: Phiên bản 3.8 trở lên.
- **PostgreSQL**: Đã cài đặt và đang chạy dịch vụ.

##  Hướng dẫn cài đặt và khởi chạy

Thực hiện các bước dưới đây để thiết lập và chạy dự án trên máy mới.

### 1. Mở thư mục dự án
Mở Terminal (Command Prompt / PowerShell / Git Bash) và điều hướng đến thư mục dự án:
```bash
cd du-an-cua-ban/FIT_Backend
```

### 2. Thiết lập môi trường ảo (Virtual Environment)
Môi trường ảo giúp quản lý các thư viện riêng biệt cho dự án.

- **Trên Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

- **Trên macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*( Dấu nhắc lệnh `(.venv)` xuất hiện ở đầu dòng lệnh, báo hiệu môi trường ảo đã được kích hoạt tành công) .*

### 3. Cài đặt các thư viện phụ thuộc (Dependencies)
Chạy lệnh sau để cài đặt toàn bộ các thư viện cần thiết (Flask, SQLAlchemy, Google GenAI,...):
```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường
Dự án sử dụng các biến môi trường để kết nối database và các dịch vụ khác.
1. Tại thư mục gốc `FIT_Backend`, copy file `.env.example` và đổi tên file mới thành `.env`.
2. Mở file `.env` bằng trình chỉnh sửa code và điền các thông số:
Ở file .env.example để xem cấu trúc và các tham số cần thiết

```ini                                      
# Cấu hình Database (Thay đổi USER, PASSWORD, DB_NAME cho khớp với PostgreSQL của bạn)
DATABASE_URL=postgresql://postgres:matkhau123@localhost:5432/fit_database_name

# Tạo khóa bảo mật ngẫu nhiên
SECRET_KEY=nhap_mot_chuoi_ngau_nhien
JWT_SECRET_KEY=nhap_mot_chuoi_ngau_nhien_cho_jwt

# API Key cho Google Gemini
GEMINI_API_KEY=api_key_cua_ban

# (Tùy chọn) Cấu hình Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=YOUR-EMAIL-HERE
MAIL_PASSWORD=YOUR-PASS-WORD-HERE
#pass word gmail này để sử dụng chức năng gửi email OTP, vì thế cần phải đăng nhập vào tài khoản gmail để tạo pass word ứng dụng sau đó dán vào đây
```

### 5. Thiết lập Cơ sở dữ liệu (Database)
1. Mở phần mềm quản trị CSDL (như pgAdmin, DBeaver) và **tạo một database trống** có tên khớp với `DB_NAME` bạn vừa điền trong file `.env`.
2. Chạy lệnh migrate để tự động tạo các bảng (tables) trong database:
```bash
flask db upgrade
```

### 6. Khởi chạy Server
Chạy lệnh sau để khởi động Backend Server:
```bash
python run.py
```

 
dự án chạy thì terminal sẽ in ra danh sách toàn bộ các API Route có sẵn.
### 7. Seed database

ở file seed.py nếu bạn muốn seed database thì chạy lệnh sau:

```bash
python -m flask seed-db

```

cái này để tạo ra dữ liệu ngẫu nhiên như người dùng giảng viên, sinh viên, tài liệu nghiên cứu để test thử 

lưu ý các dữ liệu dump data này nó ngẫu nhiên khá là vô tri


tài khoản nếu dùng file seed sẽ là :
Role: admin      | User Code: admin_fit             | Pass: admin123
Role: editor     | User Code: ED001                 | Pass: ED001123
Role: lecturer   | User Code: GV001                 | Pass: GV001123
Role: student    | User Code: SV20240001            | Pass: SV20240001123
 hoặc khi đăng nhập với tài khoản admin có thể tạo người dùng rồi test 
### lưu ý 1 chút
lưu ý ở tính năng AI để tóm tắt tổng quan , do là dùng key fre thế nên nếu dùng quá giới hạn thì sẽ bị lỗi , không nên spam request quá nhiều sẽ dẫn tới lỗi 