import io
import re
import json
import random
import asyncio
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from thinking model output."""
    if not text:
        return ""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    return cleaned if cleaned else text.strip()

import config
from generator import generar_solicitante_aleatorio
from ministerio_neo4j import ministerio_db
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image

app = FastAPI(title="Papers Please - AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CNNBase(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv4 = nn.Conv2d(128, 256, 3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.conv5 = nn.Conv2d(256, 512, 3, padding=1)
        self.bn5 = nn.BatchNorm2d(512)
        self.conv6 = nn.Conv2d(512, 512, 3, padding=1)
        self.bn6 = nn.BatchNorm2d(512)
        self.fc1 = nn.Linear(4608, 512)
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(512, 128)
        
    def forward(self, x):
        x = F.max_pool2d(F.relu(self.bn1(self.conv1(x))), 2)
        x = F.max_pool2d(F.relu(self.bn2(self.conv2(x))), 2)
        x = F.max_pool2d(F.relu(self.bn3(self.conv3(x))), 2)
        x = F.max_pool2d(F.relu(self.bn4(self.conv4(x))), 2)
        x = F.max_pool2d(F.relu(self.bn5(self.conv5(x))), 2)
        x = F.max_pool2d(F.relu(self.bn6(self.conv6(x))), 2)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        # L2 normalization is fundamental for distance metrics as trained
        x = F.normalize(x, p=2, dim=1)
        return x

class SiameseNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn = CNNBase()

    def forward(self, x1, x2=None):
        out1 = self.cnn(x1)
        if x2 is not None:
            out2 = self.cnn(x2)
            return out1, out2
        return out1

# Load model globally
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = SiameseNetwork()
state_dict = torch.load('modelo_cnn/modelo_verificacion_facial_frontera_v3.pth', map_location=device)
model.load_state_dict(state_dict)
model.to(device)
model.eval()

transform = transforms.Compose([
    transforms.Resize((250, 250)),
    transforms.ToTensor(),
])

@app.post("/api/verify-faces")
async def verify_faces(image1: UploadFile = File(...), image2: UploadFile = File(...)):
    contents1 = await image1.read()
    contents2 = await image2.read()
    
    img1 = Image.open(io.BytesIO(contents1)).convert('L')
    img2 = Image.open(io.BytesIO(contents2)).convert('L')
    
    t1 = transform(img1).unsqueeze(0).to(device)
    t2 = transform(img2).unsqueeze(0).to(device)
    
    with torch.no_grad():
        out1, out2 = model(t1, t2)
        
    euclidean_distance = F.pairwise_distance(out1, out2)
    distance = euclidean_distance.item()
        
    # Determine match based on distance (threshold can be adjusted)
    threshold = 1.0 
    is_match = distance < threshold
        
    return {
        "match": is_match,
        "distance": distance,
        "threshold": threshold
    }

class AsyncAgenteLLM:
    def __init__(self, cliente, modelo, system_prompt):
        self.cliente = cliente
        self.modelo = modelo
        self.historial = [{"role": "system", "content": system_prompt}]
        
    async def enviar_mensaje(self, mensaje):
        self.historial.append({"role": "user", "content": mensaje})
        try:
            respuesta = await self.cliente.chat.completions.create(
                model=self.modelo,
                messages=self.historial,
                temperature=0.7
            )
            contenido = respuesta.choices[0].message.content or ""
            contenido = strip_thinking(contenido)
            self.historial.append({"role": "assistant", "content": contenido})
            return contenido
        except Exception as e:
            return f'{{"decision": "ERROR", "motivo": "{str(e)}"}}'

@app.websocket("/api/ws/simulation")
async def websocket_simulation(websocket: WebSocket):
    await websocket.accept()
    cliente_ai = AsyncOpenAI(base_url=config.OLLAMA_BASE_URL, api_key=config.OLLAMA_API_KEY)
    
    try:
        data = await websocket.receive_text()
        msg = json.loads(data)
        if msg.get("action") == "start":
            mode = msg.get("mode", "simulation")
            cnn_result = msg.get("cnnResult")
            dia = random.randint(1, config.DIAS_TOTALES)
            reglas = ministerio_db.obtener_reglas_del_dia(dia)
            datos = generar_solicitante_aleatorio(dia)
            docs_json = json.dumps(datos['documentos'], indent=2, ensure_ascii=False)
            
            # Convert docs dict to list for frontend
            docs_list = [{"tipo": k, **v} if isinstance(v, dict) else {"tipo": k, "valor": v}
                         for k, v in datos['documentos'].items()]
            
            # Send initial setup info
            await websocket.send_text(json.dumps({
                "sender": "system",
                "action": "setup",
                "data": {
                    "rules": reglas,
                    "docs": docs_list,
                    "es_valido": datos['es_valido']
                }
            }, ensure_ascii=False))
            
            info_facial = ""
            if cnn_result:
                coincidencia = "SÍ coinciden" if cnn_result.get("match") else "NO coinciden (POSIBLE FRAUDE)"
                info_facial = f"\n\nRESULTADO DEL ESCÁNER FACIAL:\n- ¿Coincide la cara de la persona en la ventanilla con la foto del pasaporte? -> {coincidencia}"

            # ── Inspector Prompt (from engine.py) ──
            prompt_inspector = f"""ERES UN INSPECTOR DE ADUANAS DE ARSTOTZKA. Eres frío, burocrático y estricto. Hablas en español.

REGLA DEL TIEMPO:
- TÚ VIVES EN EL AÑO 1982. El año actual de tu mundo es EXACTAMENTE {config.FECHA_ACTUAL}.
- ¡NUNCA asumas que estás en los años 2000s! 
- Si la fecha de caducidad de un documento es "1983", "1984", "1985"... significa que caducará en el FUTURO. Por lo tanto, el documento es VÁLIDO HOY (1982).
- Si la fecha de caducidad es "1981" o anterior... significa que caducó en el PASADO. El documento es INVÁLIDO.
- ¡NO DIGAS que un documento de 1984 está caducado! Eso es un error grave.

REGLAS DE HOY:
{reglas}

DOCUMENTOS PRESENTADOS POR EL CIUDADANO: 
{docs_json}{info_facial}

INSTRUCCIONES:
En tu turno haz UNA sola cosa:

OPCIÓN 1 - INTERROGAR: 
- Si ves un error REAL (fechas pasadas, nacionalidad prohibida, cara que no coincide), haz UNA pregunta directa exigiendo explicación.
- Si NO ves errores y el ciudadano es EXTRANJERO (no es de Arstotzka), haz UNA pregunta de rutina obligatoria (ej: motivos de viaje, tiempo de estancia).
No escribas nada más que la pregunta.

OPCIÓN 2 - EMITIR VEREDICTO: 
- Si el ciudadano ES DE ARSTOTZKA, NO DEBES HACER NINGÚN INTERROGATORIO de rutina. Aprueba inmediatamente si sus papeles y foto están bien.
- Si el ciudadano es extranjero y ya respondió a tus preguntas de rutina y todo está bien, aprueba.
- Si hay un error obvio e imperdonable para cualquiera (pasaporte caducado, cara que no coincide), deniega.
Responde ÚNICAMENTE con el bloque JSON de tu decisión.

FORMATOS DE VEREDICTO PERMITIDOS:
{{"decision": "APROBAR", "motivo": "Todo en regla"}}
O
{{"decision": "DENEGAR", "motivo": "Motivo corto"}}"""
            
            # ── Citizen Prompt (does NOT reveal document problems) ──
            nombre = datos['documentos'].get('pasaporte', {}).get('nombre', 'Ciudadano')
            pais = datos['documentos'].get('pasaporte', {}).get('nacionalidad', 'desconocido')
            personalidad = datos['personalidad']
            
            prompt_entrant = f"""Eres {nombre}, un ciudadano de {pais} que intenta cruzar la frontera de Arstotzka.
Personalidad: {personalidad}.
¡REGLA CRÍTICA DEL TIEMPO!: El año actual es 1982. Actúa como si vivieras en la década de los 80s. ¡Nunca asumas que estás en los 2000s!

Tu objetivo es CRUZAR LA FRONTERA. Crees que tus papeles están en orden (aunque quizás no lo estén).
NO conoces las reglas del inspector. NO sabes si tu pasaporte está caducado o no.
Si el inspector te pregunta algo, responde con naturalidad según tu personalidad.
Si te acusan de algo, defiéndete o suplica, pero NUNCA admitas que algo está mal con tus documentos.
Responde siempre en español, corto (1-2 oraciones máximo). Mantén tu personaje."""
            
            # ── Helper to extract verdict ──
            async def extract_and_send_verdict(text):
                if "{" in text and ("APROBAR" in text.upper() or "DENEGAR" in text.upper()):
                    try:
                        inicio = text.find("{")
                        fin = text.rfind("}") + 1
                        veredicto = json.loads(text[inicio:fin])
                        await websocket.send_text(json.dumps({
                            "sender": "system", "action": "verdict",
                            "data": veredicto
                        }, ensure_ascii=False))
                        return True
                    except Exception as e:
                        print(f"Error extrayendo JSON veredicto: {e}")
                return False
            
            # ═══════════════════════════════════════
            # MODE: SIMULATION (Agent vs Agent)
            # ═══════════════════════════════════════
            if mode == "simulation":
                inspector = AsyncAgenteLLM(cliente_ai, config.MODELO_LLM, prompt_inspector)
                entrant = AsyncAgenteLLM(cliente_ai, config.MODELO_LLM, prompt_entrant)
                
                # Citizen approaches and greets
                saludo = await entrant.enviar_mensaje("Acabas de llegar a la ventanilla del inspector. Salúdale brevemente y dile que traes tus papeles.")
                print(f"[SIM] Entrant: {saludo[:120]}")
                await websocket.send_text(json.dumps({"sender": "entrant", "text": saludo}, ensure_ascii=False))
                
                mensaje_para_inspector = f"El ciudadano se acerca, entrega los documentos y dice: '{saludo}'. Analiza todo."
                
                for turno in range(config.TURNOS_MAXIMOS_INTERROGATORIO):
                    resp_insp = await inspector.enviar_mensaje(mensaje_para_inspector)
                    print(f"[SIM] Inspector (turno {turno+1}): {resp_insp[:120]}")
                    await websocket.send_text(json.dumps({"sender": "inspector", "text": resp_insp}, ensure_ascii=False))
                    
                    if await extract_and_send_verdict(resp_insp):
                        break
                        
                    resp_cit = await entrant.enviar_mensaje(f"El inspector te dice: '{resp_insp}'")
                    print(f"[SIM] Entrant: {resp_cit[:120]}")
                    await websocket.send_text(json.dumps({"sender": "entrant", "text": resp_cit}, ensure_ascii=False))
                    
                    mensaje_para_inspector = f"El ciudadano responde: '{resp_cit}'."
                else:
                    # Force verdict after max turns
                    veredicto_forzado = await inspector.enviar_mensaje("Se acabó el tiempo. EMITE TU VEREDICTO FINAL USANDO SOLO EL JSON.")
                    print(f"[SIM] Inspector (forzado): {veredicto_forzado[:120]}")
                    await websocket.send_text(json.dumps({"sender": "inspector", "text": veredicto_forzado}, ensure_ascii=False))
                    await extract_and_send_verdict(veredicto_forzado)
                    
            # ═══════════════════════════════════════
            # MODE: PLAY_GUARD (User is Inspector)
            # ═══════════════════════════════════════
            elif mode == "play_guard":
                entrant = AsyncAgenteLLM(cliente_ai, config.MODELO_LLM, prompt_entrant)
                saludo = await entrant.enviar_mensaje("Acabas de llegar a la ventanilla del inspector. Salúdale brevemente y dile que traes tus papeles.")
                print(f"[GUARD] Entrant: {saludo[:120]}")
                await websocket.send_text(json.dumps({"sender": "entrant", "text": saludo}, ensure_ascii=False))
                
                while True:
                    user_msg = json.loads(await websocket.receive_text())
                    if user_msg.get("action") == "message":
                        resp_cit = await entrant.enviar_mensaje(f"El inspector te dice: '{user_msg['text']}'")
                        print(f"[GUARD] Entrant: {resp_cit[:120]}")
                        await websocket.send_text(json.dumps({"sender": "entrant", "text": resp_cit}, ensure_ascii=False))
                    elif user_msg.get("action") == "verdict":
                        await websocket.send_text(json.dumps({
                            "sender": "system", "action": "verdict", "data": user_msg["data"]
                        }, ensure_ascii=False))
                        break
                        
            # ═══════════════════════════════════════
            # MODE: PLAY_CITIZEN (User is Citizen)
            # ═══════════════════════════════════════
            elif mode == "play_citizen":
                inspector = AsyncAgenteLLM(cliente_ai, config.MODELO_LLM, prompt_inspector)
                # Inspector waits, user speaks first
                await websocket.send_text(json.dumps({"sender": "inspector", "text": "Siguiente. Papeles, por favor."}, ensure_ascii=False))
                
                while True:
                    user_msg = json.loads(await websocket.receive_text())
                    if user_msg.get("action") == "message":
                        ctx = f"El ciudadano se acerca, entrega los documentos y dice: '{user_msg['text']}'. Analiza todo."
                        resp_insp = await inspector.enviar_mensaje(ctx)
                        print(f"[CITIZEN] Inspector: {resp_insp[:120]}")
                        
                        await websocket.send_text(json.dumps({"sender": "inspector", "text": resp_insp}, ensure_ascii=False))
                        
                        if await extract_and_send_verdict(resp_insp):
                            break
            
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
