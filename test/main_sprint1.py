import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def ejecutar_entregable():
    # Configuración de bancos para el Discovery
    bancos = [
        {"nombre": "Galicia", "url": "https://www.galicia.ar/personas/promociones", "selector": "div.card-beneficio"},
        {"nombre": "Santander", "url": "https://www.santander.com.ar/personas/beneficios#/", "selector": "div[class*='sc-fEXmlR']"}
    ]

    print(f"{'='*80}")
    print(f"🏁 ENTREGABLE SPRINT 1 - MendoAhorro")
    print(f"{'='*80}\n")

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        # Configuración de contexto profesional
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        for banco in bancos:
            try:
                page = await context.new_page()
                await page.goto(banco['url'], wait_until="commit", timeout=30000)
                
                # Módulo 1.1: Discovery
                await page.wait_for_selector(banco['selector'], timeout=15000)
                elementos = await page.query_selector_all(banco['selector'])
                
                for el in elementos:
                    texto_crudo = await el.inner_text()
                    
                    # Filtro por palabras clave de transporte para Mendoza
                    if any(key in texto_crudo.upper() for key in ["SUBE", "TRANSPORTE", "COLECTIVO", "BENCINA", "NAFTA"]):
                        # Módulo 1.2: Extractor de Datos Crudos (Formato solicitado)
                        # Limpiamos saltos de línea para la impresión en consola
                        texto_limpio = texto_crudo.replace('\n', ' ').strip()
                        print(f"Entidad: {banco['nombre']} | Texto extraído: \"{texto_limpio[:120]}...\"")
                
                await page.close()
            except Exception as e:
                print(f"Entidad: {banco['nombre']} | ⚠️ Error en extracción: {str(e)[:50]}...")

        await browser.close()
        print(f"\n{'='*80}")
        print(f"✅ Prototipo Core finalizado con éxito.")

if __name__ == "__main__":
    asyncio.run(ejecutar_entregable())