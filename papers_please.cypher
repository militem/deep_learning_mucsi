// ============================================================
// Papers Please — Modelo de Grafo en Cypher (Neo4j)
// ============================================================
// Nodos: Regla, Categoria, Pais, Documento
// Relaciones:
//   (Regla)-[:PERTENECE_A]->(Categoria)
//   (Regla)-[:AFECTA_A]->(Pais)
//   (Regla)-[:REQUIERE]->(Documento)
//   (Documento)-[:REEMPLAZA_A]->(Documento)
// ============================================================

// --- Limpiar datos previos ---
MATCH (n) DETACH DELETE n;

// ============================================================
// NODOS: Categorías
// ============================================================
MERGE (:Categoria {nombre: "basico"});
MERGE (:Categoria {nombre: "frontera"});
MERGE (:Categoria {nombre: "documentacion"});
MERGE (:Categoria {nombre: "protocolo"});
MERGE (:Categoria {nombre: "laboral"});
MERGE (:Categoria {nombre: "diplomacia"});
MERGE (:Categoria {nombre: "seguridad"});
MERGE (:Categoria {nombre: "salud"});
MERGE (:Categoria {nombre: "fraude"});

// ============================================================
// NODOS: Países / grupos afectados
// ============================================================
MERGE (:Pais {nombre: "todos"});
MERGE (:Pais {nombre: "extranjeros"});
MERGE (:Pais {nombre: "Arstotzka"});
MERGE (:Pais {nombre: "Kolechia"});
MERGE (:Pais {nombre: "Antegria"});
MERGE (:Pais {nombre: "Cobrastan"});

// ============================================================
// NODOS: Documentos
// ============================================================
MERGE (:Documento {nombre: "pasaporte",                descripcion: "Pasaporte vigente con datos del solicitante"});
MERGE (:Documento {nombre: "ticket_entrada",           descripcion: "Ticket de Entrada (Entry Ticket), días 3"});
MERGE (:Documento {nombre: "permiso_entrada",          descripcion: "Permiso de Entrada (Entry Permit), días 4-25"});
MERGE (:Documento {nombre: "cedula_identidad",         descripcion: "Cédula de Identidad (ID Card) para ciudadanos de Arstotzka"});
MERGE (:Documento {nombre: "pase_trabajo",             descripcion: "Pase de Trabajo (Work Pass) para extranjeros que vienen a trabajar"});
MERGE (:Documento {nombre: "autorizacion_diplomatica", descripcion: "Autorización Diplomática que incluya a Arstotzka"});
MERGE (:Documento {nombre: "suplemento_identidad",    descripcion: "Suplemento de Identidad (ID Supplement) con huellas y descripción física"});
MERGE (:Documento {nombre: "escaneo_corporal",         descripcion: "Registro físico / escaneo corporal"});
MERGE (:Documento {nombre: "certificado_vacunacion",   descripcion: "Certificado de Vacunación contra la Polio"});
MERGE (:Documento {nombre: "permiso_acceso",           descripcion: "Permiso de Acceso (Access Permit), reemplaza permiso_entrada + suplemento_identidad"});
MERGE (:Documento {nombre: "todos",                    descripcion: "Cualquier documento presentado"});

// ============================================================
// RELACIONES entre documentos (sustituciones históricas)
// ============================================================
MATCH (nuevo:Documento {nombre: "permiso_entrada"}),  (viejo:Documento {nombre: "ticket_entrada"})
MERGE (nuevo)-[:REEMPLAZA_A {desde_dia: 4}]->(viejo);

MATCH (nuevo:Documento {nombre: "permiso_acceso"}),   (viejo:Documento {nombre: "permiso_entrada"})
MERGE (nuevo)-[:REEMPLAZA_A {desde_dia: 26}]->(viejo);

MATCH (nuevo:Documento {nombre: "permiso_acceso"}),   (viejo:Documento {nombre: "suplemento_identidad"})
MERGE (nuevo)-[:REEMPLAZA_A {desde_dia: 26}]->(viejo);

// ============================================================
// NODOS: Reglas + sus relaciones
// ============================================================

// R_GEN_01
MERGE (r:Regla {id: "R_GEN_01", dia_inicio: 1,  dia_fin: 31,
  descripcion: "Todos los solicitantes deben presentar un pasaporte vigente. Documentos caducados o falsificados implican denegacion."})
WITH r
MATCH (c:Categoria {nombre: "basico"}),    (p:Pais {nombre: "todos"}),       (d:Documento {nombre: "pasaporte"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_01
MERGE (r:Regla {id: "R_DIA_01", dia_inicio: 1,  dia_fin: 1,
  descripcion: "Solo se permite la entrada a ciudadanos de Arstotzka. Denegar a cualquier extranjero."})
WITH r
MATCH (c:Categoria {nombre: "frontera"}),  (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "pasaporte"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_02
MERGE (r:Regla {id: "R_DIA_02", dia_inicio: 2,  dia_fin: 31,
  descripcion: "Se permite el ingreso de extranjeros. Es obligatorio verificar la validez del pasaporte y la ciudad de emision."})
WITH r
MATCH (c:Categoria {nombre: "frontera"}),  (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "pasaporte"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_03
MERGE (r:Regla {id: "R_DIA_03", dia_inicio: 3,  dia_fin: 3,
  descripcion: "Extranjeros deben presentar un Ticket de Entrada (Entry Ticket)."})
WITH r
MATCH (c:Categoria {nombre: "documentacion"}), (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "ticket_entrada"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_04
MERGE (r:Regla {id: "R_DIA_04", dia_inicio: 4,  dia_fin: 25,
  descripcion: "El Ticket de Entrada es reemplazado por el Permiso de Entrada (Entry Permit). Debe incluir nombre, numero de pasaporte y sello de validez."})
WITH r
MATCH (c:Categoria {nombre: "documentacion"}), (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "permiso_entrada"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_04_ID
MERGE (r:Regla {id: "R_DIA_04_ID", dia_inicio: 4,  dia_fin: 31,
  descripcion: "Ciudadanos de Arstotzka deben presentar su Cedula de Identidad (ID Card)."})
WITH r
MATCH (c:Categoria {nombre: "documentacion"}), (p:Pais {nombre: "Arstotzka"}), (d:Documento {nombre: "cedula_identidad"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_05
MERGE (r:Regla {id: "R_DIA_05", dia_inicio: 5,  dia_fin: 31,
  descripcion: "Cualquier discrepancia en datos (nombre, fecha de nacimiento, sexo) requiere interrogatorio inmediato."})
WITH r
MATCH (c:Categoria {nombre: "protocolo"}), (p:Pais {nombre: "todos"}), (d:Documento {nombre: "todos"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_07
MERGE (r:Regla {id: "R_DIA_07", dia_inicio: 7,  dia_fin: 31,
  descripcion: "Si el proposito del viaje es TRABAJO, el extranjero debe presentar un Pase de Trabajo (Work Pass)."})
WITH r
MATCH (c:Categoria {nombre: "laboral"}),   (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "pase_trabajo"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_08
MERGE (r:Regla {id: "R_DIA_08", dia_inicio: 8,  dia_fin: 31,
  descripcion: "Diplomaticos requieren una Autorizacion Diplomatica que incluya a Arstotzka en la lista de paises de acceso."})
WITH r
MATCH (c:Categoria {nombre: "diplomacia"}), (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "autorizacion_diplomatica"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_13
MERGE (r:Regla {id: "R_DIA_13", dia_inicio: 13, dia_fin: 31,
  descripcion: "Extranjeros deben presentar un Suplemento de Identidad (ID Supplement) con huellas dactilares y descripcion fisica."})
WITH r
MATCH (c:Categoria {nombre: "documentacion"}), (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "suplemento_identidad"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_14
MERGE (r:Regla {id: "R_DIA_14", dia_inicio: 14, dia_fin: 31,
  descripcion: "Ciudadanos de Kolechia deben ser sometidos a registro fisico (escaneo corporal) preventivo."})
WITH r
MATCH (c:Categoria {nombre: "seguridad"}), (p:Pais {nombre: "Kolechia"}), (d:Documento {nombre: "escaneo_corporal"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_19
MERGE (r:Regla {id: "R_DIA_19", dia_inicio: 19, dia_fin: 31,
  descripcion: "Ante alerta de contrabando, cualquier solicitante con discrepancia de peso o apariencia debe ser escaneado."})
WITH r
MATCH (c:Categoria {nombre: "seguridad"}), (p:Pais {nombre: "todos"}), (d:Documento {nombre: "escaneo_corporal"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_21
MERGE (r:Regla {id: "R_DIA_21", dia_inicio: 21, dia_fin: 31,
  descripcion: "Emergencia sanitaria: Todos los solicitantes deben presentar un Certificado de Vacunacion vigente contra la Polio."})
WITH r
MATCH (c:Categoria {nombre: "salud"}), (p:Pais {nombre: "todos"}), (d:Documento {nombre: "certificado_vacunacion"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_24
MERGE (r:Regla {id: "R_DIA_24", dia_inicio: 24, dia_fin: 31,
  descripcion: "Nuevos pasaportes de Arstotzka ahora requieren sello del M.O.A. Los antiguos sin sello deben ser confiscados."})
WITH r
MATCH (c:Categoria {nombre: "fraude"}), (p:Pais {nombre: "Arstotzka"}), (d:Documento {nombre: "pasaporte"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_26
MERGE (r:Regla {id: "R_DIA_26", dia_inicio: 26, dia_fin: 31,
  descripcion: "El Permiso de Entrada y el Suplemento de Identidad son retirados. Se exige el nuevo Permiso de Acceso (Access Permit)."})
WITH r
MATCH (c:Categoria {nombre: "documentacion"}), (p:Pais {nombre: "extranjeros"}), (d:Documento {nombre: "permiso_acceso"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_DIA_27
MERGE (r:Regla {id: "R_DIA_27", dia_inicio: 27, dia_fin: 31,
  descripcion: "Se prohibe la entrada a cualquier ciudadano proveniente de la Republica de Antegria. Confiscar pasaportes."})
WITH r
MATCH (c:Categoria {nombre: "seguridad"}), (p:Pais {nombre: "Antegria"}), (d:Documento {nombre: "pasaporte"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// R_COBRASTAN
MERGE (r:Regla {id: "R_COBRASTAN", dia_inicio: 1, dia_fin: 31,
  descripcion: "Los documentos de Cobrastan son siempre invalidos. Pais no reconocido."})
WITH r
MATCH (c:Categoria {nombre: "fraude"}), (p:Pais {nombre: "Cobrastan"}), (d:Documento {nombre: "todos"})
MERGE (r)-[:PERTENECE_A]->(c)
MERGE (r)-[:AFECTA_A]->(p)
MERGE (r)-[:REQUIERE]->(d);

// ============================================================
// CONSULTAS DE EJEMPLO
// ============================================================

// Ver reglas vigentes en un día concreto (p.ej. día 10):
// MATCH (r:Regla)-[:AFECTA_A]->(p:Pais), (r)-[:REQUIERE]->(d:Documento)
// WHERE r.dia_inicio <= 10 AND r.dia_fin >= 10
// RETURN r.id, r.descripcion, p.nombre AS pais, d.nombre AS documento
// ORDER BY r.id;

// Ver todos los documentos que afectan a extranjeros:
// MATCH (r:Regla)-[:AFECTA_A]->(p:Pais {nombre: "extranjeros"}),
//       (r)-[:REQUIERE]->(d:Documento)
// RETURN r.id, d.nombre AS documento, r.dia_inicio, r.dia_fin
// ORDER BY r.dia_inicio;

// Ver cadena de sustitución de documentos:
// MATCH cadena = (d:Documento)-[:REEMPLAZA_A*]->(anterior:Documento)
// RETURN cadena;
