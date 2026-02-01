import sqlite3
import json
import os

DB_PATH = 'data/beneficios.db'
JSON_PATH = 'data/beneficios_clean.json'
CONFIG_PATH = 'utils/config.json'

def conectar_db():
    return sqlite3.connect(DB_PATH)

def setup_database():
    """Esquema relacional de la db"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Entidad_Emisora
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Entidad_Emisora (
        id_entidad INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_entidad TEXT UNIQUE,
        logo_url TEXT,
        color_hex TEXT
    )''')
    
    # Agrega columnas logo_url y color_hex si no existen por versiones anteriores
    try:
        cursor.execute("ALTER TABLE Entidad_Emisora ADD COLUMN logo_url TEXT")
        cursor.execute("ALTER TABLE Entidad_Emisora ADD COLUMN color_hex TEXT")
    except: pass
    
    cursor.execute('CREATE TABLE IF NOT EXISTS Alcance_Geografico (id_alcance INTEGER PRIMARY KEY AUTOINCREMENT, provincia_region TEXT, aplica_subte BOOLEAN, UNIQUE(provincia_region, aplica_subte))')
    cursor.execute('CREATE TABLE IF NOT EXISTS Vigencia_Temporal (id_vigencia INTEGER PRIMARY KEY AUTOINCREMENT, fecha_inicio DATE, fecha_fin DATE, dias_semana TEXT, frecuencia TEXT, UNIQUE(fecha_inicio, fecha_fin, dias_semana, frecuencia))')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Beneficio (id_beneficio INTEGER PRIMARY KEY AUTOINCREMENT, id_entidad INTEGER, id_alcance INTEGER, id_vigencia INTEGER, porcentaje_descuento REAL, tope_reintegro REAL, monto_minimo_consumo REAL, requiere_nfc BOOLEAN, url_detalle_promo TEXT, terminos_condiciones TEXT, fecha_ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(id_entidad) REFERENCES Entidad_Emisora(id_entidad), FOREIGN KEY(id_alcance) REFERENCES Alcance_Geografico(id_alcance), FOREIGN KEY(id_vigencia) REFERENCES Vigencia_Temporal(id_vigencia))''')
    conn.commit()
    conn.close()

def gestionar_entidad(cursor, nombre, logo, color):
    cursor.execute("SELECT id_entidad FROM Entidad_Emisora WHERE nombre_entidad = ?", (nombre,))
    res = cursor.fetchone()
    if res:
        cursor.execute("UPDATE Entidad_Emisora SET logo_url = ?, color_hex = ? WHERE id_entidad = ?", (logo, color, res[0]))
        return res[0]
    cursor.execute("INSERT INTO Entidad_Emisora (nombre_entidad, logo_url, color_hex) VALUES (?, ?, ?)", (nombre, logo, color))
    return cursor.lastrowid

def obtener_id_generico(cursor, tabla, campos, valores):
    where = " AND ".join([f"{k}=?" for k in campos])
    cursor.execute(f"SELECT id_{tabla.lower().split('_')[0]} FROM {tabla} WHERE {where}", valores)
    res = cursor.fetchone()
    if res: return res[0]
    cols, placeholders = ", ".join(campos), ", ".join(["?"] * len(valores))
    cursor.execute(f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})", valores)
    return cursor.lastrowid

def cargar_datos():
    if not os.path.exists(JSON_PATH): return
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        branding = {b['nombre']: b for b in json.load(f)['bancos']}
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    conn = conectar_db(); cursor = conn.cursor(); count = 0
    for item in datos:
        b = branding.get(item['banco'], {})
        id_ent = gestionar_entidad(cursor, item['banco'], b.get('logo_url'), b.get('color_hex'))
        id_alc = obtener_id_generico(cursor, "Alcance_Geografico", ["provincia_region", "aplica_subte"], [item.get('provincia_region', 'Mendoza'), item['aplica_subte']])
        id_vig = obtener_id_generico(cursor, "Vigencia_Temporal", ["fecha_inicio", "fecha_fin", "dias_semana", "frecuencia"], [item['fecha_inicio'], item['fecha_fin'], item['dias_semana'], item['frecuencia']])
        
        cursor.execute("SELECT id_beneficio FROM Beneficio WHERE id_entidad=? AND id_vigencia=? AND url_detalle_promo=?", (id_ent, id_vig, item['url_detalle_promo']))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Beneficio (id_entidad, id_alcance, id_vigencia, porcentaje_descuento, tope_reintegro, monto_minimo_consumo, requiere_nfc, url_detalle_promo, terminos_condiciones) VALUES (?,?,?,?,?,?,?,?,?)",
                (id_ent, id_alc, id_vig, item['porcentaje_descuento'], item['tope_reintegro'], item['monto_minimo_consumo'], item['requiere_nfc'], item['url_detalle_promo'], item['terminos_condiciones']))
            count += 1
    conn.commit(); conn.close(); print(f"Carga completa: {count} nuevos.")

if __name__ == "__main__":
    setup_database(); cargar_datos()