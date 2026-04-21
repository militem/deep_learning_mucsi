# ministerio_rag.py
import chromadb
from chromadb.utils import embedding_functions

class MinisterioRAG:
    """
    Gestiona el Manual de Reglas de Arstotzka utilizando una Base de Datos Vectorial (ChromaDB)
    para realizar Retrieval-Augmented Generation (RAG).
    """
    def __init__(self):
        # Iniciamos ChromaDB en memoria (se borra al cerrar el juego)
        self.chroma_client = chromadb.Client()
        
        # Usamos un modelo de embeddings local, pequeño y muy rápido (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Creamos la colección (nuestro "Manual")
        self.coleccion_reglas = self.chroma_client.create_collection(
            name="manual_arstotzka",
            embedding_function=self.embedding_fn
        )
        
        # Llevamos un registro de qué reglas ya están en la DB para no duplicar
        self.reglas_ingresadas = []

    def actualizar_reglas_del_dia(self, dia: int):
        """Añade nuevas normativas a la base de datos según el día."""
        nuevas_reglas = []
        
        if dia == 1:
            nuevas_reglas.append("REGLA BÁSICA: Todos los solicitantes, sin excepción, deben presentar un pasaporte válido.")
            nuevas_reglas.append("REGLA DE CADUCIDAD: Ningún documento es válido si su fecha de caducidad es anterior a la fecha actual (1982-11-23).")
            
        elif dia == 2:
            nuevas_reglas.append("REGLA PARA EXTRANJEROS: Los ciudadanos extranjeros (nacionalidad distinta a Arstotzka) deben presentar un 'Permiso de Ingreso' obligatorio.")
            
        elif dia == 3:
            nuevas_reglas.append("ALERTA DE SEGURIDAD: Se prohíbe terminantemente la entrada a todos los ciudadanos provenientes de Kolechia. Deben ser denegados inmediatamente.")
            
        elif dia == 4:
            nuevas_reglas.append("REGLA DE TRABAJADORES: Cualquier persona que venga por motivos de 'Trabajo' debe presentar un 'Permiso de Trabajo' oficial.")

        # Inyectar las reglas en la base de datos vectorial
        for i, regla in enumerate(nuevas_reglas):
            # Creamos un ID único combinando el día y el índice
            id_regla = f"dia_{dia}_regla_{i}"
            if id_regla not in self.reglas_ingresadas:
                self.coleccion_reglas.add(
                    documents=[regla],
                    ids=[id_regla],
                    metadatas=[{"dia": dia}] # Guardamos el día como metadato
                )
                self.reglas_ingresadas.append(id_regla)

    def consultar_reglas_pertinentes(self, perfil_ciudadano_json: str, n_resultados: int = 3) -> str:
        """
        Busca en el manual las reglas que más se ajusten al perfil del ciudadano actual.
        """
        # Hacemos la consulta semántica
        resultados = self.coleccion_reglas.query(
            query_texts=[perfil_ciudadano_json],
            n_results=n_resultados
        )
        
        # Extraemos los documentos de texto encontrados
        documentos_encontrados = resultados['documents'][0]
        
        # Los formateamos como un string con viñetas para el LLM
        reglas_formateadas = "\n".join([f"- {doc}" for doc in documentos_encontrados])
        
        # --- MODO DEBUG: Mostrar qué percibe el RAG ---
        # print(f"\n🔍 [DEBUG RAG] Query enviada a la BD: '{perfil_ciudadano_json}'")
        # print(f"🧠 [DEBUG RAG] Recuerdos inyectados al Inspector:")
        print(reglas_formateadas)
        print("-" * 50)
        # ----------------------------------------------

        return reglas_formateadas