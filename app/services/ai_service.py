import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_best_model(client):
    """Tu dong tim model tot nhat trong danh sach kha dung"""
    try:
        available_models = [m.name for m in client.models.list()]
        
        # Thứ tự ưu tiên các model ổn định
        priority = [
            'models/gemini-2.0-flash',
            'models/gemini-1.5-flash', 
            'models/gemini-1.5-flash-latest', 
            'models/gemini-flash-latest',
            'models/gemini-pro',
            'gemini-1.5-flash',
        ]
        
        for p in priority:
            if p in available_models:
                return p
        
        # Nếu không có trong priority, tìm cái nào có chữ 'flash'
        for m in available_models:
            if 'flash' in m.lower() and 'preview' not in m.lower():
                return m
                
        return 'models/gemini-1.5-flash'
    except Exception as e:
        print(f"Error finding model: {e}")
        return 'models/gemini-1.5-flash'

def generate_document_summary(document_title, document_description, file_path=None):
    if not GEMINI_API_KEY:
        return {
            "objective": "Thieu API Key.",
            "methodology": "Vui long cau hinh .env",
            "key_findings": ["Key chua duoc thiet lap"],
            "conclusion": "Lien he Admin."
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        active_model = get_best_model(client)
        print(f"--- AI: Using model {active_model} ---")

        contents = []
        instruction = ""
        
        # Hầu hết các model Gemini hiện nay đều hỗ trợ PDF
        if file_path and os.path.exists(file_path):
            print(f"--- AI: Processing PDF {os.path.basename(file_path)} ---")
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            contents.append(types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"))
            instruction = f"Hay phan tich file PDF va tom tat bai nghien cuu '{document_title}'."
        else:
            print("--- AI: Processing text metadata only ---")
            instruction = f"Tom tat bai nghien cuu '{document_title}' dua tren mo ta sau."
            contents.append(f"Tieu de: {document_title}\nMo ta: {document_description}")

        prompt = f"""
        {instruction}
        
        Yeu cau tra ve JSON thuan tuy (khong markdown) voi cac truong:
        - objective: Muc tieu chinh (2-3 cau)
        - methodology: Phuong phap su dung
        - key_findings: Mang 3 ket qua quan trong nhat
        - conclusion: Gia tri cua tai lieu
        
        Ngon ngu: Tieng Viet.
        """
        contents.append(prompt)

        response = client.models.generate_content(model=active_model, contents=contents)
        
        res_text = response.text.strip()
        
        # Parse JSON
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        try:
            return json.loads(res_text)
        except:
            import re
            json_match = re.search(r'\{.*\}', res_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {
                "objective": "Loi format JSON tu AI",
                "methodology": res_text[:200],
                "key_findings": ["Khong the phan tich JSON"],
                "conclusion": "Lien he Admin."
            }

    except Exception as e:
        print(f"AI ERROR: {str(e)}")
        return {
            "objective": "AI gap su co khi xu ly.",
            "methodology": f"Error: {str(e)}",
            "key_findings": ["Vui long thu lai sau"],
            "conclusion": "Loi ket noi Gemini."
        }
