import asyncio
import json
import logging
import os
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth 
from urllib.parse import urlparse

os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/scraper.log', level=logging.ERROR, format='%(asctime)s - %(message)s')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

KEYWORDS_TRANSPORTE = ["SUBE", "COLECTIVO", "TRANSPORTE", "PASAJE", "SUBTE"]

async def extraer_contenido_generico(page):
    """ Extractor unificado """
    contenido = ""
    try:
        await page.wait_for_timeout(1500)
        
        selectores_desc = [
            "div[role='region'][aria-label*='detalle']", 
            ".vs-offer-details", 
            "main", 
            "article"
        ]
        for sel in selectores_desc:
            try:
                el = await page.query_selector(sel)
                if el:
                    contenido += "DESCRIPCION:\n" + await el.inner_text() + "\n\n"
                    break
            except: continue

        dias_encontrados = []
        elementos_dias = await page.query_selector_all("div[role='img'][aria-label], div[title], span[title]")
        for el in elementos_dias:
            etiqueta = await el.get_attribute("aria-label") or await el.get_attribute("title")
            if etiqueta and etiqueta.upper().strip() in ["LUNES", "MARTES", "MIERCOLES", "MIÉRCOLES", "JUEVES", "VIERNES", "SABADO", "SÁBADO", "DOMINGO"]:
                dias_encontrados.append(etiqueta)
        
        if dias_encontrados:
            contenido += "VIGENCIA DIAS: " + ", ".join(set(dias_encontrados)) + ".\n\n"

        selectores_btn_tyc = ['div[data-testid="termsButton"]', '.legal-text-toggle', 'button:has-text("Términos")']
        for sel in selectores_btn_tyc:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(500)
            except: pass
        
        selectores_legales = [
            "div[data-testid='terms']", ".legal-text", ".terms", ".condiciones", ".disclaimer", 
            "div[class*='Legal']", ".legales", "small"
        ]
        found_legal = False
        for sel in selectores_legales:
            els = await page.query_selector_all(sel)
            for el in els:
                txt = await el.inner_text()
                if len(txt) > 20:
                    contenido += "TERMINOS Y CONDICIONES:\n" + txt + "\n"
                    found_legal = True
        
        if len(contenido) < 50:
            contenido = await page.inner_text('body')

        return contenido

    except Exception as e:
        print(f"      Error extrayendo contenido: {e}")
        return None

async def procesar_estrategia_spa(page, banco, datos_finales):
    print("   Modo SPA: Detectando tarjetas...")
    try: await page.click("#cookie-close", timeout=1000)
    except: pass

    selector = banco.get('selector_item', 'div')
    config_spa = banco.get('config_spa', {})
    
    tarjetas = await page.query_selector_all(selector)
    count = len(tarjetas)
    titulos_procesados = set() 

    for i in range(count):
        try:
            tarjetas_fresh = await page.query_selector_all(selector)
            if i >= len(tarjetas_fresh): break
            tarjeta = tarjetas_fresh[i]
            
            texto_preview = await tarjeta.inner_text()
            titulo_clean = texto_preview.strip().upper()

            if any(k in titulo_clean for k in KEYWORDS_TRANSPORTE):
                if titulo_clean in titulos_procesados: continue
                titulos_procesados.add(titulo_clean)
                
                print(f"      Ingresar a tarjeta en: {texto_preview[:15]}...")
                
                if config_spa.get('accion_apertura') == 'click':
                    await tarjeta.evaluate("el => el.click()")
                    await page.wait_for_timeout(config_spa.get('espera_carga', 2000))
                
                raw_data = await extraer_contenido_generico(page)
                
                if raw_data:
                    raw_data = f"CATEGORIA: {titulo_clean}\n{raw_data}"
                    datos_finales.append({
                        "banco": banco['nombre'], 
                        "url_detalle": banco['url'], 
                        "raw_data": raw_data
                    })
                    print("         TyC capturados.")
                
                if config_spa.get('accion_cierre') == 'ESCAPE':
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(1000)
                
        except Exception as e:
            print(f"      Error en {i}: {e}")
            await page.keyboard.press("Escape")

async def procesar_estrategia_link(context, page, banco, datos_finales):
    selector = banco.get('selector_item', 'a')
    try:
        await page.wait_for_selector(selector, timeout=10000)
    except: pass
    
    tarjetas = await page.query_selector_all(selector)
    links_a_procesar = []
    
    print(f"   Analizando {len(tarjetas)} tarjetas")

    for tarjeta in tarjetas:
        texto = await tarjeta.inner_text()
        if any(k in texto.upper() for k in KEYWORDS_TRANSPORTE):
            enlace = await tarjeta.query_selector('a')
            if not enlace: enlace = await tarjeta.query_selector("xpath=..")
            if enlace and await enlace.evaluate("el => el.tagName") != "A": enlace = None
            if not enlace: enlace = await tarjeta.query_selector('div a')

            if enlace:
                href = await enlace.get_attribute('href')
                if href:
                    if href.startswith('http'): full_url = href
                    else:
                        parsed_uri = urlparse(banco['url'])
                        domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
                        full_url = f"{domain}{href}"
                    
                    clean_url = full_url.split('?')[0]
                    if clean_url not in links_a_procesar:
                        links_a_procesar.append(clean_url)

    print(f"   Links : {len(links_a_procesar)}")
    
    for url in links_a_procesar:
        print(f"      Leyendo TyC de: {url}")
        p_detalle = await context.new_page()
        try:
            await p_detalle.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            selector_espera = banco.get('selector_espera_carga')
            if selector_espera:
                try:
                    await p_detalle.wait_for_selector(selector_espera, timeout=10000)
                except:
                    print(f"      Aviso: {banco['nombre']} tardó en cargar selector específico...")

            raw_data = await extraer_contenido_generico(p_detalle)
            if raw_data:
                datos_finales.append({
                    "banco": banco['nombre'], 
                    "url_detalle": url,
                    "raw_data": raw_data
                })
        except Exception as e:
            print(f"      Error navegando: {e}")
        finally:
            await p_detalle.close()

async def correr_motor():
    ruta_config = 'utils/config.json' if os.path.exists('utils/config.json') else 'config.json'
    with open(ruta_config, 'r') as f:
        config = json.load(f)

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(USER_AGENTS),
            locale="es-AR"
        )
        
        datos_finales = []

        for banco in config['bancos']:
            print(f"Extract en {banco['nombre']}")
            page = await context.new_page()
            
            try:
                await page.goto(banco['url'], wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                tipo = banco.get('tipo_extraccion', 'link_detalle')
                
                if tipo == 'spa_modal':
                    await procesar_estrategia_spa(page, banco, datos_finales)
                else:
                    await procesar_estrategia_link(context, page, banco, datos_finales)

            except Exception as e:
                print(f"Error en {banco['nombre']}: {e}")
            finally:
                await page.close()

        os.makedirs('data', exist_ok=True)
        with open('data/raw_extraction.json', 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, indent=4, ensure_ascii=False)
        
        await browser.close()
        print(f"\nProceso Finalizado.")

if __name__ == "__main__":
    asyncio.run(correr_motor())