import random

def generar_solicitante_aleatorio(dia: int) -> dict:
    """
    Genera un perfil aleatorio para un ciudadano según las reglas del día.
    """
    nombres = ["Jorji Costava", "Mila Pavlova", "Igor Vostok", "Sergiu", "Elisa"]
    paises = ["Arstotzka", "Kolechia", "Impor", "Antegria", "Republia"]
    personalidades = ["Nervioso", "Agresivo", "Amable", "Apresurado", "Suplicante"]
    
    nombre = random.choice(nombres)
    pais = random.choice(paises)
    es_valido = random.choice([True, False])
    motivo_invalido = ""
    
    # Generar pasaporte base
    fecha_caducidad = "1983-12-01" if es_valido else "1981-05-14"
    documentos = {
        "pasaporte": {
            "nombre": nombre,
            "nacionalidad": pais,
            "fecha_caducidad": fecha_caducidad,
            "sexo": random.choice(["M", "F"])
        }
    }
    
    if not es_valido:
        motivo_invalido = "El pasaporte está caducado."
        
    # Reglas del Día 2 (Permiso de ingreso para extranjeros)
    if dia >= 2 and pais != "Arstotzka":
        if es_valido:
            documentos["permiso_ingreso"] = {"nombre": nombre, "proposito": "Turismo/Trabajo"}
        else:
            # Si no es válido, podemos hacer que le falte el permiso o que el pasaporte esté caducado
            if random.choice([True, False]):
                motivo_invalido = "No tengo el permiso de ingreso obligatorio para extranjeros. Se me olvidó."
            elif not motivo_invalido:
                 motivo_invalido = "El pasaporte está caducado."
                 documentos["pasaporte"]["fecha_caducidad"] = "1981-05-14"
                 documentos["permiso_ingreso"] = {"nombre": nombre, "proposito": "Turismo/Trabajo"}
                 
    # Reglas del Día 3 (Prohibición a Kolechia)
    if dia >= 3 and pais == "Kolechia":
        es_valido = False
        motivo_invalido = "Soy de Kolechia y está prohibido, pero intenta suplicar que te dejen pasar por la guerra."

    motivo_oculto = "Todo en regla." if es_valido else motivo_invalido

    return {
        "es_valido": es_valido,
        "personalidad": random.choice(personalidades),
        "documentos": documentos,
        "motivo_oculto": motivo_oculto
    }