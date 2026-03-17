import json
from openai import OpenAI
from generator import generar_solicitante_aleatorio
from agents import AgenteLLM
from ministerio import Ministerio
import config

class MotorPapersPlease:
    """
    Motor principal que orquesta la simulación entre el Entorno, 
    el Solicitante y el Inspector.
    """
    def __init__(self, cliente_ai: OpenAI, modelo: str):
        self.cliente_ai = cliente_ai
        self.modelo = modelo
        self.saldo_creditos = config.CREDITOS_INICIALES
        self.dia_actual = 1
        self.reglas_del_dia = ""

    def iniciar_dia(self, dia: int):
        """Prepara las reglas y el entorno para un nuevo día."""
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
        
        # 1. Obtener datos pasando el día actual
        datos = generar_solicitante_aleatorio(self.dia_actual)
        docs_json = json.dumps(datos['documentos'], indent=2, ensure_ascii=False)
        
        # 2. Instanciar Agentes
        solicitante = self._crear_solicitante(datos, docs_json)
        inspector = self._crear_inspector(docs_json)

        # 3. Iniciar diálogo
        saludo = solicitante.enviar_mensaje("Acabas de llegar a la ventanilla del inspector. Di tu primera frase y entrégale los documentos.")
        print(f"[Solicitante]: {saludo}")
        
        mensaje_para_inspector = f"El solicitante dice: '{saludo}'. Haz tu análisis y decide si preguntar algo o emitir veredicto en JSON."
        
        # 4. Bucle de interrogatorio
        for i in range(config.TURNOS_MAXIMOS_INTERROGATORIO):
            respuesta_inspector = inspector.enviar_mensaje(mensaje_para_inspector)
            print(f"\n[Inspector]: {respuesta_inspector}")
            
            # Comprobar si emitió un veredicto estructurado
            if "{" in respuesta_inspector and "decision" in respuesta_inspector.lower():
                self.evaluar_veredicto(respuesta_inspector, datos['es_valido'])
                return
            
            respuesta_solicitante = solicitante.enviar_mensaje(respuesta_inspector)
            print(f"\n[Solicitante]: {respuesta_solicitante}")
            mensaje_para_inspector = f"El solicitante responde: '{respuesta_solicitante}'."

        # 5. Fin de tiempo (Forzar decisión)
        print("\n[Sistema]: Forzando decisión por falta de tiempo...")
        veredicto_forzado = inspector.enviar_mensaje("Se acabó el tiempo. Emite tu decisión final AHORA en formato JSON.")
        print(f"\n[Inspector]: {veredicto_forzado}")
        self.evaluar_veredicto(veredicto_forzado, datos['es_valido'])

    def _crear_solicitante(self, datos: dict, docs_json: str) -> AgenteLLM:
        prompt = f"""
        Eres un ciudadano intentando cruzar la frontera de Arstotzka.
        Tu personalidad es: {datos['personalidad']}.
        Tus documentos son: {docs_json}.
        Tu situación real es: {datos['motivo_oculto']}.
        Responde siempre de forma corta y conversacional. Si algo está mal, miente o justifícate.
        """
        return AgenteLLM(self.cliente_ai, self.modelo, prompt)

    def _crear_inspector(self, docs_json: str) -> AgenteLLM:
        prompt = f"""
        Eres el Inspector de Aduanas de Arstotzka. Eres frío y burocrático.
        Reglas de hoy: {self.reglas_del_dia}
        Documentos presentados: {docs_json}
        
        Interroga si ves anomalías.
        Cuando decidas, DEBES responder ÚNICAMENTE con un JSON en este formato exacto:
        {{"decision": "APROBAR" o "DENEGAR", "motivo": "explicación"}}
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
            print("\n⚠️ [Error]: El Inspector no generó un JSON válido. -5 créditos.")
            self.saldo_creditos -= 5