from openai import OpenAI
import config
from engine import MotorPapersPlease

def main():
    print("=== INICIANDO SIMULACIÓN DE ARSTOTZKA (OLLAMA EDITION) ===")
    
    # Configuramos el cliente para que use el servidor local de Ollama
    try:
        cliente_local = OpenAI(
            base_url=config.OLLAMA_BASE_URL,
            api_key=config.OLLAMA_API_KEY
        )
        
        motor = MotorPapersPlease(cliente_local, modelo=config.MODELO_LLM)
        
        # Bucle principal de Días
        for dia in range(1, config.DIAS_TOTALES + 1):
            motor.iniciar_dia(dia)
            
            # Bucle de Solicitantes (turnos) por día
            for turno in range(config.TURNOS_POR_DIA):
                motor.jugar_turno()
                
                # Si se arruina en mitad del día, salimos del bucle de turnos
                if motor.saldo_creditos < 0:
                    break
                    
            # Si se arruinó, también salimos del bucle de días
            if motor.saldo_creditos < 0:
                print("\n🚨 [Ministerio]: Te has quedado sin créditos. Estás arrestado. FIN DEL JUEGO.")
                break
                
        print("\n=== FIN DEL TURNO DE TRABAJO ===")
        print(f"Saldo final: {motor.saldo_creditos} créditos.")

    except Exception as e:
        print(f"\n[Error fatal]: {e}")
        print("¿Está Ollama ejecutándose en segundo plano?")

if __name__ == "__main__":
    main()