import os
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = Flask(__name__, static_folder=None)
MODEL = os.getenv('OPENAI_MODEL', 'gpt-5-mini')
API_KEY = os.getenv('OPENAI_API_KEY', '').strip()
client = OpenAI(api_key=API_KEY) if API_KEY else None

INSTRUCTIONS = '''أنت مساعد العملاء الرسمي لمخرطة القحطاني. أجب بالعربية الواضحة والمهنية وباختصار.
ساعد العملاء على فهم خدمات الخراطة وتشغيل المعادن وتصنيع القطع حسب الطلب، واطلب عند الحاجة وصف القطعة والمقاسات والكمية ونوع المعدن إن كان معروفاً.
لا تخترع أسعاراً أو مواعيد تسليم أو شهادات أو قدرات غير مؤكدة، ولا تعط سعراً نهائياً؛ وضح أن السعر يحتاج مراجعة فريق المخرطة.
للتواصل: +966 55 152 6605. واتساب: https://wa.me/966551526605
لا تطلب كلمات مرور أو بيانات دفع أو معلومات حساسة.'''

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_PAGES = {
    'index', 'services', 'turning', 'cnc', 'laser',
    'gallery', 'about', 'contact',
}

@app.get('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.get('/<page>.html')
def html_page(page):
    # Serve only the known site pages; keep API routes separate.
    if page not in ALLOWED_PAGES:
        return jsonify(error='الصفحة غير موجودة.'), 404
    return send_from_directory(BASE_DIR, f'{page}.html')

@app.get('/api/health')
def health():
    return jsonify(ok=True, assistantConfigured=bool(client), model=MODEL)

@app.post('/api/chat')
def chat():
    if client is None:
        return jsonify(error='المساعد غير مفعّل. أضف مفتاح OPENAI_API_KEY إلى ملف .env ثم أعد تشغيل الموقع.'), 503
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    if not isinstance(message, str) or not message.strip():
        return jsonify(error='اكتب سؤالك أولاً.'), 400
    message = message.strip()
    if len(message) > 700:
        return jsonify(error='السؤال طويل جداً؛ اختصره إلى 700 حرف.'), 400
    try:
        response = client.responses.create(
            model=MODEL,
            instructions=INSTRUCTIONS,
            input=message,
            max_output_tokens=350,
        )
        return jsonify(reply=response.output_text or 'لم أتمكن من إعداد إجابة الآن. تواصل معنا عبر واتساب.')
    except Exception as exc:
        app.logger.error('AI chat failed: %s', getattr(exc, 'status', None) or type(exc).__name__)
        return jsonify(error='تعذر الحصول على إجابة من المساعد حالياً. حاول لاحقاً أو تواصل عبر واتساب.'), 502

if __name__ == '__main__':
    # للتجربة المحلية فقط؛ استخدم خادماً مناسباً عند النشر العام.
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
