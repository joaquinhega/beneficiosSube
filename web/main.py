import os
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Beneficios SUBE API")

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "beneficios.db")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza la main page de la app."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/beneficios")
async def api_beneficios():
    """Retorna lista de beneficios """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT e.nombre_entidad as banco, e.logo_url, e.color_hex, b.porcentaje_descuento, 
           b.tope_reintegro, vt.dias_semana, b.url_detalle_promo, b.terminos_condiciones, 
           ag.aplica_subte, b.requiere_nfc
    FROM Beneficio b
    JOIN Entidad_Emisora e ON b.id_entidad = e.id_entidad
    JOIN Vigencia_Temporal vt ON b.id_vigencia = vt.id_vigencia
    JOIN Alcance_Geografico ag ON b.id_alcance = ag.id_alcance
    """
    
    cursor.execute(query)
    filas = cursor.fetchall()
    conn.close()
    
    resultados = []
    for f in filas:
        d = dict(f)
        
        # Normalización de dias
        orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dias_set = {x.strip().capitalize() for x in d['dias_semana'].split(',')}
        d['dias_semana'] = ", ".join(sorted(list(dias_set), 
                                     key=lambda x: orden_dias.index(x) if x in orden_dias else 9))
        
        # Tipos de transporte
        transporte = ["Colectivo"]
        if d['aplica_subte']: transporte.append("Subte")
        d['tipo_transporte'] = ", ".join(transporte)
        
        # Métodos de pago
        legal = d['terminos_condiciones'].upper()
        metodos = []
        if "QR" in legal: metodos.append("📱 QR")
        if any(w in legal for w in ["DEBITO", "DÉBITO"]): metodos.append("💳 Débito")
        if d['requiere_nfc']: metodos.append("📲 Solo NFC")
        d['metodos_pago'] = ", ".join(metodos) if metodos else "Consultar Legales"
        
        resultados.append(d)
        
    return resultados