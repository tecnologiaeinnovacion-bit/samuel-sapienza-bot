# 🎓 Sapienza Bot — Asesor Virtual de Admisiones

Bot conversacional para WhatsApp con **Gemini API + Base de Conocimiento de Sapienza**.
Listo para ejecutar en terminal. Migrable a producción (WhatsApp / web).

---

## 🚀 Inicio rápido (5 minutos)

### 1) Obtener API Key de Gemini (gratis)

Ve a 👉 https://aistudio.google.com/apikey

Inicia sesión con tu cuenta de Google → **Create API Key** → cópiala.

> 💡 El tier gratuito da ~1500 requests/día con `gemini-2.5-flash`, más que suficiente para probar.

### 2) Instalar dependencias

```bash
cd sapienza-bot
python3 -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Configurar API key

```bash
cp .env.example .env
# Edita .env y pega tu API key en GEMINI_API_KEY=
```

### 4) Probar el bot

**Modo chat interactivo:**
```bash
python sapienza_bot.py
```

**Una sola pregunta (test rápido):**
```bash
python sapienza_bot.py --once "¿Cuánto cuesta la especialización?"
```

**Suite de evaluación (11 preguntas representativas):**
```bash
python sapienza_bot.py --eval
```

---

## 💬 Comandos dentro del chat

| Comando | Acción |
|---------|--------|
| `/reset` | Reinicia la conversación (borra historial) |
| `/save` | Guarda la transcripción en `transcripts/chat_<timestamp>.md` |
| `/history` | Muestra los últimos 10 turnos |
| `/system` | Muestra las primeras líneas del system prompt |
| `/quit` | Sale del bot |

---

## 📂 Estructura del proyecto

```
sapienza-bot/
├── sapienza_bot.py        # Script principal (CLI)
├── system_prompt.md       # Personalidad y reglas de "Sofía"
├── kb.txt                 # Base de conocimiento (extraída del .docx)
├── requirements.txt       # Dependencias
├── .env.example           # Plantilla de configuración
├── .env                   # Tu API key (NO subir a git)
├── transcripts/           # Conversaciones guardadas con /save
└── README.md              # Este archivo
```

---

## 🧪 Ejemplos de prueba

Estas son las preguntas que `--eval` corre automáticamente:

1. `Hola` → debe saludar y presentarse
2. `¿Cuánto cuesta la especialización?` → debe dar valores exactos
3. `¿Es virtual?` → sí, sincrónica + asincrónica
4. `¿Cuál es el horario?` → martes/miércoles/jueves nocturno
5. `Me interesa, ¿cómo me inscribo?` → debe pedir datos del lead
6. `¿Y si quiero hacer una maestría después?` → debe explicar convenio FUAC
7. `¿La maestría también es de Sapienza?` → debe aclarar que el título es de FUAC
8. `¿Qué pasa si no alcanzo el 50% de homologación?` → $2.104.925
9. `¿Puedo pagar con cesantías?` → sí
10. `¿Dan certificación PMP?` → sí, lista todas
11. `¿Tienen sede en Medellín?` → **debe fallar gracefully** y derivar a asesor

---

## 🔧 Personalización rápida

### Cambiar el tono de Sofía
Edita `system_prompt.md` (sección "Estilo de respuesta WhatsApp").

### Actualizar precios o info
Edita `kb.txt` directamente. Si actualizas el `.docx`, regenera:
```bash
pandoc KB_Bot_WhatsApp_Sapienza.docx -t plain -o kb.txt
```

### Cambiar de modelo
En `.env`:
```
GEMINI_MODEL=gemini-2.5-pro    # más capaz pero más lento/caro
```

### Cambiar la "creatividad"
En `.env`:
```
GEMINI_TEMPERATURE=0.2    # más conservador, sigue mejor las reglas
GEMINI_TEMPERATURE=0.7    # más natural pero menos predecible
```

---

## 🚢 Próximos pasos (de prueba a producción)

| Hito | Setup recomendado |
|------|-------------------|
| **Validar respuestas con asesores humanos** | Sube `kb.txt` + `system_prompt.md` a un **Gem en Google AI Studio**: https://aistudio.google.com/app/gems |
| **Demo web interna** | Envuelve `sapienza_bot.py` con FastAPI + un frontend simple (Streamlit o Gradio) |
| **Producción WhatsApp** | API Gemini + **Twilio** o **360dialog** o **WhatsApp Business Cloud API** |
| **Captura de leads → CRM** | Webhook desde WhatsApp → almacenar conversaciones en una base + integración con HubSpot / Pipedrive |
| **RAG (si la KB crece mucho)** | Migrar a Vertex AI Search o pgvector cuando tengas >20 programas |

---

## 🐛 Troubleshooting

**Error: `No module named 'google.genai'`**
→ Ejecuta `pip install -r requirements.txt` dentro del venv activado.

**Error: `No encuentro GEMINI_API_KEY`**
→ Verifica que `.env` existe y tiene la línea `GEMINI_API_KEY=...`.

**El bot responde en inglés**
→ Sube `GEMINI_TEMPERATURE` o revisa que `system_prompt.md` empiece en español.

**Respuestas muy largas para WhatsApp**
→ Reduce `max_output_tokens` en `sapienza_bot.py` (línea ~88) o refuerza la regla en `system_prompt.md`.

**El bot inventa precios o fechas**
→ Baja `GEMINI_TEMPERATURE` a `0.2` y refuerza las "Reglas inviolables" en `system_prompt.md`.

---

## 📚 Recursos

- **Gemini API docs**: https://ai.google.dev/gemini-api/docs
- **AI Studio (probar sin código)**: https://aistudio.google.com
- **Crear un Gem**: https://aistudio.google.com/app/gems
- **Vertex AI (producción)**: https://cloud.google.com/vertex-ai

---

*Generado con Claude · Mayo 2026*
