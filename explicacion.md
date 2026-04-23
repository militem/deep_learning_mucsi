# Papers Please — Conversión a Base de Datos de Grafos con Neo4j

## 1. ¿Qué es una base de datos de grafos?

Una base de datos de grafos almacena la información como **nodos** (entidades) y **relaciones** (aristas dirigidas entre nodos). A diferencia de las bases de datos relacionales, las relaciones son ciudadanas de primera clase: no se infieren mediante JOINs, sino que existen como objetos propios con sus propias propiedades.

Neo4j es el motor de grafos más usado, con el lenguaje de consulta **Cypher** (sintaxis declarativa similar a SQL pero orientada a patrones de grafo).

---

## 2. Origen de los datos

El archivo `Reglas_papersPlease.json` contiene **17 reglas** del videojuego *Papers, Please*. Cada regla tiene:

| Campo               | Tipo    | Descripción                              |
|---------------------|---------|------------------------------------------|
| `id`                | string  | Identificador único de la regla          |
| `dia_inicio`        | número  | Día del juego en que entra en vigor      |
| `dia_fin`           | número  | Día del juego en que deja de aplicarse   |
| `descripcion`       | string  | Texto de la norma                        |
| `categoria`         | string  | Tipo de norma (seguridad, fraude, etc.)  |
| `pais_afectado`     | string  | País o grupo al que aplica               |
| `documento_requerido` | string | Documento que exige la norma            |

---

## 3. Modelo de grafo diseñado

Se identificaron **4 tipos de nodos** y **4 tipos de relaciones**:

### 3.1 Nodos

| Etiqueta     | Propiedades clave | Descripción                                        |
|--------------|-------------------|----------------------------------------------------|
| `Regla`      | `id`, `dia_inicio`, `dia_fin`, `descripcion` | Cada regla del juego       |
| `Categoria`  | `nombre`          | Tipo de norma (basico, frontera, seguridad…)       |
| `Pais`       | `nombre`          | País o grupo afectado (Arstotzka, Kolechia…)       |
| `Documento`  | `nombre`, `descripcion` | Documento exigido (pasaporte, permiso_acceso…) |

### 3.2 Relaciones

| Relación           | Dirección              | Significado                                    |
|--------------------|------------------------|------------------------------------------------|
| `PERTENECE_A`      | `Regla → Categoria`    | La regla pertenece a una categoría             |
| `AFECTA_A`         | `Regla → Pais`         | La regla aplica a ese país/grupo               |
| `REQUIERE`         | `Regla → Documento`    | La regla exige ese documento                   |
| `REEMPLAZA_A`      | `Documento → Documento`| Un documento sustituye a otro (evolución histórica) |

La relación `REEMPLAZA_A` modela la progresión temporal del juego:

```
ticket_entrada  <──REEMPLAZA_A── permiso_entrada  <──REEMPLAZA_A── permiso_acceso
                                  suplemento_identidad ──────────────────────────^
```

---

## 4. Estructura de archivos

```
Papers Please/
├── Reglas_papersPlease.json   ← Datos originales
├── docker-compose.yml         ← Levanta Neo4j en Docker
├── papers_please.cypher       ← Queries Cypher puras (importar en Browser)
├── cargar_datos.py            ← Script Python que carga el grafo automáticamente
└── explicacion.md             ← Este archivo
```

---

## 5. Tecnologías instaladas / utilizadas

| Componente         | Versión usada | Cómo se obtuvo                   |
|--------------------|---------------|----------------------------------|
| Docker Desktop     | 29.2.x        | Ya instalado en el sistema       |
| Neo4j              | 5.26          | Imagen Docker `neo4j:5.26`       |
| Python             | 3.12          | Ya instalado en el sistema       |
| Driver `neo4j`     | 6.1.0         | `pip install neo4j`              |

---

## 6. Cómo ejecutarlo

### Paso 1 — Arrancar Docker Desktop
Abre Docker Desktop desde el escritorio o el menú inicio y espera a que el icono de la ballena esté verde.

### Paso 2 — Levantar Neo4j
Desde la carpeta del proyecto:
```bash
docker compose up -d
```
Esto descarga la imagen de Neo4j (≈500 MB la primera vez) y arranca el contenedor `papers_please_neo4j`.

### Paso 3 — Cargar los datos
```bash
python cargar_datos.py
```
El script espera automáticamente a que Neo4j esté listo y después:
1. Borra datos previos
2. Crea restricciones de unicidad
3. Crea nodos `Categoria`, `Pais`, `Documento`
4. Crea nodos `Regla` con sus 3 relaciones
5. Añade las relaciones `REEMPLAZA_A` entre documentos
6. Imprime un resumen del grafo

### Paso 4 — Explorar en Neo4j Browser
Abre http://localhost:7474 en el navegador.
- **Usuario**: `neo4j`
- **Contraseña**: `papersplease`

---

## 7. Consultas Cypher de ejemplo

### Ver todo el grafo
```cypher
MATCH (n) RETURN n LIMIT 50
```

### Reglas vigentes en el día 10
```cypher
MATCH (r:Regla)-[:AFECTA_A]->(p:Pais),
      (r)-[:REQUIERE]->(d:Documento)
WHERE r.dia_inicio <= 10 AND r.dia_fin >= 10
RETURN r.id, r.descripcion, p.nombre AS pais, d.nombre AS documento
ORDER BY r.id
```

### Documentos exigidos a extranjeros (cronológico)
```cypher
MATCH (r:Regla)-[:AFECTA_A]->(p:Pais {nombre: "extranjeros"}),
      (r)-[:REQUIERE]->(d:Documento)
RETURN r.id, d.nombre AS documento, r.dia_inicio, r.dia_fin
ORDER BY r.dia_inicio
```

### Reglas de seguridad agrupadas por país
```cypher
MATCH (r:Regla)-[:PERTENECE_A]->(c:Categoria {nombre: "seguridad"}),
      (r)-[:AFECTA_A]->(p:Pais)
RETURN p.nombre AS pais, collect(r.id) AS reglas
```

### Cadena de sustitución de documentos
```cypher
MATCH cadena = (d:Documento)-[:REEMPLAZA_A*]->(anterior:Documento)
RETURN cadena
```

### ¿Qué documentos necesita alguien de Kolechia en el día 20?
```cypher
MATCH (r:Regla)-[:AFECTA_A]->(p:Pais),
      (r)-[:REQUIERE]->(d:Documento)
WHERE (p.nombre = "Kolechia" OR p.nombre = "extranjeros" OR p.nombre = "todos")
  AND r.dia_inicio <= 20 AND r.dia_fin >= 20
RETURN DISTINCT d.nombre AS documento, r.id, r.descripcion
ORDER BY d.nombre
```

---

## 8. ¿Por qué un grafo y no una tabla relacional?

| Pregunta                                   | SQL (JOIN)     | Grafo (Cypher)   |
|--------------------------------------------|----------------|------------------|
| ¿Qué documentos necesito hoy?             | 2-3 JOINs      | 1 MATCH           |
| ¿Qué documentos reemplazaron a X?         | Tabla puente   | `[:REEMPLAZA_A*]` |
| Países con más restricciones              | GROUP BY + COUNT | collect() nativo |
| Explorar relaciones sin conocer la profundidad | Recursivo / CTE | `*` en el patrón |

El modelo de grafo es especialmente natural aquí porque las reglas del juego forman una red de restricciones que evolucionan con el tiempo, exactamente lo que los grafos capturan mejor.
