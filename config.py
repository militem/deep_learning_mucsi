"""
Configuración global del proyecto.
Ajustado para funcionar con Ollama localmente.
"""

# Configuración de Ollama (Usa el puerto por defecto de Ollama)
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_API_KEY = "ollama"  # La API key no importa en local, pero la librería la requiere

# Modelo a utilizar 
MODELO_LLM = "llama3"

# Configuración del juego
CREDITOS_INICIALES = 50
TURNOS_MAXIMOS_INTERROGATORIO = 3
DIAS_TOTALES = 3
TURNOS_POR_DIA = 2