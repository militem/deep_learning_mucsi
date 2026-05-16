"""
Configuración global del proyecto.
Ajustado para funcionar con Ollama localmente.
"""

# Configuración de Ollama (Usa el puerto por defecto de Ollama)
OLLAMA_BASE_URL = "http://192.168.1.151:1234/v1"
OLLAMA_API_KEY = "no-key"

# Modelo a utilizar
# MODELO_LLM = "llama3"
# "qwen/qwen3-4b-thinking-2507"
MODELO_LLM = "google/gemma-3-4b"

# Configuración del juego
CREDITOS_INICIALES = 50
TURNOS_MAXIMOS_INTERROGATORIO = 3
DIAS_TOTALES = 3
TURNOS_POR_DIA = 2

# El juego original ocurre a finales de 1982. 
FECHA_ACTUAL = "1982-11-23"