import re
from datetime import datetime

class BeneficioSubeParser:
    """ Estructura el crudo para pasarlo a JSON """
    
    def __init__(self):
        self.regex_porcentaje = r"(\d+)\s?%"
        self.regex_monto = r"\$\s?(\d+(?:\.\d+)?)"
        self.dias_map = {
            "LUNES": "Lunes", "MARTES": "Martes", "MIERCOLES": "Miércoles", "MIÉRCOLES": "Miércoles",
            "JUEVES": "Jueves", "VIERNES": "Viernes", "SABADO": "Sábado", "SÁBADO": "Sábado", "DOMINGO": "Domingo"  
        }
        self.meses_map = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
        }

    def _limpiar_monto(self, monto_str):
        if not monto_str: return 0.0
        limpio = monto_str.replace(".", "").replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return 0.0
    
    def _detectar_nfc(self, texto):
        keywords = ["NFC", "CONTACTLESS", "SIN CONTACTO", "APPLE PAY", "GOOGLE PAY", "APPLEPAY", "GOOGLEPAY", "MODO"]
        return any(k in texto.upper() for k in keywords)

    def _detectar_subte(self, texto):
        return "SUBTE" in texto.upper()

    def _extraer_monto_minimo(self, texto):
        regex_min = r"(?:COMPRA|MONTO|GASTO|OPERACI[ÓO]N)\s+M[ÍI]NIM[OA]\s+(?:DE\s+)?\$?\s?(\d+(?:\.\d+)?)"
        match = re.search(regex_min, texto, re.IGNORECASE)
        if match:
            return self._limpiar_monto(match.group(1))
        return 0.0
    
    def _detectar_frecuencia(self, texto):
        """ Detecta la periodicidad del beneficio """
        texto_upper = texto.upper()
        if any(x in texto_upper for x in ["MENSUAL", "POR MES", "X MES", "MES"]):
            return "Mensual"
        if any(x in texto_upper for x in ["SEMANAL", "POR SEMANA"]):
            return "Semanal"
        if any(x in texto_upper for x in ["DIARIO", "POR DIA", "POR DÍA"]):
            return "Diaria"
        return "Por transacción"

    def _normalizar_fecha_iso(self, fecha_str):
        """ Convierte DD/MM/YYYY a YYYY-MM-DD """
        formatos = ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"]
        for fmt in formatos:
            try:
                dt = datetime.strptime(fecha_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError: continue
        return None

    def _parsear_fecha_texto(self, fecha_str):
        """ Parsea Fecha implicita a YYYY-MM-DD """
        try:
            fecha_str = fecha_str.lower().replace("  ", " ").strip()
            match = re.search(r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})", fecha_str)
            if match:
                dia, mes_nom, anio = match.groups()
                mes_num = self.meses_map.get(mes_nom)
                if mes_num: return f"{anio}-{mes_num}-{dia.zfill(2)}" 
        except: pass
        return None

    def _extraer_fechas_sql(self, texto):
        """ Retorna (fecha_inicio, fecha_fin) en formato YYYY-MM-DD."""
        texto_lower = texto.lower()
        inicio_iso = None
        fin_iso = None
        
        regex_num = r"(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})"
        matches_num = re.findall(regex_num, texto_lower)
        
        fechas_encontradas = []
        for f in matches_num:
            iso = self._normalizar_fecha_iso(f)
            if iso: fechas_encontradas.append(iso)

        if len(fechas_encontradas) < 2:
            regex_txt = r"(\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4})"
            matches_txt = re.findall(regex_txt, texto_lower)
            for f in matches_txt:
                iso = self._parsear_fecha_texto(f)
                if iso: fechas_encontradas.append(iso)

        fechas_ordenadas = sorted(list(set(fechas_encontradas))) 
        
        if len(fechas_ordenadas) >= 2:
            inicio_iso = fechas_ordenadas[0] 
            fin_iso = fechas_ordenadas[-1]  
        elif len(fechas_ordenadas) == 1:
            fin_iso = fechas_ordenadas[0]
            inicio_iso = datetime.now().strftime("%Y-%m-%d")
        else:
            inicio_iso = datetime.now().strftime("%Y-%m-%d")
            fin_iso = "2099-12-31"

        return inicio_iso, fin_iso

    def _extraer_dias(self, texto):
        texto_upper = texto.upper()
        if "VIGENCIA DIAS:" in texto_upper:
            try:
                parte_dias = texto_upper.split("VIGENCIA DIAS:")[1].split("\n")[0]
                encontrados = []
                for clave, valor in self.dias_map.items():
                    if clave in parte_dias: encontrados.append(valor)
                if encontrados: return encontrados
            except: pass

        if any(x in texto_upper for x in ["TODOS LOS DÍAS", "DIARIO", "TODOS LOS DIAS", "CADA DÍA"]): 
            return list(self.dias_map.values())
        
        encontrados = []
        for clave, valor in self.dias_map.items():
            if clave in texto_upper and valor not in encontrados: encontrados.append(valor)
        return encontrados if encontrados else list(self.dias_map.values())

    def _limpiar_terminos(self, texto_sucio):
        borrar = ["Menú", "Hacete Cliente", "Online Banking", "Cerrar sesión", "Ir al contenido", "Volver"]
        texto_limpio = texto_sucio
        for b in borrar:
            texto_limpio = texto_limpio.replace(b, "")
        
        texto_limpio = re.sub(r'\n\s*\n', '\n\n', texto_limpio).strip()
        if "DESCRIPCION:" in texto_limpio:
            texto_limpio = texto_limpio.split("DESCRIPCION:")[1]
            
        return texto_limpio[:800] + ("..." if len(texto_limpio) > 800 else "")

    def procesar_texto(self, texto_crudo, url_origen=""):
        texto_upper = texto_crudo.upper()

        if not any(k in texto_upper for k in ["SUBE", "COLECTIVO", "PASAJE", "SUBTE", "TRANSPORTE"]):
            return None 
        
        match_porc = re.search(self.regex_porcentaje, texto_crudo)
        porcentaje = float(match_porc.group(1)) if match_porc else 0.0

        montos = re.findall(self.regex_monto, texto_crudo)
        montos_float = [self._limpiar_monto(m) for m in montos]
        tope = max(montos_float) if montos_float else 0.0

        dias_lista = self._extraer_dias(texto_crudo)
        dias_string = ",".join(dias_lista) 
        
        fecha_inicio, fecha_fin = self._extraer_fechas_sql(texto_crudo)
        frecuencia = self._detectar_frecuencia(texto_crudo)

        requiere_nfc = self._detectar_nfc(texto_crudo)
        aplica_subte = self._detectar_subte(texto_crudo)
        monto_minimo = self._extraer_monto_minimo(texto_crudo)
        
        tyc = self._limpiar_terminos(texto_crudo)
        
        return {
            "porcentaje_descuento": porcentaje,
            "tope_reintegro": tope,
            "monto_minimo_consumo": monto_minimo,
            "requiere_nfc": requiere_nfc,
            "aplica_subte": aplica_subte,
            "url_detalle_promo": url_origen,
            "terminos_condiciones": tyc,
            
            "fecha_inicio": fecha_inicio, 
            "fecha_fin": fecha_fin,
            "dias_semana": dias_string,
            "frecuencia": frecuencia,
            
            "provincia_region": "Mendoza",
            
            "banco": "Desconocido"
        }