import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'data/beneficios.db'
JSON_PATH = 'data/beneficios_clean.json'

def conectar_db():
    return sqlite3.connect(DB_PATH)

def setup_database():
    """ Crea el esquema Relacional basado en el DER """
    conn = conectar_db()
    cursor = conn.cursor()

    # Entidad_Emisora
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Entidad_Emisora (
        id_entidad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_entidad TEXT UNIQUE,
        url_promociones_principal TEXT
    )''')

    # Alcance_Geografico
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Alcance_Geografico (
        id_alcance INTEGER PRIMARY KEY AUTOINCREMENT,
        provincia_region TEXT,
        aplica_subte BOOLEAN,
        UNIQUE(provincia_region, aplica_subte)
    )''')

    # Vigencia_Temporal
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Vigencia_Temporal (
        id_vigencia INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_inicio DATE,
        fecha_fin DATE,
        dias_semana TEXT,
        frecuencia TEXT,
        UNIQUE(fecha_inicio, fecha_fin, dias_semana, frecuencia)
    )''')

    # Beneficio (La central que une todo)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Beneficio (
        id_beneficio INTEGER PRIMARY KEY AUTOINCREMENT,
        id_entidad INTEGER,
        id_alcance INTEGER,
        id_vigencia INTEGER,
        porcentaje_descuento REAL,
        tope_reintegro REAL,
        monto_minimo_consumo REAL,
        requiere_nfc BOOLEAN,
        url_detalle_promo TEXT,
        terminos_condiciones TEXT,
        fecha_ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(id_entidad) REFERENCES Entidad_Emisora(id_entidad),
        FOREIGN KEY(id_alcance) REFERENCES Alcance_Geografico(id_alcance),
        FOREIGN KEY(id_vigencia) REFERENCES Vigencia_Temporal(id_vigencia)
    )''')

    conn.commit()
    conn.close()
    print("Base de datos y tablas verificadas.")

def obtener_o_crear_id(cursor, tabla, campos_buscar, valores):
    """ 
    Función helper para manejar Tablas Dimensionales.
    Busca si el registro existe. Si sí, devuelve su ID.
    Si no, lo inserta y devuelve el nuevo ID.
    """
    where_clause = " AND ".join([f"{k}=?" for k in campos_buscar])
    query_select = f"SELECT id_{tabla.lower().split('_')[0]} FROM {tabla} WHERE {where_clause}"
    
    cursor.execute(query_select, valores)
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0]
    else:
        cols = ", ".join(campos_buscar)
        placeholders = ", ".join(["?"] * len(valores))
        query_insert = f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})"
        cursor.execute(query_insert, valores)
        return cursor.lastrowid

def cargar_datos():
    if not os.path.exists(JSON_PATH):
        print(f"No se encontró {JSON_PATH}. Ejecuta el scraper primero.")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    contador_nuevos = 0
    
    print(f"Procesando {len(datos)} beneficios para insertar en SQL...")

    for item in datos:
        try:
            # Gestionar Entidad
            id_entidad = obtener_o_crear_id(
                cursor, "Entidad_Emisora", 
                ["nombre_entidad"], 
                [item['banco']]
            )

            # Gestionar Alcance
            id_alcance = obtener_o_crear_id(
                cursor, "Alcance_Geografico",
                ["provincia_region", "aplica_subte"],
                [item.get('provincia_region', 'Mendoza'), item['aplica_subte']]
            )

            # Gestionar Vigencia
            id_vigencia = obtener_o_crear_id(
                cursor, "Vigencia_Temporal",
                ["fecha_inicio", "fecha_fin", "dias_semana", "frecuencia"],
                [item['fecha_inicio'], item['fecha_fin'], item['dias_semana'], item['frecuencia']]
            )

            # Insertar Beneficio (de Hechos)
            cursor.execute('''
                SELECT id_beneficio FROM Beneficio 
                WHERE id_entidad=? AND id_vigencia=? AND url_detalle_promo=?
            ''', (id_entidad, id_vigencia, item['url_detalle_promo']))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO Beneficio (
                        id_entidad, id_alcance, id_vigencia,
                        porcentaje_descuento, tope_reintegro, monto_minimo_consumo,
                        requiere_nfc, url_detalle_promo, terminos_condiciones
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    id_entidad, id_alcance, id_vigencia,
                    item['porcentaje_descuento'], item['tope_reintegro'], item['monto_minimo_consumo'],
                    item['requiere_nfc'], item['url_detalle_promo'], item['terminos_condiciones']
                ))
                contador_nuevos += 1

        except Exception as e:
            print(f"Error cargando beneficio de {item.get('banco')}: {e}")

    conn.commit()
    conn.close()
    print(f"Carga completa. Se insertaron {contador_nuevos} beneficios nuevos.")
if __name__ == "__main__":
    setup_database()
    cargar_datos()