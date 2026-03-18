class Ministerio:
    """
    Gestiona las reglas dinámicas de Arstotzka según el día actual.
    """
    @staticmethod
    def obtener_reglas(dia: int) -> str:
        reglas = [
            "1. Todos los solicitantes deben tener un pasaporte válido (no caducado).",
        ]
        
        if dia >= 2:
            reglas.append("2. Los ciudadanos extranjeros (no de Arstotzka) deben presentar un 'Permiso de Ingreso' obligatorio.")
            
        if dia >= 3:
            reglas.append("3. ALERTA TERRORISTA: Se prohíbe la entrada a todos los ciudadanos de Kolechia sin excepciones.")
            
        return "\n".join(reglas)