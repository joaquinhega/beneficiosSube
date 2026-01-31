import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def discovery_galicia(page):
    print("🔎 Galicia: Buscando beneficios...")
    try:
        await page.goto("https://www.galicia.ar/personas/promociones", wait_until="domcontentloaded", timeout=30000)
        # Usamos el selector que identificaste: h3.heading__title
        await page.wait_for_selector("h3.heading__title", timeout=15000)
        
        items = await page.query_selector_all("div.card-beneficio, .promo-card, article")
        promos = []
        for item in items:
            titulo_el = await item.query_selector("h3.heading__title")
            link_el = await item.query_selector("a.btn.primary")
            if titulo_el and link_el:
                titulo = await titulo_el.inner_text()
                link = await link_el.get_attribute("href")
                full_link = f"https://www.galicia.ar{link}" if link.startswith('/') else link
                promos.append({"banco": "Galicia", "titulo": titulo.strip(), "url": full_link})
        return promos
    except Exception as e:
        print(f"❌ Error Galicia: {e}")
        return []

async def discovery_santander(page):
    print("🔎 Santander: Extrayendo detalles específicos...")
    try:
        await page.goto("https://www.santander.com.ar/personas/beneficios#/", wait_until="commit", timeout=30000)
        
        # Selector del contenedor de la tarjeta
        selector_card = "div[class*='sc-fEXmlR']"
        await page.wait_for_selector(selector_card, timeout=20000)
        
        cards = await page.query_selector_all(selector_card)
        promos = []
        vistos = set() # Para evitar duplicados

        for card in cards:
            # Extraemos el texto completo para filtrar
            raw_text = await card.inner_text()
            
            # Limpieza básica: Si ya procesamos este texto, lo saltamos
            if raw_text in vistos: continue
            vistos.add(raw_text)

            if any(p in raw_text.lower() for p in ["subte", "colectivo", "transporte"]):
                # --- BUSQUEDA DE DETALLES (Usando tus hallazgos) ---
                # Porcentaje (buscamos el span con la clase sc-hdxRZL)
                porcentaje = await card.query_selector("span[class*='sc-hdxRZL'], .accordion-title")
                pct_text = await porcentaje.inner_text() if porcentaje else "Consultar %"

                # Vigencia (clase sc-cNYriL)
                vigencia = await card.query_selector("div[class*='sc-cNYriL']")
                vig_text = await vigencia.inner_text() if vigencia else "Ver vigencia"

                promos.append({
                    "banco": "Santander",
                    "titulo": raw_text.split('\n')[0], # Usualmente la primera línea es el título
                    "ahorro": pct_text.strip(),
                    "vigencia": vig_text.strip(),
                    "full_info": raw_text.replace('\n', ' | ')
                })
        return promos
    except Exception as e:
        print(f"❌ Error detalle Santander: {e}")
        return []

async def main():
    async with Stealth().use_async(async_playwright()) as p:
        # 1. Lanzamos con viewport específico para asegurar renderizado desktop
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 2. Ejecutamos discovery
        galicia = await discovery_galicia(page)
        santander = await discovery_santander(page)

        # 3. Consolidamos resultados limpios
        total_beneficios = galicia + santander
        resultados = {
            "fecha": "2026-01-29", # Fecha actual según sistema
            "cantidad": len(total_beneficios),
            "beneficios": total_beneficios
        }

        with open("beneficios_mendoza.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=4, ensure_ascii=False)
            
        print(f"\n✅ Proceso terminado. Se guardaron {len(total_beneficios)} beneficios reales.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())