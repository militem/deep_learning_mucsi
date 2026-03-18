import json
from openai import OpenAI
from generator import generar_solicitante_aleatorio
from agents import AgenteLLM
from ministerio import Ministerio
import config

class MotorPapersPlease:
    def __init__(self, cliente_ai: OpenAI, modelo: str):
        self.cliente_ai = cliente_ai
        self.modelo = modelo
        self.saldo_creditos = config.CREDITOS_INICIALES
        self.dia_actual = 1
        self.reglas_del_dia = ""

    def iniciar_dia(self, dia: int):
        self.dia_actual = dia
        self.reglas_del_dia = Ministerio.obtener_reglas(dia)
        print(f"\n" + "★"*50)
        print(f"★ INICIANDO DÍA {self.dia_actual} ★")
        print(f"★ Boletín del Ministerio:")
        print(f"{self.reglas_del_dia}")
        print("★"*50)

    def jugar_turno(self):
        print("\n" + "="*50)
        print("Siguiente en la fila...")
        print("="*50)
        
        datos = generar_solicitante_aleatorio(self.dia_actual)
        docs_json = json.dumps(datos['documentos'], indent=2, ensure_ascii=False)
        
        solicitante = self._crear_solicitante(datos, docs_json)
        inspector = self._crear_inspector(docs_json)

        saludo = solicitante.enviar_mensaje("Acabas de llegar a la ventanilla. Di una frase corta saludando y entregando los documentos.")
        print(f"[Solicitante]: {saludo}")
        
        mensaje_para_inspector = f"El solicitante dice: '{saludo}'. Haz tu análisis visualizando la fecha actual."
        
        for i in range(config.TURNOS_MAXIMOS_INTERROGATORIO):
            respuesta_inspector = inspector.enviar_mensaje(mensaje_para_inspector)
            print(f"\n[Inspector]: {respuesta_inspector}")
            
            # === MEJORA: Detección estricta del veredicto ===
            # Solo evalúa si encuentra el JSON *y* contiene específicamente APROBAR o DENEGAR
            es_veredicto = "{" in respuesta_inspector and ("aprobar" in respuesta_inspector.lower() or "denegar" in respuesta_inspector.lower())
            
            if es_veredicto:
                self.evaluar_veredicto(respuesta_inspector, datos['es_valido'])
                return
            
            # Si no ha dado veredicto, es porque le ha hecho una pregunta al ciudadano
            respuesta_solicitante = solicitante.enviar_mensaje(respuesta_inspector)
            print(f"\n[Solicitante]: {respuesta_solicitante}")
            mensaje_para_inspector = f"El solicitante responde: '{respuesta_solicitante}'."

        print("\n[Sistema]: Forzando decisión por falta de tiempo...")
        veredicto_forzado = inspector.enviar_mensaje("Se acabó el tiempo de interrogatorio. EMITE TU VEREDICTO FINAL AHORA MISMO USANDO SOLO EL FORMATO JSON.")
        print(f"\n[Inspector]: {veredicto_forzado}")
        self.evaluar_veredicto(veredicto_forzado, datos['es_valido'])

    def _crear_solicitante(self, datos: dict, docs_json: str) -> AgenteLLM:
        prompt = f"""
        Eres un ciudadano en 1982 intentando cruzar la frontera de Arstotzka.
        Tu personalidad es: {datos['personalidad']}.
        Tus documentos (en formato JSON) son: {docs_json}.
        Tu situación real es: {datos['motivo_oculto']}.
        Responde siempre en ESPAÑOL, de forma muy corta (1 o 2 líneas). Si algo está mal en tus papeles, inventa una excusa rápidamente.
        """
        return AgenteLLM(self.cliente_ai, self.modelo, prompt)

    def _crear_inspector(self, docs_json: str) -> AgenteLLM:
        prompt = f"""
        Eres el Inspector de Aduanas de Arstotzka. Eres frío y burocrático. Debes pensar lógicamente.
        
        CONTEXTO TEMPORAL IMPORTANTE:
        La fecha de hoy es: {config.FECHA_ACTUAL}
        (Cualquier fecha anterior a hoy significa CADUCADO/INVÁLIDO. Si es posterior, es VÁLIDO).
        
        REGLAS DE HOY:
        {self.reglas_del_dia}
        
        DOCUMENTOS PRESENTADOS: 
        {docs_json}
        
        INSTRUCCIONES DE ACCIÓN:
        En tu turno solo puedes hacer UNA de estas dos cosas:
        
        OPCIÓN 1 - INTERROGAR: Si detectas que falta un papel o hay un documento caducado, hazle una pregunta directa al ciudadano en español (ej. "¿Por qué falta su permiso?"). Escribe solo tu pregunta.
        
        OPCIÓN 2 - EMITIR VEREDICTO: Si ya tienes clara tu decisión, DEBES responder ÚNICAMENTE con un bloque JSON estricto. NADA de texto extra, ni saludos, solo el JSON. Solo puedes elegir entre "APROBAR" o "DENEGAR".
        
        FORMATO ESTRICTO DEL VEREDICTO:
        {{"decision": "APROBAR", "motivo": "Todo está en regla"}}
        O
        {{"decision": "DENEGAR", "motivo": "Explicación de la norma infringida"}}
        """
        return AgenteLLM(self.cliente_ai, self.modelo, prompt)

    def evaluar_veredicto(self, veredicto_json_str: str, era_valido: bool):
        try:
            inicio = veredicto_json_str.find("{")
            fin = veredicto_json_str.rfind("}") + 1
            json_limpio = veredicto_json_str[inicio:fin]
            
            decision_data = json.loads(json_limpio)
            decision = decision_data.get("decision", "").upper()
            
            es_correcta = (decision == "APROBAR" and era_valido) or (decision == "DENEGAR" and not era_valido)
            
            if es_correcta:
                print("\n✅ [Ministerio]: Decisión CORRECTA. +5 créditos.")
                self.saldo_creditos += 5
            else:
                print("\n❌ [Ministerio]: CITACIÓN. Decisión INCORRECTA. -10 créditos.")
                self.saldo_creditos -= 10
                
            print(f"Saldo actual: {self.saldo_creditos} créditos")
            
        except json.JSONDecodeError:
            print("\n [Error]: El Inspector no generó un JSON válido. Penalización: -5 créditos.")
            self.saldo_creditos -= 5