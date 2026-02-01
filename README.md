💳 BeneficiosSUBE - Beneficios de Transporte
BeneficiosSUBE es una plataforma integral y autónoma diseñada para centralizar, procesar y visualizar los beneficios de transporte público dispersos en las webs de distintas fintechs o bancos tradicionales. El sistema utiliza técnicas de Web Scraping avanzado para recolectar datos, los persiste en una base de datos y los expone a través de una interfaz web moderna y responsiva.
 
- Arquitectura del Sistema
El proyecto sigue un modelo de flujo de datos tipo ETL (Extract, Transform, Load) automatizado:

Extracción (Scraper): Utiliza Playwright para navegar de forma programática y extraer beneficios incluso en sitios con carga dinámica (SPA).
Transformación: Limpia y normaliza los datos (elimina duplicados, normaliza días de la semana y detecta métodos de pago).
Carga (Loader): Mapea los datos procesados a un esquema SQL relacional.
Visualización: Un servidor FastAPI entrega la información a una Single Page Application (SPA) construida en JavaScript Vanilla.

- Modelo de Datos (DER)
La persistencia se realiza en SQLite mediante un diseño normalizado que garantiza la integridad y escalabilidad de los datos:

Entidad_Emisora: Almacena bancos/billeteras con su identidad visual (Logo y Color Hex).
Alcance_Geografico: Define las zonas de aplicación y tipos de transporte (Colectivo/Subte).
Vigencia_Temporal: Gestiona los días y periodos de validez de cada promoción.
Beneficio: Tabla central que vincula las entidades con sus descuentos y condiciones específicas.

- Stack Tecnológico
Backend: Python 3.10+, FastAPI, Uvicorn.
Scraping: Playwright, Playwright-Stealth.
Base de Datos: SQLite3 (Relacional).
Frontend: HTML5, CSS3 (Grid/Flexbox), JavaScript Vanilla.
Automatización: GitHub Actions (CI/CD) con ejecución programada.

- Instalación y Configuración
Sigue estos pasos para ejecutarla en entorno local:

1. Requisitos Previos
-- Python instalado (versión 3.10 o superior).

-- Git para clonar el repositorio.

2. Clonar y Preparar Entorno
# Clonar el repositorio
git clone https://github.com/tu-usuario/beneficiosSube.git
cd beneficiosSube

# Crear y activar entorno virtual
python -m venv .venv
En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
playwright install chromium
3. Ejecutar el Sistema
Puedes ejecutar el flujo completo o solo la interfaz web:

Scraper + Loader (Recolectar datos):

python main.py
Interfaz Web (Ver beneficios):

uvicorn web.main:app --reload
Luego abre http://127.0.0.1:8000 en tu navegador.

- Automatización (GitHub Actions)
El proyecto cuenta con un flujo de Git Scraping configurado en .github/workflows/schedule.yml. Este bot se ejecuta automáticamente todos los días a las 08:00 AM para:

-- Encender un entorno Linux efímero.
 
-- Ejecutar los scrapers.

-- Actualizar la base de datos beneficios.db.

-- Realizar un commit automático con los nuevos datos al repositorio.

- Estructura del Proyecto
beneficiosSube/
├── data/               # Base de datos SQLite y archivos JSON procesados
├── loaders/            # Lógica de carga a la base de datos (SQL)
├── logs/               # Historial de ejecución del scraper
├── scrapers/           # Scripts de extracción (Playwright)
├── utils/              # Configuración centralizada de bancos (logos, colores, URLs)
├── web/                # Aplicación Web (FastAPI, HTML, CSS, JS)
└── main.py             # Orquestador principal del proceso ETL