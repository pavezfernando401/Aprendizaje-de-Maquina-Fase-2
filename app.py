from flask import Flask, render_template, request, jsonify
import ollama
import os

# config general
MODEL_NAME        = "llama3.1:8b"
KB_DIR            = os.path.join(os.path.dirname(__file__), "knowledge_base")
PROMPT_FILE       = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
MAX_CONTEXT_CHARS = 6000
TEMPERATURE       = 0.3
NUM_PREDICT       = 400

app = Flask(__name__)

# carga los archivos .md al iniciar
def load_knowledge_base() -> dict:
    kb = {}
    for fname in os.listdir(KB_DIR):
        if fname.endswith(".md"):
            path = os.path.join(KB_DIR, fname)
            with open(path, encoding="utf-8") as f:
                kb[fname[:-3]] = f.read()
    return kb

def load_system_prompt() -> str:
    with open(PROMPT_FILE, encoding="utf-8") as f:
        return f.read()

KB            = load_knowledge_base()
SYSTEM_PROMPT = load_system_prompt()

# keywords por tema para el RAG
TOPIC_KEYWORDS: dict = {
    "causas":            ["causa", "origen", "tratado", "versalles", "depresión",
                          "nazi", "fascis", "apaciguamiento", "molotov", "ribbentrop"],
    "cronologia":        ["cuándo", "fecha", "año", "cronolog", "1939", "1940",
                          "1941", "1942", "1943", "1944", "1945", "timeline"],
    "paises_y_alianzas": ["aliado", "eje", "país", "nacion", "churchill", "hitler",
                          "stalin", "roosevelt", "mussolini", "japón", "alemania",
                          "urss", "estados unidos", "eeuu", "lider", "líder"],
    "batallas":          ["batalla", "operación", "stalingrado", "normandía", "midway",
                          "kursk", "ardenas", "berlín", "atlántico", "iwo jima",
                          "dunkerque", "alamein"],
    "frente_occidental": ["occidental", "francia", "dunkerque", "vichy", "resistencia",
                          "áfrica", "italia", "normandía", "overlord", "paris", "parís",
                          "rommel", "montgomery"],
    "frente_oriental":   ["oriental", "urss", "soviet", "barbarroja", "stalingrado",
                          "leningrado", "kursk", "bagration", "zhúkov", "invierno"],
    "guerra_pacifico":   ["pacífico", "japón", "pearl harbor", "midway", "kamikaze",
                          "island hopping", "hiroshima", "nagasaki", "atómica",
                          "macarthur", "nimitz", "iwo jima", "guadalcanal"],
    "consecuencias":     ["consecuencia", "resultado", "posguerra", "onu", "naciones unidas",
                          "guerra fría", "plan marshall", "holocausto", "nuclear",
                          "nuremberg", "núremberg", "israel", "telón"],
    "glosario":          ["qué es", "qué significa", "definición", "significa",
                          "blitzkrieg", "enigma", "panzer", "waffen", "luftwaffe",
                          "u-boot", "lend-lease", "overlord", "ostfront"],
}

# busca los archivos más relevantes según la query
def retrieve_context(query: str) -> str:
    q_lower = query.lower()
    scores: dict = {topic: 0 for topic in KB}

    for topic, keywords in TOPIC_KEYWORDS.items():
        if topic in KB:
            for kw in keywords:
                if kw in q_lower:
                    scores[topic] += 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    context_parts = []
    total_chars   = 0

    for topic, score in ranked:
        if topic not in KB:
            continue
        content = KB[topic]
        if score > 0 or (all(s == 0 for _, s in ranked) and len(context_parts) < 2):
            if total_chars + len(content) <= MAX_CONTEXT_CHARS:
                context_parts.append(f"### {topic.upper().replace('_', ' ')}\n{content}")
                total_chars += len(content)
            else:
                remaining = MAX_CONTEXT_CHARS - total_chars
                if remaining > 200:
                    context_parts.append(
                        f"### {topic.upper().replace('_', ' ')}\n{content[:remaining]}..."
                    )
                break

    # fallback: si no hubo matches, manda los primeros 2 archivos
    if not context_parts:
        for i, (topic, content) in enumerate(KB.items()):
            if i >= 2:
                break
            context_parts.append(f"### {topic.upper().replace('_', ' ')}\n{content[:2000]}")

    return "\n\n---\n\n".join(context_parts)

# arma el prompt y llama al modelo
def ask_ollama(user_query: str, chat_history: list) -> str:
    context = retrieve_context(user_query)

    messages = [
        {
            "role": "system",
            "content": (
                f"{SYSTEM_PROMPT}\n\n"
                "A continuación encontrarás la base de conocimiento disponible:\n\n"
                f"{context}"
            )
        }
    ]

    # últimas 6 rondas de historial
    for turn in chat_history[-12:]:
        messages.append(turn)

    messages.append({"role": "user", "content": user_query})

    response = ollama.chat(
        model=MODEL_NAME,
        messages=messages,
        options={"temperature": TEMPERATURE, "num_predict": NUM_PREDICT}
    )
    return response["message"]["content"]


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data     = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    history  = data.get("history", [])

    if not user_msg:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        answer = ask_ollama(user_msg, history)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health")
def health():
    try:
        models = ollama.list()
        names  = [m["model"] for m in models.get("models", [])]
        ok     = any(MODEL_NAME in n for n in names)
        return jsonify({
            "status":      "ok" if ok else "model_not_found",
            "model":       MODEL_NAME,
            "model_ready": ok,
            "available":   names
        })
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


if __name__ == "__main__":
    print(f"Modelo: {MODEL_NAME}")
    print("Abre http://127.0.0.1:5000 en tu navegador")
    app.run(debug=True, use_reloader=False, port=5000)
