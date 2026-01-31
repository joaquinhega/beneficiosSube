import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.parser import BeneficioSubeParser

def ejecutar_transformacion():
    """Lógica de Transform y Load """
    ruta_input = 'data/raw_extraction.json'
    ruta_output = 'data/beneficios_clean.json'

    if not os.path.exists(ruta_input):
        print(f"Error: No se encuentra {ruta_input}.")
        return

    with open(ruta_input, 'r', encoding='utf-8') as f:
        datos_crudos = json.load(f)

    parser = BeneficioSubeParser()
    beneficios_limpios = []

    print(f"Procesando {len(datos_crudos)}")

    for item in datos_crudos:
        url_origen = item.get('url_detalle', '')
        procesado = parser.procesar_texto(item['raw_data'], url_origen=url_origen)
        
        if procesado:
            procesado['banco'] = item.get('banco', 'Desconocido')
            beneficios_limpios.append(procesado)

    # Load
    os.makedirs('data', exist_ok=True)
    with open(ruta_output, 'w', encoding='utf-8') as f:
        json.dump(beneficios_limpios, f, indent=4, ensure_ascii=False)

    print(f"\nTRANSFORM EXITOSO")
    print(f"Beneficios limpios guardados: {len(beneficios_limpios)}")
    print(f"Archivo: {ruta_output}")

if __name__ == "__main__":
    ejecutar_transformacion()