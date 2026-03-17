from openai import OpenAI

class AgenteLLM:
    """
    Clase base para gestionar agentes conversacionales usando un LLM.
    Mantiene el historial de la conversación para dar contexto.
    """
    def __init__(self, cliente: OpenAI, modelo: str, system_prompt: str):
        self.cliente = cliente
        self.modelo = modelo
        self.system_prompt = system_prompt
        self.historial = [{"role": "system", "content": system_prompt}]

    def enviar_mensaje(self, mensaje_usuario: str) -> str:
        """
        Envía un mensaje al LLM, guarda el historial y devuelve la respuesta.
        """
        self.historial.append({"role": "user", "content": mensaje_usuario})
        
        try:
            respuesta = self.cliente.chat.completions.create(
                model=self.modelo,
                messages=self.historial,
                temperature=0.7
            )
            
            contenido = respuesta.choices[0].message.content
            self.historial.append({"role": "assistant", "content": contenido})
            return contenido
            
        except Exception as e:
            error_msg = f"Error al comunicar con el LLM: {str(e)}"
            print(f"\n[Sistema]: {error_msg}")
            return '{"decision": "ERROR", "motivo": "Fallo de conexión"}'