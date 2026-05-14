import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_ordered_models(client):
    """Lấy danh sách các model Flash khả dụng và sắp xếp theo thứ tự ưu tiên."""
    try:
        available_models = [m.name for m in client.models.list()]
        print(f"--- AI: Available models on your system: {available_models} ---")
        
        # Danh sách ưu tiên các model Flash mạnh và mới nhất
        preferred_patterns = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-1.5-flash'
        ]
        
        ordered_list = []
        # Đầu tiên thêm các model theo đúng thứ tự ưu tiên
        for pattern in preferred_patterns:
            for m in available_models:
                if pattern in m:
                    if m not in ordered_list:
                        ordered_list.append(m)
        
        # Sau đó thêm bất kỳ model nào có chữ 'flash' còn lại
        for m in available_models:
            if 'flash' in m.lower() and m not in ordered_list:
                ordered_list.append(m)
        
        return ordered_list
    except Exception as e:
        print(f"--- AI: Could not list models: {str(e)} ---")
        return ['models/gemini-2.0-flash', 'models/gemini-1.5-flash']

def generate_document_summary(document_title, document_description, file_path=None):
    if not GEMINI_API_KEY:
        return {"objective": "Thiếu API Key.", "methodology": "Kiểm tra file .env", "key_findings": [], "conclusion": ""}

    client = genai.Client(api_key=GEMINI_API_KEY)
    models_to_try = get_ordered_models(client)
    
    # Chuẩn bị nội dung gửi đi (dùng chung cho mọi lần thử)
    contents = []
    instruction = ""
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        contents.append(types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"))
        instruction = f"Hãy phân tích file PDF và tóm tắt bài nghiên cứu '{document_title}'."
    else:
        instruction = f"Tóm tắt bài nghiên cứu '{document_title}' dựa trên mô tả sau."
        contents.append(f"Tiêu đề: {document_title}\nMô tả: {document_description}")

    prompt = f"""
    {instruction}
    Yêu cầu trả về JSON thuần túy (không markdown) với các trường:
    - objective: Mục tiêu chính (2-3 câu)
    - methodology: Phương pháp sử dụng
    - key_findings: Mảng 3 kết quả quan trọng nhất
    - conclusion: Giá trị của tài liệu
    Ngôn ngữ: Tiếng Việt.
    """
    contents.append(prompt)

    # --- CHIẾN THUẬT: THỬ LẦN LƯỢT CÁC MODEL ---
    last_error = ""
    for model_name in models_to_try:
        try:
            print(f"--- AI Strategy: Trying model {model_name} ---")
            response = client.models.generate_content(model=model_name, contents=contents)
            
            res_text = response.text.strip()
            # Xử lý bóc tách JSON
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(res_text)
                print(f"--- AI Strategy: SUCCESS with {model_name} ---")
                return result
            except:
                import re
                json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise Exception("Lỗi format JSON")

        except Exception as e:
            last_error = str(e)
            print(f"--- AI Strategy: FAILED with {model_name} -> {last_error} ---")
            # Nếu lỗi là do Quota (429) thì dừng lại luôn vì thử model khác cũng sẽ lỗi tương tự
            if "429" in last_error or "ResourceExhausted" in last_error:
                return {
                    "objective": "Hệ thống AI đang tạm thời hết lượt dùng miễn phí (Quota Limit).",
                    "methodology": "Vui lòng chờ khoảng 1-2 phút rồi thử lại.",
                    "key_findings": ["Lỗi Resource Exhausted (429)"],
                    "conclusion": "Hạn mức API Key miễn phí đã hết."
                }
            # Nếu lỗi khác (như 404), tiếp tục thử model tiếp theo trong danh sách
            continue

    # Nếu tất cả các model đều thất bại
    return {
        "objective": "Tất cả các model AI đều không phản hồi.",
        "methodology": f"Lỗi cuối cùng: {last_error}",
        "key_findings": ["Vui lòng kiểm tra lại API Key hoặc File PDF"],
        "conclusion": "Chiến thuật thử nhiều model đã thất bại."
    }
