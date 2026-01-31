import asyncio
import json
import logging
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Configuración de Logs (Tarea: Manejo de Excepciones)
if not os.path.exists('logs'): os.makedirs('logs')
logging.basicConfig(filename='logs/scraper.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

async def extractor_crudo(page, url):
    """Módulo 1.2: Extrae el texto bruto de una URL específica."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        # Extraemos todo el texto del cuerpo de la página
        return await page.inner_text("body")
    except Exception as e:
        logging.error(f"Falla al extraer texto crudo en {url}: {e}")
        return ""

async def discovery_bot(p, banco_config):
    """Módulo 1.1: Recorre la landing y detecta links clave."""
    nombre = banco_config['nombre']
    url_landing = banco_config['url']
    selector_promo = banco_config['selector']
    
    # Implementación de Bloque Try-Except por Fuente
    try:
        print(f"🚀 Iniciando Discovery en {nombre}...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        await page.goto(url_landing, wait_until="commit")
        await page.wait_for_selector(selector_promo, timeout=15000)
        
        elementos = await page.query_selector_all(selector_promo)
        beneficios_detectados = []

        for el in elementos:
            texto_breve = await el.inner_text()
            # Filtro: SUBE o Transporte
            if any(key in texto_breve.upper() for key in ["SUBE", "TRANSPORTE", "COLECTIVO", "BENCINA"]):
                link = await el.query_selector("a")
                href = await link.get_attribute("href") if link else url_landing
                
                # Módulo 1.2: Entrar y extraer texto crudo
                print(f"  🔗 Entrando a detalle: {texto_breve[:30]}...")
                raw_data = await extractor_crudo(page, href)
                
                beneficios_detectados.append({
                    "banco": nombre,
                    "keyword_match": texto_breve.strip(),
                    "url": href,
                    "raw_text": raw_data[:500] # Guardamos solo los primeros 500 caracteres
                })
        
        await browser.close()
        return beneficios_detectados

    except Exception as e:
        # Manejo de excepciones: Registra y permite continuar con otro banco
        logging.error(f"Error crítico en módulo de {nombre}: {e}")
        print(f"⚠️ {nombre} falló, pero el proceso continúa. Revisar logs.")
        return []

async def main():
    configs = [
        {"nombre": "Galicia", "url": "https://www.galicia.ar/personas/promociones", "selector": "div.card-beneficio"},
        {"nombre": "Santander", "url": "https://www.santander.com.ar/personas/beneficios#/", "selector": "div[class*='sc-fEXmlR']"}
    ]

    async with Stealth().use_async(async_playwright()) as p:
        todas_las_promos = []
        for conf in configs:
            resultado = await discovery_bot(p, conf)
            todas_las_promos.extend(resultado)

        # Guardar resultados del Prototipo
        with open("data/raw_extraction.json", "w", encoding="utf-8") as f:
            json.dump(todas_las_promos, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Sprint 1 finalizado. Datos crudos guardados en 'data/raw_extraction.json'.")

if __name__ == "__main__":
    asyncio.run(main())