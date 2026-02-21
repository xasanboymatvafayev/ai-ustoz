import re

DEFAULT_KEYWORDS = [
    "chunki", "sababli", "natijada", "demak", "xulosa", "muhim",
    "birinchi", "ikkinchi", "uchinchi", "misol", "masalan", "ya'ni"
]

def check_length(content: str) -> tuple:
    words = len(content.split())
    if words >= 100: return 5, f"Juda yaxshi uzunlik ({words} so'z)"
    elif words >= 60: return 4, f"Yaxshi uzunlik ({words} so'z)"
    elif words >= 30: return 3, f"O'rtacha uzunlik ({words} so'z)"
    elif words >= 15: return 2, f"Qisqa javob ({words} so'z)"
    else: return 1, f"Juda qisqa ({words} so'z)"

def check_structure(content: str) -> tuple:
    sentences = [s.strip() for s in re.split(r'[.!?]', content) if len(s.strip()) > 5]
    xulosa = ["xulosa", "demak", "shunday", "yakunida", "natijada", "umuman"]
    score = 1
    notes = []
    if sentences: score += 1; notes.append("Kirish bor")
    if len(sentences) >= 3: score += 1; notes.append("Asosiy qism bor")
    if any(w in content.lower() for w in xulosa): score += 1; notes.append("Xulosa bor")
    if len(content.split('\n')) >= 2: notes.append("Paragraflar bor")
    return min(score, 5), " | ".join(notes) or "Oddiy struktura"

def check_keywords(content: str, extra_words: list = None) -> tuple:
    kw = DEFAULT_KEYWORDS + (extra_words or [])
    found = [k for k in kw if k in content.lower()]
    ratio = len(found) / max(len(kw), 1)
    if ratio >= 0.35: return 5, f"{len(found)} kalit so'z topildi"
    elif ratio >= 0.2: return 4, f"{len(found)} kalit so'z topildi"
    elif ratio >= 0.1: return 3, f"{len(found)} kalit so'z topildi"
    elif ratio >= 0.05: return 2, f"{len(found)} kalit so'z topildi"
    else: return 1, "Kalit so'zlar kam"

def check_quality(content: str) -> tuple:
    words = content.lower().split()
    if not words: return 1, "Bo'sh"
    unique_ratio = len(set(words)) / len(words)
    has_numbers = bool(re.search(r'\d+', content))
    has_examples = any(w in content.lower() for w in ["misol", "masalan", "ya'ni"])
    score = 3
    notes = []
    if unique_ratio >= 0.7: score += 1; notes.append("Boy lug'at")
    elif unique_ratio < 0.4: score -= 1; notes.append("Takror so'zlar ko'p")
    if has_numbers: notes.append("Faktlar bor")
    if has_examples: score = min(score + 1, 5); notes.append("Misollar bor")
    return max(1, min(score, 5)), " | ".join(notes) or "O'rtacha"

def ai_check(content: str, assignment_description: str = "") -> dict:
    if not content or not content.strip():
        return {"ai_score": 1, "ai_comment": "Javob bo'sh yoki juda qisqa", "confidence": 95}

    extra = [w for w in assignment_description.lower().split() if len(w) > 4][:10]

    l_score, l_note = check_length(content)
    s_score, s_note = check_structure(content)
    k_score, k_note = check_keywords(content, extra)
    q_score, q_note = check_quality(content)

    # Weighted average
    final = round((l_score * 2 + s_score * 2 + k_score * 1 + q_score * 1.5) / 6.5)
    final = max(1, min(5, final))

    confidence = max(65, min(95, 85 - abs(l_score - q_score) * 5))

    if final == 5: summary = "🌟 Ajoyib javob! Barcha mezonlar a'lo darajada bajarilgan."
    elif final == 4: summary = "✅ Yaxshi javob. Biroz kengaytirish bilan mukammal bo'ladi."
    elif final == 3: summary = "📝 O'rtacha javob. Strukturani va hajmni yaxshilang."
    elif final == 2: summary = "⚠️ Zaif javob. Ko'proq ma'lumot va misol kerak."
    else: summary = "❌ Qoniqarsiz. Vazifani diqqat bilan qayta o'qib, javobni qayta yozing."

    comment = f"{summary}\n\n• Uzunlik: {l_note}\n• Struktura: {s_note}\n• Kalit so'zlar: {k_note}\n• Sifat: {q_note}"

    return {"ai_score": final, "ai_comment": comment, "confidence": confidence}
