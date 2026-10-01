import os, re, json
from flask import Flask, request, jsonify, send_file
import anthropic

app = Flask(__name__, static_folder=None)
client = anthropic.Anthropic()  # ANTHROPIC_API_KEY muhit o'zgaruvchisidan olinadi
MODEL = os.getenv("MODEL", "claude-haiku-4-5-20251001")

CATS = {
    "Inson": "mashhur inson (tarixiy yoki zamonaviy; dunyo va O'zbekiston/Markaziy Osiyo shaxslari, sportchi, olim, san'atkor, siyosatchi, yozuvchi)",
    "Buyum": "buyum yoki narsa (kundalik buyumlar, texnika, asboblar, transport, kiyim, o'yinchoq, mebel)",
    "Hayvon": "hayvon (yovvoyi, uy, qush, baliq, hasharot, dinozavr)",
}

def build_prompt(cat, log, rej, extra=""):
    n = len(log)
    lines = "\n".join(f"{i+1}. {x['q']} -> {x['a']}" for i, x in enumerate(log)) or "(hali savol yo'q)"
    rule = "Hali taxmin qilma, faqat yangi savol ber." if n < 12 else "Agar kamida 90% ishonsang taxmin qil, bo'lmasa savol ber."
    if n >= 22:
        rule += " Endi albatta eng ehtimolli taxminingni ayt."
    return f"""Sen Akinator kabi taxmin qiluvchi o'yinsan. Mavzu: {CATS.get(cat, cat)}. Foydalanuvchi shu mavzudan bitta obyektni o'ylagan. Sen ha/yo'q savollar berib topasan. Javoblar: "Ha", "Yo'q", "Ba'zan" (qisman), "Umuman bilmayman".
Hozirgacha:
{lines}
Noto'g'ri taxminlar (qayta aytma): {", ".join(rej) or "yo'q"}.
{rule} {extra}
Muhim: savolda hech qachon aniq nom yoki javobni aytma, faqat xususiyat haqida so'ra. Aniq nomni faqat taxmin turida ayt. Savol qisqa, o'zbek tilida, oldingi savollarni takrorlama; umumiydan aniqqa qarab bor.
Faqat JSON qaytar. Savol: {{"type":"question","text":"..."}}. Taxmin: {{"type":"guess","name":"nomi (o'zbekcha)","info":"2-3 gaplik qisqa ma'lumot","does":"u nima qiladi yoki nima bilan mashhur, 1-2 gap","wiki":"Vikipediyada qidirish uchun inglizcha nomi"}}"""

def ask(prompt):
    r = client.messages.create(model=MODEL, max_tokens=500,
                               messages=[{"role": "user", "content": prompt}])
    m = re.search(r"\{.*\}", r.content[0].text, re.S)
    return json.loads(m.group(0))

@app.post("/api/ask")
def api_ask():
    d = request.get_json(force=True)
    cat, log, rej = d.get("cat", "Inson"), d.get("log", []), d.get("rej", [])
    try:
        r = ask(build_prompt(cat, log, rej))
        if r.get("type") == "guess" and len(log) < 12:
            r = ask(build_prompt(cat, log, rej, "Hozir taxmin qilma, faqat savol ber."))
        return jsonify(r)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/")
def index():
    return send_file("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
