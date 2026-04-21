# engine.py
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
        print("Siguiente en la fila... ¡Eres tú!")
        print("="*50)
        
        datos = generar_solicitante_aleatorio(self.dia_actual)
        docs_json = json.dumps(datos['documentos'], indent=2, ensure_ascii=False)
        
        print("\n🛂 [TUS DOCUMENTOS Y SITUACIÓN]")
        print(f"Documentos que llevas: {docs_json}")
        print(f"Tu objetivo secreto: {datos['motivo_oculto']}")
        print(f"Personalidad sugerida (roleplay): {datos['personalidad']}")
        print("-" * 50)
        
        inspector = self._crear_inspector(docs_json)

        saludo = input("\n[Tú (Ciudadano)]: ")
        mensaje_para_inspector = f"El ciudadano se acerca, entrega los documentos y dice: '{saludo}'. Analiza todo."
        
        for i in range(config.TURNOS_MAXIMOS_INTERROGATORIO):
            respuesta_inspector = inspector.enviar_mensaje(mensaje_para_inspector)
            print(f"\n[Inspector IA]: {respuesta_inspector}")
            
            es_veredicto = "{" in respuesta_inspector and ("aprobar" in respuesta_inspector.lower() or "denegar" in respuesta_inspector.lower())
            
            if es_veredicto:
                self.evaluar_veredicto(respuesta_inspector, datos['es_valido'])
                return
            
            tu_respuesta = input("\n[Tú (Ciudadano)]: ")
            mensaje_para_inspector = f"El ciudadano responde: '{tu_respuesta}'."

        print("\n[Sistema]: Forzando decisión del Inspector por falta de tiempo...")
        veredicto_forzado = inspector.enviar_mensaje("Se acabó el tiempo. EMITE TU VEREDICTO FINAL USANDO SOLO EL JSON.")
        print(f"\n[Inspector IA]: {veredicto_forzado}")
        self.evaluar_veredicto(veredicto_forzado, datos['es_valido'])

    def _crear_inspector(self, docs_json: str) -> AgenteLLM:
        prompt = f"""
        Eres un Inspector de Aduanas de Arstotzka. Eres un funcionario burocrático, aburrido, profesional y estricto. 
        Hablas con frialdad y cortesía oficial, sin dramatismos ni insultos.
        
        MATEMÁTICA TEMPORAL (¡MUY IMPORTANTE LEER BIEN!):
        - Hoy estamos en el AÑO 1982 (Fecha: {config.FECHA_ACTUAL}).
        - Si un documento dice caducidad en "1983", "1984", etc., eso es el FUTURO. Significa que el documento ES VÁLIDO y NO ESTÁ CADUCADO.
        - Si un documento dice caducidad en "1981", "1980", etc., eso es el PASADO. Significa que ESTÁ CADUCADO e INVÁLIDO.
        
        REGLAS DE HOY:
        {self.reglas_del_dia}
        
        DOCUMENTOS PRESENTADOS POR EL CIUDADANO: 
        {docs_json}
        
        INSTRUCCIONES:
        En tu turno haz UNA sola cosa:
        
        OPCIÓN 1 - INTERROGAR: Si ves un error REAL (basado en la matemática temporal correcta o falta de papeles), haz UNA pregunta corta y profesional en español. Ejemplo: "Ciudadano, su pasaporte caducó en 1981, ¿qué tiene que decir?". No escribas nada más que la pregunta.
        
        OPCIÓN 2 - EMITIR VEREDICTO: Si ya decidiste, responde ÚNICAMENTE con el bloque JSON.
        
        FORMATOS DE VEREDICTO PERMITIDOS:
        {{"decision": "APROBAR", "motivo": "Todo en regla"}}
        O
        {{"decision": "DENEGAR", "motivo": "Motivo corto"}}
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
                print("\n✅ [Ministerio evalúa al Inspector]: El Inspector acertó. La IA gana +5 créditos.")
                self.saldo_creditos += 5
                if not era_valido:
                     print("👉 ¡La IA te ha pillado mintiendo!")
            else:
                print("\n❌ [Ministerio evalúa al Inspector]: CITACIÓN. El Inspector falló. -10 créditos.")
                self.saldo_creditos -= 10
                if not era_valido and decision == "APROBAR":
                     print("👉 ¡Lograste engañar a la IA y cruzaste la frontera con papeles falsos!")
                
            print(f"Saldo del Inspector (IA): {self.saldo_creditos} créditos")
            
        except json.JSONDecodeError:
            print("\n⚠️ [Error]: El Inspector no generó un JSON válido. Penalización: -5 créditos.")
            self.saldo_creditos -= 5