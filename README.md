# Chatbot - Fase 2 - Segunda Guerra Mundial

## Descripcion
Chatbot educativo de dominio cerrado sobre la Segunda Guerra Mundial (1939-1945).
Usa llama3.1:8b via Ollama con RAG simple por palabras clave sobre una base de conocimiento en Markdown. Frontend en HTML/CSS/JS servido por Flask.

## Estructura
```
Chatbot Fase 2/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── knowledge_base/
│   ├── causas.md
│   ├── cronologia.md
│   ├── paises_y_alianzas.md
│   ├── frente_occidental.md
│   ├── frente_oriental.md
│   ├── guerra_pacifico.md
│   ├── batallas.md
│   ├── consecuencias.md
│   └── glosario.md
└── prompts/
    └── system_prompt.txt
```

## Requisitos
- Python 3.10+
- Ollama instalado (https://ollama.com)

## Instalacion

```bash
pip install -r requirements.txt
ollama pull llama3.1:8b
```

## Ejecucion

```bash
python app.py
```

Abrir en el navegador: http://127.0.0.1:5000

> Ollama se inicia automaticamente en segundo plano. Si no, ejecuta `ollama serve` en otra terminal primero.

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Interfaz del chat |
| POST | `/api/chat` | Recibe `{message, history}`, devuelve `{answer}` |
| GET | `/api/health` | Estado del modelo |

## Configuracion del modelo

| Parametro | Valor |
|-----------|-------|
| Modelo | llama3.1:8b |
| Temperatura | 0.3 |
| Tokens max por respuesta | 400 |
| Historial | ultimas 6 rondas |
| Contexto RAG max | 6000 caracteres |
