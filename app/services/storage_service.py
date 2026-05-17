import os
import uuid
import mimetypes
import requests
from flask import current_app
from werkzeug.utils import secure_filename
from app.models.setting_model import SystemSetting
from app.extensions import db

class StorageService:
    def upload_file(self, file, bucket_name: str) -> str:
        """
        Uploads a file and returns its access URL.
        `file`: Flask FileStorage object (from request.files).
        `bucket_name`: The bucket or folder category (e.g., 'papers', 'datasets', 'uploads').
        """
        raise NotImplementedError

class LocalStorageService(StorageService):
    def upload_file(self, file, bucket_name: str) -> str:
        # Đường dẫn thư mục lưu file local thống nhất trong app/storage/uploads
        upload_dir = os.path.join(os.getcwd(), 'app', 'storage', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Làm sạch tên file và tạo mã duy nhất chống trùng lặp
        original_name = secure_filename(file.filename)
        filename = f"{bucket_name}_{uuid.uuid4().hex[:8]}_{original_name}"
        file_path = os.path.join(upload_dir, filename)
        
        # Đảm bảo file được đọc từ đầu nếu đã đọc trước đó
        file.seek(0)
        
        # Lưu file vật lý
        file.save(file_path)
        
        # Trả về đường link tương đối thống nhất để Flask serve
        return f"/storage/uploads/{filename}"

class SupabaseStorageService(StorageService):
    def upload_file(self, file, bucket_name: str) -> str:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Thiếu cấu hình SUPABASE_URL hoặc SUPABASE_KEY trong file .env!")

        # Tự động chuẩn hóa URL (chỉ lấy scheme và domain, loại bỏ mọi path thừa như /rest/v1 nếu có)
        from urllib.parse import urlparse
        parsed_url = urlparse(supabase_url)
        base_supabase_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Tạo tên file duy nhất
        original_name = secure_filename(file.filename)
        filename = f"{bucket_name}_{uuid.uuid4().hex[:8]}_{original_name}"
        
        # Xác định Mime-Type của file tự động
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
            
        # Đường dẫn API REST upload của Supabase Storage
        upload_url = f"{base_supabase_url}/storage/v1/object/{bucket_name}/{filename}"
        
        # Đọc dữ liệu nhị phân của file
        file.seek(0)
        file_data = file.read()
        
        # Header bắt buộc của Supabase REST API
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key,
            "Content-Type": mime_type
        }
        
        # Upload trực tiếp không cần thư viện bên thứ 3 nặng nề
        response = requests.post(upload_url, headers=headers, data=file_data)
        
        if response.status_code != 200:
            raise Exception(f"Lỗi tải file lên Supabase (Mã {response.status_code}): {response.text}")
            
        # Trả về đường link Public của file vừa upload
        public_url = f"{base_supabase_url}/storage/v1/object/public/{bucket_name}/{filename}"
        return public_url

class StorageManager:
    @staticmethod
    def get_provider() -> StorageService:
        try:
            # Truy vấn database lấy trạng thái cấu hình của Admin
            setting = SystemSetting.query.filter_by(key="STORAGE_PROVIDER").first()
            provider_type = setting.value if setting else "local"
        except Exception:
            # Fallback nếu db chưa được migrate/chạy lần đầu
            provider_type = "local"
            
        if provider_type == "cloud":
            return SupabaseStorageService()
        return LocalStorageService()
