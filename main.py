import asyncio
from scrapers.extract import correr_motor
from scrapers.transform import ejecutar_transformacion
from loaders.loader import cargar_datos, setup_database

async def run_pipeline():
    print("INICIO BeneficiosSUBE")

    # EXTRACT
    print("Extracción")
    try:
        await correr_motor() 
    except Exception as e:
        print(f"Error en Extracción: {e}")
        return

    print("\n" + "-"*40 + "\n")

    # TRANSFORM 
    print("Transformación y Limpieza")
    try:
        ejecutar_transformacion()
    except Exception as e:
        print(f"Error en Transformación: {e}")
        return

    # LOAD
    print("Carga de Datos")
    try:
        setup_database()
        cargar_datos()
    except Exception as e:
        print(f"Error en Carga de Datos: {e}")
        return

    print("Guardados en 'data/beneficios_clean.json'")

if __name__ == "__main__":
    asyncio.run(run_pipeline())