import sqlite3
import os

DB_PATH = 'data/beneficios.db'
LOG_PATH = 'logs/scraper.log'

def analizar_db():
    print("\n ESTADÍSTICAS DE BASE DE DATOS")
    if not os.path.exists(DB_PATH):
        print("BBDD no encontrada.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total de Beneficios
        cursor.execute("SELECT COUNT(*) FROM Beneficio")
        total_result = cursor.fetchone()
        total = total_result[0] if total_result else 0
        print(f"Beneficios Activos: {total}")

        # Desglose por Banco
        print("\nDesglose por Banco:")
        cursor.execute('''
            SELECT e.nombre_entidad, COUNT(b.id_beneficio) 
            FROM Beneficio b
            JOIN Entidad_Emisora e ON b.id_entidad = e.id_entidad
            GROUP BY e.nombre_entidad
            ORDER BY COUNT(b.id_beneficio) DESC
        ''')
        
        filas = cursor.fetchall()
        if filas:
            for banco, cantidad in filas:
                print(f"   - {banco}: {cantidad} promos")
        else:
            print("   (No hay datos desglosados)")

        conn.close()
    except Exception as e:
        print(f"Error leyendo DB: {e}")

def analizar_logs():
    print("\n LOGS")
    if not os.path.exists(LOG_PATH):
        print("Logs no encontrados.")
        return

    errores = 0
    advertencias = 0
    
    try:
        with open(LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lineas = f.readlines()
            ultimas_lineas = lineas[-50:] if len(lineas) > 50 else lineas
            
            for linea in ultimas_lineas:
                if "TargetClosedError" in linea:
                    continue

                if "ERROR" in linea.upper() or "FALLO" in linea.upper():
                    errores += 1
                    print(f"   {linea.strip()}") 
                elif "WARNING" in linea.upper() or "AVISO" in linea.upper():
                    advertencias += 1

        print(f"\nResumen de Salud:")
        if errores == 0:
            print("   SISTEMA SALUDABLE: 0 Errores recientes.")
        else:
            print(f"   ATENCIÓN: Se detectaron {errores} errores recientes.")
            
    except Exception as e:
        print(f"Error crítico leyendo logs: {e}")

if __name__ == "__main__":
    print("INICIANDO MONITOR DE SALUD | BeneficiosSUBE")
    analizar_db()
    analizar_logs()