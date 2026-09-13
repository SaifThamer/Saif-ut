# -*- coding: utf-8 -*-
"""
الاتصال بـ Claude API لاستخراج بيانات الكتاب الرسمي من صورة أو ملف PDF
لا يعتمد على مكتبات خارجية إضافية (يستخدم urllib المدمجة في Python)
"""

import base64
import json
import os
import urllib.request
import urllib.error

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

EXTRACTION_PROMPT = (
    "أنت تستخرج بيانات من صورة أو ملف PDF لكتاب رسمي حكومي مكتوب باللغة العربية. "
    "أعد الإجابة بصيغة JSON فقط، بدون أي نص إضافي قبله أو بعده وبدون علامات Markdown، "
    "وبالمفاتيح التالية بالضبط:\n"
    '{\n'
    '  "letter_number": "رقم الكتاب كما ورد",\n'
    '  "sender_type": "نوع الجهة المرسلة، يجب أن يكون واحدًا من: وزارة، هيئة، مديرية، قسم، شعبة، وحدة",\n'
    '  "sender_name": "اسم الجهة المرسلة بالكامل",\n'
    '  "letter_date": "تاريخ الكتاب بصيغة yyyy-MM-dd إن أمكن تحويله، وإلا كما ورد",\n'
    '  "subject": "عنوان أو موضوع الكتاب",\n'
    '  "notes": "أي ملاحظات إضافية مهمة ظاهرة في الكتاب مثل السرية أو الاستعجال (أو نص فارغ)"\n'
    '}\n'
    "إذا لم يظهر أي حقل بوضوح في الكتاب، ضع له قيمة نص فارغ \"\". لا تخترع بيانات غير موجودة."
)

IMAGE_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class ExtractionError(Exception):
    pass


def _build_content_block(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    with open(file_path, "rb") as f:
        raw = f.read()
    b64_data = base64.standard_b64encode(raw).decode("utf-8")

    if ext == ".pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": b64_data,
            },
        }
    media_type = IMAGE_MEDIA_TYPES.get(ext)
    if not media_type:
        raise ExtractionError(f"صيغة الملف غير مدعومة: {ext}")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": b64_data,
        },
    }


def _strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def extract_letter_data(api_key, file_path, model="claude-sonnet-5"):
    """
    يرسل الملف إلى Claude API ويرجع قاموس (dict) ببيانات الكتاب المستخرجة.
    يرفع ExtractionError عند أي خطأ (مفتاح غلط، اتصال، أو استجابة غير متوقعة).
    """
    if not api_key:
        raise ExtractionError("لم يتم إدخال مفتاح Anthropic API. أضفه من صفحة الإعدادات أولاً.")

    content_block = _build_content_block(file_path)

    body = {
        "model": model,
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [content_block, {"type": "text", "text": EXTRACTION_PROMPT}],
            }
        ],
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            msg = error_body
        raise ExtractionError(f"خطأ من الخادم ({e.code}): {msg}")
    except urllib.error.URLError as e:
        raise ExtractionError(f"تعذر الاتصال بالإنترنت أو بخادم Anthropic: {e.reason}")

    text_parts = [
        block.get("text", "") for block in result.get("content", [])
        if block.get("type") == "text"
    ]
    raw_text = "\n".join(text_parts)
    clean_text = _strip_code_fences(raw_text)

    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError:
        raise ExtractionError(
            "تعذر فهم استجابة النموذج كبيانات JSON صحيحة. "
            "جرّب صورة أوضح للكتاب أو حاول مجددًا."
        )

    for key in ["letter_number", "sender_type", "sender_name", "letter_date", "subject", "notes"]:
        data.setdefault(key, "")

    return data
