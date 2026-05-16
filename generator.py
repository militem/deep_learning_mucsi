import random

def generar_solicitante_aleatorio(dia: int) -> dict:
    """
    Genera un perfil aleatorio para un ciudadano según las reglas del día.
    """
    nombres = ["Jorji Costava", "Mila Pavlova", "Igor Vostok", "Sergiu", "Elisa"]
    paises = ["Arstotzka"] #"Kolechia", "Impor", "Antegria", "Republia"
    personalidades = ["Nervioso", "Agresivo", "Amable", "Apresurado", "Suplicante"]
    
    nombre = random.choice(nombres)
    pais = random.choice(paises)
    es_valido = random.choice([True, False])
    motivo_invalido = ""
    
    # Decidir tipo de error si es inválido
    tipos_error = ["caducado", "sexo_erroneo"]
    tipo_error = random.choice(tipos_error) if not es_valido else "ninguno"
    
    # Generar pasaporte base
    fecha_caducidad = "1981-05-14" if tipo_error == "caducado" else "1988-12-01"
    sexo_real = random.choice(["M", "F"])
    sexo_doc = "X" if tipo_error == "sexo_erroneo" else sexo_real
    
    id_pasaporte = f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    documentos = {
        "pasaporte": {
            "id_pasaporte": id_pasaporte,
            "nombre": nombre,
            "nacionalidad": pais,
            "fecha_caducidad": fecha_caducidad,
            "sexo": sexo_doc
        }
    }
    
    if tipo_error == "caducado":
        motivo_invalido = "El pasaporte está caducado."
    elif tipo_error == "sexo_erroneo":
        motivo_invalido = "El sexo en el pasaporte no coincide con mi apariencia."
        
    # Regla: Prohibición a Kolechia (a partir del Día 3)
    if pais == "Kolechia" and dia >= 3:
        es_valido = False
        motivo_invalido = "Los ciudadanos de Kolechia tienen prohibida la entrada."

    motivo_oculto = "Todo en regla." if es_valido else motivo_invalido

    return {
        "es_valido": es_valido,
        "personalidad": random.choice(personalidades),
        "documentos": documentos,
        "motivo_oculto": motivo_oculto
    }