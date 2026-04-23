"""
Carga las reglas de Papers Please en Neo4j a partir del JSON original.
Requiere: pip install neo4j
Neo4j debe estar corriendo (docker compose up -d)
"""

import json
import time
import sys
from pathlib import Path
from neo4j import GraphDatabase

URI      = "bolt://localhost:7687"
USER     = "neo4j"
PASSWORD = "papersplease"
JSON_FILE = Path(__file__).parent / "Reglas_papersPlease.json"


def esperar_neo4j(driver, intentos=20, espera=3):
    for i in range(intentos):
        try:
            driver.verify_connectivity()
            print("Neo4j disponible.")
            return
        except Exception:
            print(f"Esperando Neo4j... ({i+1}/{intentos})")
            time.sleep(espera)
    print("No se pudo conectar a Neo4j. ¿Está el contenedor corriendo?")
    sys.exit(1)


def limpiar_base(session):
    session.run("MATCH (n) DETACH DELETE n")
    print("Base de datos limpiada.")


def crear_restricciones(session):
    constraints = [
        "CREATE CONSTRAINT regla_id IF NOT EXISTS FOR (r:Regla)     REQUIRE r.id     IS UNIQUE",
        "CREATE CONSTRAINT cat_nombre IF NOT EXISTS FOR (c:Categoria) REQUIRE c.nombre IS UNIQUE",
        "CREATE CONSTRAINT pais_nombre IF NOT EXISTS FOR (p:Pais)    REQUIRE p.nombre IS UNIQUE",
        "CREATE CONSTRAINT doc_nombre IF NOT EXISTS FOR (d:Documento) REQUIRE d.nombre IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("Restricciones de unicidad creadas.")


def crear_nodos_base(session):
    """Crea nodos Categoria, Pais y Documento a partir del JSON (sin duplicados)."""
    with open(JSON_FILE, encoding="utf-8") as f:
        reglas = json.load(f)

    categorias = set(r["categoria"]           for r in reglas)
    paises     = set(r["pais_afectado"]       for r in reglas)
    documentos = set(r["documento_requerido"] for r in reglas)

    for cat in categorias:
        session.run("MERGE (:Categoria {nombre: $n})", n=cat)
    for pais in paises:
        session.run("MERGE (:Pais {nombre: $n})", n=pais)
    for doc in documentos:
        session.run("MERGE (:Documento {nombre: $n})", n=doc)

    print(f"Nodos creados — Categorias: {len(categorias)}, Paises: {len(paises)}, Documentos: {len(documentos)}")
    return reglas


def crear_reglas(session, reglas):
    for regla in reglas:
        session.run(
            """
            MERGE (r:Regla {id: $id})
              SET r.dia_inicio  = $di,
                  r.dia_fin     = $df,
                  r.descripcion = $desc
            WITH r
            MATCH (c:Categoria {nombre: $cat}),
                  (p:Pais      {nombre: $pais}),
                  (d:Documento {nombre: $doc})
            MERGE (r)-[:PERTENECE_A]->(c)
            MERGE (r)-[:AFECTA_A]   ->(p)
            MERGE (r)-[:REQUIERE]   ->(d)
            """,
            id=regla["id"],
            di=regla["dia_inicio"],
            df=regla["dia_fin"],
            desc=regla["descripcion"],
            cat=regla["categoria"],
            pais=regla["pais_afectado"],
            doc=regla["documento_requerido"],
        )
    print(f"{len(reglas)} reglas cargadas con sus relaciones.")


def crear_relaciones_documentos(session):
    """Modela las sustituciones históricas de documentos."""
    sustituciones = [
        ("permiso_entrada",  "ticket_entrada",      4),
        ("permiso_acceso",   "permiso_entrada",     26),
        ("permiso_acceso",   "suplemento_identidad", 26),
    ]
    for nuevo, viejo, dia in sustituciones:
        session.run(
            """
            MATCH (n:Documento {nombre: $nuevo}), (v:Documento {nombre: $viejo})
            MERGE (n)-[:REEMPLAZA_A {desde_dia: $dia}]->(v)
            """,
            nuevo=nuevo, viejo=viejo, dia=dia,
        )
    print(f"{len(sustituciones)} relaciones de sustitución de documentos creadas.")


def mostrar_resumen(session):
    counts = {
        "Reglas":     session.run("MATCH (n:Regla)     RETURN count(n) AS c").single()["c"],
        "Categorias": session.run("MATCH (n:Categoria) RETURN count(n) AS c").single()["c"],
        "Paises":     session.run("MATCH (n:Pais)      RETURN count(n) AS c").single()["c"],
        "Documentos": session.run("MATCH (n:Documento) RETURN count(n) AS c").single()["c"],
        "Relaciones": session.run("MATCH ()-[r]->()    RETURN count(r) AS c").single()["c"],
    }
    print("\n=== Resumen del grafo ===")
    for label, count in counts.items():
        print(f"  {label:<12}: {count}")
    print("\nNeo4j Browser: http://localhost:7474  (usuario: neo4j / contraseña: papersplease)")
    print("Consulta inicial: MATCH (n) RETURN n LIMIT 50")


def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    esperar_neo4j(driver)

    with driver.session() as session:
        limpiar_base(session)
        crear_restricciones(session)
        reglas = crear_nodos_base(session)
        crear_reglas(session, reglas)
        crear_relaciones_documentos(session)
        mostrar_resumen(session)

    driver.close()


if __name__ == "__main__":
    main()
