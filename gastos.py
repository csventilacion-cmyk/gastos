import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Admin de Gastos", page_icon="🧾", layout="wide")

st.title("📂 Administrador de Gastos (Lector de XML)")
st.markdown("Sube tus facturas (XML) para generar el reporte en Excel.")

# --- FUNCIÓN: LIMPIAR NAMESPACES DEL SAT ---
def strip_namespace(tag):
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

# --- FUNCIÓN: PROCESAR CADA XML ---
def parsear_xml(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        
        # Estructura de datos
        data = {
            "Fecha": "",
            "Forma Pago": "",
            "Emisor": "",
            "RFC": "",
            "Subtotal": 0.0,
            "IVA": 0.0,
            "Otros Imp": 0.0, # IEPS, ISH, etc.
            "Total": 0.0,
            "UUID": "",
            "Archivo": file.name
        }

        # 1. Datos Generales
        data["Fecha"] = root.get("Fecha", "").split("T")[0]
        data["Forma Pago"] = root.get("FormaPago", "N/A")
        data["Subtotal"] = float(root.get("SubTotal", "0"))
        data["Total"] = float(root.get("Total", "0"))

        # 2. Navegar por los nodos (Emisor, Impuestos)
        iva_acumulado = 0.0
        otros_impuestos = 0.0
        
        for child in root:
            tag = strip_namespace(child.tag)
            
            if tag == "Emisor":
                data["Emisor"] = child.get("Nombre", "Sin Nombre")
                data["RFC"] = child.get("Rfc", "")
            
            if tag == "Complemento":
                for sub in child:
                    if strip_namespace(sub.tag) == "TimbreFiscalDigital":
                        data["UUID"] = sub.get("UUID", "")

            # Lógica de Impuestos (Globales)
            if tag == "Impuestos":
                # Traslados (IVA, IEPS)
                for imp in child:
                    if strip_namespace(imp.tag) == "Traslados":
                        for tras in imp:
                            tipo = tras.get("Impuesto", "") # 002=IVA
                            monto = float(tras.get("Importe", "0"))
                            if tipo == "002":
                                iva_acumulado += monto
                            else:
                                otros_impuestos += monto
                    
                    # Retenciones (Se suman a 'Otros' para cuadrar flujo, o se separan si prefieres)
                    if strip_namespace(imp.tag) == "Retenciones":
                        for ret in imp:
                            otros_impuestos += float(ret.get("Importe", "0"))

        data["IVA"] = iva_acumulado
        data["Otros Imp"] = otros_impuestos
        
        # Validación de seguridad: Si no hay nodo de impuestos pero Total > Subtotal
        if iva_acumulado == 0 and otros_impuestos == 0:
            diff = data["Total"] - data["Subtotal"]
            if diff > 0: data["IVA"] = diff

        return data

    except Exception as e:
        st.error(f"Error en {file.name}: {e}")
        return None

# --- INTERFAZ DE CARGA ---
uploaded_files = st.file_uploader("Arrastra aquí tus archivos XML", type=["xml"], accept_multiple_files=True)

if uploaded_files:
    # Procesar archivos
    lista_datos = []
    with st.spinner("Leyendo facturas..."):
        for f in uploaded_files:
            info = parsear_xml(f)
            if info:
                lista_datos.append(info)
    
    if lista_datos:
        df = pd.DataFrame(lista_datos)
        
        # Reordenar columnas visuales
        cols = ["Fecha", "Forma Pago", "Emisor", "RFC", "Subtotal", "IVA", "Otros Imp", "Total", "Archivo"]
        df = df[cols]
        
        # Mostrar Tabla
        st.success(f"✅ {len(df)} Facturas procesadas.")
        st.dataframe(df, use_container_width=True)
        
        # Totales
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Gasto Total", f"${df['Total'].sum():,.2f}")
        with c2: st.metric("IVA Total", f"${df['IVA'].sum():,.2f}")
        with c3: st.metric("Subtotal", f"${df['Subtotal'].sum():,.2f}")
        
        # --- EXPORTAR A EXCEL ---
        def to_excel(dataframe):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Gastos')
                workbook = writer.book
                worksheet = writer.sheets['Gastos']
                money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
                worksheet.set_column('E:H', 15, money_fmt) # Formato moneda a columnas E,F,G,H
            return output.getvalue()

        excel_file = to_excel(df)
        
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_file,
            file_name="Reporte_Gastos_CS.xlsx",
            mime="application/vnd.ms-excel"
        )
