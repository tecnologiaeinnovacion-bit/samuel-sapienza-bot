#!/usr/bin/env python3
"""
Sapienza Bot — Asesor virtual de admisiones (Gemini API)

Uso:
    python sapienza_bot.py              # modo chat interactivo
    python sapienza_bot.py --once "Hola, ¿cuánto cuesta la especialización?"
    python sapienza_bot.py --eval       # corre suite de preguntas de prueba

Comandos dentro del chat:
    /reset       -> reinicia la conversación
    /save        -> guarda transcript en transcripts/<timestamp>.md
    /history     -> muestra los últimos 5 turnos
    /system      -> muestra los primeros 30 renglones del system prompt
    /quit        -> sale (Ctrl+C también funciona)
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("\n❌ Falta el paquete google-genai. Ejecuta:\n   pip install -r requirements.txt\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv es opcional

# ============== CONFIGURACIÓN ==============
ROOT = Path(__file__).parent
SYSTEM_PROMPT_FILE = ROOT / "system_prompt.md"
KB_FILE = ROOT / "kb.txt"
TRANSCRIPTS_DIR = ROOT / "transcripts"
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # rápido y barato
TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))

# Colores ANSI para terminal
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    BLUE    = "\033[34m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    RED     = "\033[31m"
    CYAN    = "\033[36m"
    MAGENTA = "\033[35m"
    GRAY    = "\033[90m"

def cprint(text, color="", bold=False, end="\n"):
    prefix = (C.BOLD if bold else "") + color
    print(f"{prefix}{text}{C.RESET}", end=end, flush=True)

# ============== CARGA DE ARCHIVOS ==============
def load_files():
    if not SYSTEM_PROMPT_FILE.exists():
        cprint(f"❌ No encuentro {SYSTEM_PROMPT_FILE.name}", C.RED, bold=True)
        sys.exit(1)
    if not KB_FILE.exists():
        cprint(f"❌ No encuentro {KB_FILE.name}", C.RED, bold=True)
        sys.exit(1)

    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    kb = KB_FILE.read_text(encoding="utf-8")
    full_system = f"{system_prompt}\n\n{kb}"
    return full_system

# ============== CLIENTE GEMINI ==============
def build_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        cprint("\n❌ No encuentro GEMINI_API_KEY.", C.RED, bold=True)
        cprint("   Crea un archivo .env basándote en .env.example, o exporta la variable:", C.YELLOW)
        cprint("     export GEMINI_API_KEY='tu-api-key-aqui'", C.GRAY)
        cprint("\n   Obtén una gratis en: https://aistudio.google.com/apikey\n", C.CYAN)
        sys.exit(1)
    return genai.Client(api_key=api_key)

def make_chat(client, system_instruction):
    """Crea una sesión de chat con system instruction + KB."""
    return client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=TEMPERATURE,
            max_output_tokens=1024,
        ),
    )

# ============== TRANSCRIPT ==============
def save_transcript(chat):
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = TRANSCRIPTS_DIR / f"chat_{ts}.md"
    lines = [f"# Transcript Sapienza Bot — {ts}\n", f"Modelo: `{MODEL}` · Temperature: `{TEMPERATURE}`\n"]
    for msg in chat.get_history():
        role = "👤 Usuario" if msg.role == "user" else "🤖 Sofía (Sapienza)"
        text = msg.parts[0].text if msg.parts else ""
        lines.append(f"\n## {role}\n\n{text}\n")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

# ============== MODO CHAT ==============
BANNER = f"""
{C.BOLD}{C.BLUE}╔══════════════════════════════════════════════════════════════╗
║   SAPIENZA BOT · Asesor Virtual de Admisiones (Gemini)       ║
║   Modelo: {C.RESET}{C.CYAN}{{model}}{C.BLUE}{C.BOLD}                                   ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
{C.DIM}Comandos: /reset · /save · /history · /system · /quit{C.RESET}
"""

EVAL_QUESTIONS = [
    "Hola",
    "¿Cuánto cuesta la especialización?",
    "¿Es virtual?",
    "¿Cuál es el horario?",
    "Me interesa, ¿cómo me inscribo?",
    "¿Y si quiero hacer una maestría después?",
    "¿La maestría también es de Sapienza?",
    "¿Qué pasa si no alcanzo el 50% de homologación?",
    "¿Puedo pagar con cesantías?",
    "¿Dan certificación PMP?",
    "¿Tienen sede en Medellín?",  # debería caer al fallback
]

def chat_loop(client, system_instruction):
    print(BANNER.format(model=MODEL).replace("{model}", MODEL))
    chat = make_chat(client, system_instruction)

    while True:
        try:
            cprint("\nTú ", C.GREEN, bold=True, end="")
            user_input = input("» ").strip()
        except (EOFError, KeyboardInterrupt):
            cprint("\n\n👋 Hasta luego.", C.YELLOW)
            break

        if not user_input:
            continue

        # ---- comandos ----
        if user_input == "/quit":
            cprint("\n👋 Hasta luego.", C.YELLOW); break

        if user_input == "/reset":
            chat = make_chat(client, system_instruction)
            cprint("🔄 Conversación reiniciada.", C.YELLOW); continue

        if user_input == "/save":
            path = save_transcript(chat)
            cprint(f"💾 Transcript guardado en: {path}", C.GREEN); continue

        if user_input == "/history":
            history = chat.get_history()
            cprint(f"\n— Historial ({len(history)} turnos) —", C.DIM)
            for msg in history[-10:]:
                role = "👤" if msg.role == "user" else "🤖"
                text = msg.parts[0].text if msg.parts else ""
                cprint(f"{role} {text[:120]}{'...' if len(text) > 120 else ''}", C.DIM)
            continue

        if user_input == "/system":
            cprint("\n— System prompt (primeras líneas) —", C.DIM)
            for line in SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").splitlines()[:30]:
                cprint(line, C.DIM)
            continue

        # ---- envío al modelo ----
        cprint("\nSofía ", C.MAGENTA, bold=True, end="")
        cprint("(escribiendo...)", C.DIM, end="\r")
        t0 = time.time()
        try:
            response = chat.send_message(user_input)
            text = response.text or "(sin respuesta)"
        except Exception as e:
            cprint(f"❌ Error: {e}", C.RED); continue
        latency = time.time() - t0

        # limpiar línea "escribiendo..."
        sys.stdout.write("\033[K")
        cprint(f"{C.MAGENTA}{C.BOLD}Sofía » {C.RESET}{text}")
        cprint(f"{C.DIM}({latency:.1f}s){C.RESET}", end="")
        print()

def once_mode(client, system_instruction, prompt):
    chat = make_chat(client, system_instruction)
    response = chat.send_message(prompt)
    print(response.text or "")

def eval_mode(client, system_instruction):
    cprint(f"\n🧪 Modo evaluación — {len(EVAL_QUESTIONS)} preguntas\n", C.CYAN, bold=True)
    chat = make_chat(client, system_instruction)
    for i, q in enumerate(EVAL_QUESTIONS, 1):
        cprint(f"[{i}/{len(EVAL_QUESTIONS)}] 👤 {q}", C.GREEN, bold=True)
        t0 = time.time()
        try:
            response = chat.send_message(q)
            text = response.text or "(sin respuesta)"
        except Exception as e:
            cprint(f"   ❌ Error: {e}\n", C.RED); continue
        latency = time.time() - t0
        cprint(f"🤖 {text}", C.MAGENTA)
        cprint(f"   ({latency:.1f}s)\n", C.DIM)
    # guardar
    path = save_transcript(chat)
    cprint(f"💾 Transcript guardado en: {path}\n", C.GREEN)

# ============== MAIN ==============
def main():
    parser = argparse.ArgumentParser(description="Bot Sapienza con Gemini")
    parser.add_argument("--once", type=str, help="Una sola pregunta y salir")
    parser.add_argument("--eval", action="store_true", help="Correr suite de evaluación")
    args = parser.parse_args()

    system_instruction = load_files()
    client = build_client()

    if args.once:
        once_mode(client, system_instruction, args.once)
    elif args.eval:
        eval_mode(client, system_instruction)
    else:
        chat_loop(client, system_instruction)

if __name__ == "__main__":
    main()
