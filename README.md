# 💳 BeneficiosSUBE

### Centralizador inteligente de beneficios para SUBE

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-API-success)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Playwright](https://img.shields.io/badge/Scraping-Playwright-orange)
![CI](https://img.shields.io/badge/GitHub_Actions-Automated-brightgreen)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## ¿Qué es BeneficiosSUBE?

**BeneficiosSUBE** es una plataforma que **centraliza, normaliza y visualiza** los beneficios de transporte público (SUBE) ofrecidos por **bancos y billeteras virtuales**, los cuales hoy se encuentran **fragmentados, mal estructurados o poco accesibles** en múltiples sitios web.

El proyecto automatiza la recolección de estos datos usando **Web Scraping avanzado**, los transforma en información limpia y estructurada, y los expone a través de una **interfaz web simple y entendible para cualquier usuario**.

> Pensado desde el punto de vista de la **persona común**, no del banco.

---

## Motivación del Proyecto

Hoy, una persona que quiere saber:

* Qué banco le devuelve más viajando en colectivo
* Qué días conviene usar determinada billetera
* Si un beneficio aplica en su provincia

Tiene que:

* Recorrer múltiples webs,
* Leer letras chicas,
* Interpretar condiciones poco claras.

**BeneficiosSUBE resuelve ese problema**, convirtiendo información dispersa y “sucia” en **datos claros, comparables y accesibles**.

---

## Arquitectura General (ETL)

El sistema sigue un enfoque **ETL automatizado**, orientado a datos reales y no ideales.

```text
┌────────────┐
│   Webs     │  Bancos / Fintechs
└─────┬──────┘
      │
      ▼
┌────────────┐
│ Scrapers   │  Playwright (SPA, JS dinámico)
└─────┬──────┘
      │
      ▼
┌────────────┐
│ Transform  │  Limpieza, normalización, deduplicación
└─────┬──────┘
      │
      ▼
┌────────────┐
│ SQLite DB  │  Modelo relacional normalizado
└─────┬──────┘
      │
      ▼
┌────────────┐
│ FastAPI    │  API REST
└─────┬──────┘
      │
      ▼
┌────────────┐
│ Web UI     │  SPA JS Vanilla
└────────────┘
```

---

## Modelo de Datos (DER)

Diseño relacional normalizado para garantizar integridad y escalabilidad.

**Entidades principales:**

* **Entidad_Emisora**

  * Bancos y billeteras
  * Logo
  * Color institucional

* **Alcance_Geografico**

  * Provincia / Ciudad
  * Tipo de transporte (Colectivo / Subte)

* **Vigencia_Temporal**

  * Días de la semana
  * Períodos promocionales

* **Beneficio**

  * Descuento
  * Tope
  * Condiciones
  * Relación con las entidades anteriores

---

## Stack Tecnológico

### Backend

* Python 3.10+
* FastAPI
* Uvicorn

### Scraping

* Playwright
* Playwright-Stealth
* Manejo de SPAs y carga dinámica

### Base de Datos

* SQLite (modelo relacional)

### Frontend

* HTML5
* CSS3 (Grid / Flexbox)
* JavaScript Vanilla

### DevOps / Automatización

* GitHub Actions
* Git Scraping programado

---

## Instalación y Uso

### 1️⃣ Requisitos

* Python 3.10+
* Git

---

### 2️⃣ Clonar y configurar entorno

```bash
git clone https://github.com/tu-usuario/beneficiosSube.git
cd beneficiosSube
```

```bash
python -m venv .venv
```

Activar entorno:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
playwright install chromium
```

---

### 3️⃣ Ejecución

**Ejecutar ETL completo (scraping + carga):**

```bash
python main.py
```

**Levantar interfaz web:**

```bash
uvicorn web.main:app --reload
```

Abrir en el navegador:

```
http://127.0.0.1:8000
```

---

## Automatización (GitHub Actions)

El proyecto incluye un workflow de **Git Scraping** en:

```
.github/workflows/schedule.yml
```

Se ejecuta **todos los días a las 08:00 AM** y:

* Inicializa entorno Linux
* Ejecuta scrapers
* Actualiza `beneficios.db`
* Commits automáticos con nuevos datos

El repositorio **se actualiza solo**, sin intervención humana.

---

## Estructura del Proyecto

```text
beneficiosSube/
├── data/               # SQLite + JSON procesados
├── loaders/            # Inserción y normalización SQL
├── logs/               # Logs de scraping
├── scrapers/           # Extracción Playwright
├── utils/              # Configuración de entidades (logos, colores, URLs)
├── web/                # FastAPI + UI
└── main.py             # Orquestador ETL
```

---

## Enfoque del Proyecto

* Datos reales y desordenados
* Problema cotidiano
* Automatización completa
* Escalable a nuevas entidades
* Pensado para usuarios no técnicos

---

## Proximas Extensiones...

* Filtros por provincia
* Comparador de bancos
* Historial de beneficios
* API pública
* Dashboard analítico