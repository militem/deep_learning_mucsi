from neo4j import GraphDatabase
import config

class MinisterioNeo4j:
    """
    Gestiona las reglas dinámicas de Arstotzka consultando la base de datos de grafos (Neo4j).
    Sustituye la lógica estática y RAG.
    """
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="papersplease"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def cerrar(self):
        self.driver.close()

    def obtener_reglas_del_dia(self, dia: int) -> str:
        """
        Consulta en Neo4j las reglas vigentes para un día específico
        y devuelve un string formateado para el contexto del LLM.
        """
        query = """
        MATCH (r:Regla)-[:AFECTA_A]->(p:Pais),
              (r)-[:REQUIERE]->(d:Documento)
        WHERE r.dia_inicio <= $dia AND r.dia_fin >= $dia
        RETURN r.id AS id, r.descripcion AS descripcion, p.nombre AS pais, d.nombre AS documento
        ORDER BY r.id
        """
        
        reglas = []
        try:
            with self.driver.session() as session:
                resultados = session.run(query, dia=dia)
                for record in resultados:
                    # Formateamos cada regla devuelta por el grafo
                    texto_regla = f"- [{record['id']}] (Aplica a: {record['pais']} | Doc: {record['documento']}): {record['descripcion']}"
                    reglas.append(texto_regla)
        except Exception as e:
            print(f" Error al conectar con Neo4j: {e}")
            return "1. Error: No se pudieron cargar las reglas del ministerio (Neo4j inactivo)."

        if not reglas:
             return "No hay reglas vigentes para el día de hoy."

        return "\n".join(reglas)

# Instancia global para facilitar la importación y evitar abrir múltiples drivers
ministerio_db = MinisterioNeo4j()
