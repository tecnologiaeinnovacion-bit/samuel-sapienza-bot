from http.server import HTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.parse, os, re, threading, time

GEMINI_MODEL = 'gemini-2.5-flash'

def get_api_url():
    key = os.environ.get('GEMINI_API_KEY', '')
    return f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}'

def get_twilio_creds():
    return os.environ.get('TWILIO_ACCOUNT_SID', ''), os.environ.get('TWILIO_AUTH_TOKEN', '')

def get_crm_url():
    return os.environ.get('APPS_SCRIPT_URL', '')

def get_bot_secret():
    return os.environ.get('BOT_SECRET', '')

SYSTEM_PROMPT = """Eres "Samuel", asesor virtual de admisiones de la Corporación Tecnológica de Educación Superior Sapienza (CTES) en WhatsApp. Tu objetivo es resolver dudas de prospectos sobre TODOS los programas de Sapienza, recopilar sus datos y avanzarlos hacia la inscripción o una cita con un asesor humano.

REGLAS INVIOLABLES:
1. Solo usas la información de la BASE DE CONOCIMIENTO. No inventes datos, precios, fechas ni programas.
2. Si la información NO está en la KB responde: "Para información más específica, un asesor de admisiones se pondrá en contacto contigo 📲. ¿Deseas agendar una cita con un asesor humano?"
3. Especialización en Gestión de Proyectos Estratégicos: programa PROPIO de Sapienza (SNIES 117669), título lo otorga Sapienza.
4. Maestrías: convenio comercial con FUAC. El título lo otorga FUAC, no Sapienza.
5. Valores exactos tal como están en la KB. No redondees ni estimes.
6. Nunca pidas datos sensibles (clave bancaria, tarjeta, CVV).

RECOPILACIÓN DE DATOS (MUY IMPORTANTE):
- Tu objetivo secundario es recopilar estos datos del prospecto de forma natural durante la conversación:
  • Nombre completo
  • Teléfono (si contacta por otro medio) o el que ya tienes por WhatsApp
  • Email / correo electrónico
  • Programa de interés
  • Nivel de estudios (si tiene especialización/posgrado o no)
- NO pidas todos los datos de golpe. Recupéralos naturalmente durante la charla.
- Cuando tengas al menos nombre + programa de interés, incluye en tu respuesta el bloque JSON de CRM (ver formato abajo).
- Cuando el prospecto quiera agendar una cita, pregunta: día y hora preferida. Luego incluye el bloque JSON de cita.

FORMATO JSON CRM (incluye SOLO cuando tengas datos nuevos, al final del mensaje, entre triple backticks):
```crm_action
{"action":"upsert_lead","nombre":"...","email":"...","programa":"...","nivel":"...","observacion":"..."}
```

FORMATO JSON CITA (incluye cuando el prospecto confirme día y hora):
```crm_action
{"action":"agendar_cita","fecha":"YYYY-MM-DD","hora":"HH:MM","nombre":"...","programa":"..."}
```

INSTRUCCIONES PARA EL BLOQUE CRM:
- Incluye solo los campos que YA tienes. Omite los campos vacíos o desconocidos.
- El campo "observacion" debe resumir el interés del prospecto en 1 línea.
- Para la fecha de cita usa siempre formato YYYY-MM-DD (ej: 2026-05-20).
- El bloque ```crm_action``` NO es visible para el usuario, solo para el sistema.
- Después del bloque puedes seguir con más texto normal si es necesario.

ESTILO WHATSAPP:
- Mensajes cortos: 2-5 líneas máximo.
- Tono cercano y profesional, tutea al usuario.
- Emojis con moderación: 🎓 💰 📌 ✅ 📲. Máximo 2-3 por mensaje.
- Negrita con *asteriscos* estilo WhatsApp.
- Sin encabezados (#). Esto es chat.

FLUJO:
- Apertura: saluda, preséntate como Samuel y pregunta en qué ayudas.
- Discovery: si la pregunta es vaga, pregunta por qué programa o nivel le interesa.
- Cierre: cuando detectes intención de inscripción pide nombre completo, cédula, correo, ciudad y título de pregrado.
- Pago inscripción: https://www.mipagoamigo.com/MPA_WebSite/ServicePayments — Convenio: CORP TECNOLOGICA DE EDU SUPERIOR SAPIENZA CTE

═══════════════════════════════
BASE DE CONOCIMIENTO COMPLETA
═══════════════════════════════

## INSTITUCIÓN

- Nombre: Corporación Tecnológica de Educación Superior Sapienza — CTES
- Resolución fundación: 05050 del 22 de septiembre de 1993 (MEN)
- Resolución ciclos propedéuticos: 009404 del 27 de mayo de 2022
- Sede: Carrera 14A # 71-29, Barrios Unidos, Bogotá D.C.
- Web: https://sapienza.edu.co
- Teléfono: 601-265-0657
- WhatsApp institucional: 315-861-5888
- Email MEN: notificaciones.men@sapienza.edu.co
- Redes: @sapienza_colombia (Instagram, TikTok) · Sapienzacolombia (Facebook) · @usapienza (YouTube)
- Horario de atención: Lunes a viernes 8am–5pm · Sábados 8am–12pm
- Misión: Forma talento humano con principios éticos, morales, sociales, ambientales y sólidas competencias laborales.
- Plataforma académica: Q10 (campus virtual, pagos y matrículas)
- Créditos educativos: LEXCAPITAL Abogados & Inversiones S.A.S. desde 30/05/2025 · lexcapital01@sapienza.edu.co · Tel. 301 5125820

## PROGRAMAS DE PREGRADO

### Profesional en Administración de la Seguridad y Salud en el Trabajo
- Nivel: Profesional universitario
- Modalidad: Virtual
- Duración: 9 semestres · 144 créditos
- Costo: $2.100.000
- Inicio próxima cohorte: 30 de junio
- Resolución MEN: 010326
- Perfil: diseñar sistemas de gestión SST, investigar accidentes, formular políticas, consultoría pública y privada.
- Link: https://sapienza.edu.co/programa/profesional-en-administracion-de-la-seguridad-y-salud-en-el-trabajo/

### Tecnología en Gestión de la Seguridad y Salud en el Trabajo
- Nivel: Tecnólogo
- Modalidad: Virtual
- Duración: 5 semestres · 80 créditos
- Costo: $2.100.000
- Inicio próxima cohorte: 30 de junio
- Resolución MEN: 010325
- Perfil: implementar sistemas de gestión SST, identificar peligros, gestionar emergencias, investigar accidentes.
- Más de 1.500 egresados empleados en menos de 6 meses.
- Link: https://sapienza.edu.co/programa/tecnologia-en-gestion-de-la-seguridad-y-salud/

## TÉCNICOS LABORALES

- Auxiliar Contable y Financiero
- Investigador Criminalístico Judicial
- Auxiliar de Clínica Veterinaria
- Auxiliar Agrícola
- Recreación y Deportes
- Seguridad Ocupacional
- Auxiliar de Negocios Digitales
- Auxiliar Eléctrico
- Cocina Nacional e Internacional (distancia virtual · 2 semestres)

Para detalles de cada técnico: https://sapienza.edu.co/todos-los-programas/

## IDIOMAS

- Inglés A1, A2, B1, B2 (cursos de conocimientos académicos)
- Detalles: https://sapienza.edu.co/todos-los-programas/

## POSGRADOS

### Especialización en Gestión de Proyectos Estratégicos ⭐ (PROGRAMA PROPIO SAPIENZA)
- SNIES: 117669 · Resolución MEN: 018631 del 22/10/2024 · Vigencia: 7 años
- Modalidad: Virtual sincrónica (clases en vivo) + asincrónica. 100% virtual.
- Duración: 6 meses · 2 periodos · 24 créditos · 9 asignaturas (2 electivas)
- Horario: Nocturno · martes, miércoles y jueves · 6:30 p.m. – 9:45 p.m.
- Título: Especialista en Gestión de Proyectos Estratégicos (lo otorga Sapienza)
- Requisito de grado: trabajo/seminario aprobado + certificación inglés B1 (MCER)
- INVERSIÓN:
  · Inscripción: $116.061
  · Valor oficial MEN: $13.294.260
  · Valor con descuento promocional: $6.300.000 (vigente hasta 23 abril 2026)
  · Pago completo con 15% dto. adicional: $5.650.061
- Formas de pago: 50/50 por periodo · Credity sin intereses · Fincomercio · Valcredit · Comuna · ICETEX · cesantías · PSE · BRE-B · Nequi · tarjeta débito/crédito · Bolt
- Certificaciones incluidas: PMP–PMI · SCRUM / SCRUM Master / LEAN · ISO 21500 · ISO 31000 · MGA (Metodología General Ajustada)
- Plan de estudios Periodo 1: Formulación de proyectos · Estrategia y competitividad · Planificación y gestión de recursos y presupuestos · Electiva I (SCRUM o Habilidades Gerenciales)
- Plan de estudios Periodo 2: Gestión del desempeño y evaluación · Gerencia de proyectos · Gestión de calidad · Electiva II (ISO 21500/31000) · Seminario de Investigación
- Opciones de grado: certificación internacional · tesis sin costo · seminario de grado · grupo de investigación Sapienza
- Aplazamiento: máximo 1 año, una sola vez
- Devoluciones: Reglamento Estudiantil Acuerdo 007
- Pago inscripción: https://www.mipagoamigo.com/MPA_WebSite/ServicePayments · Convenio: CORP TECNOLOGICA DE EDU SUPERIOR SAPIENZA CTE
- Carga documentos: https://docs.google.com/forms/d/e/1FAIpQLSd9B7gDIJrBQwej4-qAtZWKoKcAfpThZ52i45fVh6W9b1662w/viewform

### MAESTRÍAS EN CONVENIO CON FUAC (Universidad Autónoma de Colombia)
IMPORTANTE: El título de TODAS las maestrías lo otorga FUAC. Sapienza opera el convenio comercial.
- Homologación 50%: aplica si tienes especialización afín. Se determina una vez matriculado. Con homologación: 2 periodos (vs 4 completos).
- Sin homologación 50%: solo curso de nivelación FUAC, costo total $2.104.925.
- Modalidad: Presencial Asistida (clase en vivo sincronizada, NO queda grabada).
- Financiación: Credity sin intereses · Fincomercio · Valcredit · Comuna · ICETEX · cesantías · PSE · tarjeta débito/crédito.
- Inglés: homologable con certificación B1 vigente que cumpla criterios FUAC (adjuntar notas y contenidos programáticos).

#### Maestría en Administración de Negocios Internacionales
- SNIES: 107703 · Resolución: 2108
- Duración: 4 semestres · 98 créditos
- Costo: $7.629.797
- Modalidad: Distancia con estrategia virtual
- Perfil: dirigir y gestionar organizaciones en entorno global, estrategia internacional, finanzas, logística, liderazgo.
- Link: https://sapienza.edu.co/programa/maestria-administracion-de-negocios-internacionales-en-convenio-con-universidad-autonoma-de-colombia/

#### Maestría en Derecho Público
- SNIES: 106892 · Resolución: 6108
- Duración: 4 semestres · 98 créditos
- Costo: $7.743.906
- Modalidad: Distancia con estrategia virtual
- Perfil: derecho constitucional, administrativo, financiero, ambiental, derechos humanos, gestión pública.
- Link: https://sapienza.edu.co/programa/maestria-en-derecho-publico-en-convenio-con-universidad-autonoma-de-colombia/

#### Maestría en Derecho Laboral y Seguridad Social
- SNIES: 107392 · Resolución: 20775
- Duración: 4 semestres · 98 créditos
- Costo: $7.743.906
- Modalidad: Distancia con estrategia virtual
- Perfil: abierta a cualquier profesional (abogados, psicólogos, médicos, ingenieros, administradores, etc.) con interés en derecho laboral.
- Link: https://sapienza.edu.co/programa/maestria-en-derecho-laboral-y-seguridad-social-en-convenio-con-universidad-autonoma-de-colombia/

#### Maestría en Desarrollo de Productos Sustentables
- SNIES: 106524 · Resolución: 20775
- Duración: 4 semestres · 98 créditos
- Costo: $7.537.845
- Modalidad: Distancia con estrategia virtual
- Perfil: ingenieros, diseñadores, ciencias ambientales. Innovación sostenible, economía circular, gestión de cadenas de valor.
- Link: https://sapienza.edu.co/programa/maestria-en-desarrollo-de-productos-sustentable-en-convenio-con-universidad-autonoma-de-colombia/

## PROCESO DE ADMISIÓN (POSGRADOS)

Documentos requeridos:
- Fotocopia cédula de ciudadanía (ampliada al 150%)
- Diploma y acta de grado de pregrado
- Resultado Prueba Saber 11
- Foto reciente tamaño 3x4 (digital)
- Certificación EPS o Sisbén
- Comprobante pago inscripción ($116.061)
- Formato de matrícula Sapienza
- Acta de compromiso si hay documentos pendientes (plazo 1 mes)

Carga de documentos: https://docs.google.com/forms/d/e/1FAIpQLSd9B7gDIJrBQwej4-qAtZWKoKcAfpThZ52i45fVh6W9b1662w/viewform
Pago inscripción: https://www.mipagoamigo.com/MPA_WebSite/ServicePayments"""

# Historial por número de teléfono
# Formato: { phone: { history: [...], lead_data: {...} } }
sessions = {}

def call_gemini(history):
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': history,
        'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 600}
    }).encode()
    req = urllib.request.Request(get_api_url(), data=body,
                                  headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data['candidates'][0]['content']['parts'][0]['text']

def send_whatsapp(to, body_text, account_sid, auth_token):
    url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
    data = urllib.parse.urlencode({
        'From': 'whatsapp:+14155238886',
        'To': to,
        'Body': body_text
    }).encode()
    credentials = f'{account_sid}:{auth_token}'
    import base64
    b64 = base64.b64encode(credentials.encode()).decode()
    req = urllib.request.Request(url, data=data,
                                  headers={'Authorization': f'Basic {b64}',
                                           'Content-Type': 'application/x-www-form-urlencoded'},
                                  method='POST')
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def extract_crm_action(text):
    """Extrae el bloque ```crm_action ... ``` del texto de Samuel y retorna (texto_limpio, dict_accion)."""
    pattern = r'```crm_action\s*([\s\S]*?)```'
    match = re.search(pattern, text)
    if not match:
        return text, None
    raw_json = match.group(1).strip()
    clean_text = re.sub(pattern, '', text).strip()
    try:
        action = json.loads(raw_json)
        return clean_text, action
    except Exception:
        return clean_text, None

def call_crm(action_dict, phone_number):
    """Envía la acción al Apps Script del CRM."""
    crm_url = get_crm_url()
    if not crm_url:
        print('[CRM] APPS_SCRIPT_URL no configurada, omitiendo.')
        return None

    # Agregar teléfono si no viene en el dict
    if 'telefono' not in action_dict:
        # Quitar prefijo 'whatsapp:' si viene de Twilio
        phone = phone_number.replace('whatsapp:', '').strip()
        action_dict['telefono'] = phone

    action_dict['secret'] = get_bot_secret()

    body = json.dumps(action_dict).encode()
    try:
        req = urllib.request.Request(crm_url, data=body,
                                      headers={'Content-Type': 'application/json'},
                                      method='POST')
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            print(f'[CRM] {result}')

            # Guardar rowNumber en sesión para acciones futuras (agendar_cita)
            return result
    except Exception as e:
        print(f'[CRM] Error al llamar Apps Script: {e}')
        return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{args[0]}] {args[1]}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/' or path == '/index.html':
            self._serve_file('index.html', 'text/html; charset=utf-8')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)

        # Webhook de Twilio WhatsApp
        if self.path == '/whatsapp':
            params = dict(urllib.parse.parse_qsl(raw.decode()))
            from_number = params.get('From', '')
            user_text = params.get('Body', '').strip()
            print(f"WhatsApp [{from_number}]: {user_text}")

            account_sid, auth_token = get_twilio_creds()

            if from_number not in sessions:
                sessions[from_number] = {'history': [], 'lead_data': {}, 'row_number': None}

            sessions[from_number]['history'].append(
                {'role': 'user', 'parts': [{'text': user_text}]}
            )

            try:
                raw_reply = call_gemini(sessions[from_number]['history'])
                clean_reply, crm_action = extract_crm_action(raw_reply)

                sessions[from_number]['history'].append(
                    {'role': 'model', 'parts': [{'text': raw_reply}]}
                )

                # Procesar acción CRM en background (no bloquea la respuesta)
                if crm_action:
                    try:
                        if crm_action.get('action') == 'agendar_cita' and sessions[from_number].get('row_number'):
                            crm_action['rowNumber'] = sessions[from_number]['row_number']
                        result = call_crm(crm_action, from_number)
                        if result and result.get('ok') and result.get('rowNumber'):
                            sessions[from_number]['row_number'] = result['rowNumber']
                    except Exception as crm_err:
                        print(f'[CRM] Error no crítico: {crm_err}')

                if account_sid and auth_token:
                    send_whatsapp(from_number, clean_reply, account_sid, auth_token)

            except Exception as e:
                print(f'[ERROR whatsapp handler] {e}')
                clean_reply = 'Hola, tuve un problema técnico. Por favor escribe de nuevo en un momento 🙏'
                try:
                    if account_sid and auth_token:
                        send_whatsapp(from_number, clean_reply, account_sid, auth_token)
                except Exception:
                    pass

            self.send_response(200)
            self.send_header('Content-Type', 'text/xml')
            self.end_headers()
            self.wfile.write(b'<?xml version="1.0" encoding="UTF-8"?><Response></Response>')
            return

        # API del chat web
        if self.path == '/chat':
            try:
                body = json.loads(raw)
                req = urllib.request.Request(
                    get_api_url(), data=json.dumps(body).encode(),
                    headers={'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(req) as r:
                    result = r.read()
                self.send_response(200)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            except urllib.error.HTTPError as e:
                err = e.read()
                self.send_response(e.code)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err)
            return

        self.send_response(404)
        self.end_headers()

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _serve_file(self, filename, ctype):
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)


def keep_alive():
    """Hace ping al propio servidor cada 14 minutos para evitar el sleep de Render."""
    time.sleep(60)  # espera 1 min al arrancar antes del primer ping
    while True:
        try:
            url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:8080')
            urllib.request.urlopen(f'{url}/', timeout=10)
            print('[keep-alive] ping OK')
        except Exception as e:
            print(f'[keep-alive] {e}')
        time.sleep(14 * 60)

if __name__ == '__main__':
    threading.Thread(target=keep_alive, daemon=True).start()
    print('Servidor corriendo en http://localhost:8080')
    HTTPServer(('', 8080), Handler).serve_forever()
