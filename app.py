import streamlit as st
import pandas as pd
import math
import urllib.parse
import re

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Admin CS Ventilación",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS ---
st.markdown("""
    <style>
    .main-header { font-size: 28px; font-weight: bold; color: #0E4F8F; margin-bottom: 10px; }
    .price-tag { font-size: 24px; font-weight: bold; color: #28a745; }
    .profit-tag { font-size: 16px; font-weight: bold; color: #0E4F8F; background-color: #e6f2ff; padding: 8px; border-radius: 5px; border: 1px solid #b3d7ff; }
    .roi-box { padding: 15px; border-radius: 10px; background-color: #f0f2f6; margin-bottom: 10px; }
    .win-box { padding: 15px; border-radius: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; border: 1px solid #c3e6cb; }
    .warning-box { padding: 10px; background-color: #fff3cd; color: #856404; border-radius: 5px; border: 1px solid #ffeeba; }
    .danger-box { padding: 10px; background-color: #f8d7da; color: #721c24; border-radius: 5px; border: 1px solid #f5c6cb; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- 2. SISTEMA DE SEGURIDAD (LOGIN) ---
# ==========================================
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    
    # 👇 AQUÍ CAMBIAS TU CONTRASEÑA (Línea 23)
    SECRETO = "CS2026"  

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Interfaz de Login
    st.markdown("""<style>.stTextInput > label {display:none;}</style>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔒 Acceso Administrativo")
        st.caption("Sistema de Cotización y Rentabilidad CS")
        pwd_input = st.text_input("Ingrese Clave de Acceso", type="password")
        
        if st.button("Ingresar"):
            if pwd_input == SECRETO:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("⛔ Clave incorrecta")
            
    return False

if not check_password():
    st.stop()  # DETIENE EL CÓDIGO AQUÍ SI NO HAY CLAVE

# ==========================================
# --- 3. FUNCIONES Y DATOS ---
# ==========================================
@st.cache_data
def load_data():
    try:
        try:
            df = pd.read_excel("productos.xlsx")
        except:
            df = pd.read_csv("productos.xlsx")
            
        # Limpieza
        df['CATEGORIA'] = df['CATEGORIA'].astype(str).str.strip()
        df['Modelo'] = df['Modelo'].astype(str).str.strip()
        
        # Asegurar columnas numéricas
        cols_precios = ['precios de lista', 'precio contratista sin flete', 'precio fabrica', 'Precio Publico']
        for col in cols_precios:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"⚠️ Error leyendo la base de datos: {e}")
        return pd.DataFrame()

def parse_hp(hp_str):
    try:
        s = str(hp_str).lower().replace('hp', '').replace('motor', '').strip()
        if ' ' in s:
            parts = s.split()
            if len(parts) == 2:
                whole = float(parts[0])
                frac_parts = parts[1].split('/')
                if len(frac_parts) == 2:
                    return whole + (float(frac_parts[0])/float(frac_parts[1]))
        elif '/' in s:
            num, den = s.split('/')
            return float(num)/float(den)
        else:
            return float(s)
    except:
        return 0.0

def get_trans_cat(hp):
    if 0.25 <= hp <= 2.0: return "0.25-2HP"
    if 3.0 <= hp <= 5.0: return "3-5HP"
    if 7.5 <= hp <= 10.0: return "7.5-10HP"
    if 15.0 <= hp <= 30.0: return "15-30HP"
    return None

# --- CARGA DE DATOS ---
df = load_data()

if not df.empty:
    # Preparar Motores
    df_motors = df[df['CATEGORIA'].isin(['MONOFASICO', 'TRIFASICO'])].copy()
    df_motors['HP_Val'] = df_motors['PRODUCTO'].apply(
        lambda x: parse_hp(re.search(r'(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)\s*HP', str(x), re.IGNORECASE).group(1)) 
        if re.search(r'(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)\s*HP', str(x), re.IGNORECASE) else 0
    )
    # Preparar Transmisiones
    cat_trans = ["0.25-2HP", "3-5HP", "7.5-10HP", "15-30HP"]
    df_trans = df[df['CATEGORIA'].isin(cat_trans)].copy()

# ==========================================
# --- 4. INTERFAZ PRINCIPAL ---
# ==========================================

# --- SIDEBAR COMÚN ---
with st.sidebar:
    try:
        st.image("logo.jpg", use_column_width=True)
    except:
        st.header("CS VENTILACIÓN")
    
    st.title("CS Ventilación")
    st.caption("Herramientas Administrativas")
    
    st.markdown("---")
    if st.button("🔒 Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["💰 COTIZADOR DE PRECIOS", "⚡ ANÁLISIS ENERGÍA (ROI)"])

# ==========================================
# --- TAB 1: COTIZADOR (Tu código original) ---
# ==========================================
with tab1:
    st.markdown('<div class="main-header">COTIZADOR ADMINISTRATIVO</div>', unsafe_allow_html=True)
    
    # Configuración Cotizador (Dentro del Tab para no afectar al Tab 2)
    c_conf1, c_conf2, c_conf3 = st.columns(3)
    
    with c_conf1:
        tipo_cliente = st.selectbox("Lista de Precios:", 
                                    ["Publico en general", "cliente top LABPUE/CUL", "Costo CS ventilacion"])
        
        # Mapeo exacto a las columnas de tu Excel nuevo
        col_precio_map = {
            "Publico en general": "precios de lista",
            "cliente top LABPUE/CUL": "precio contratista sin flete",
            "Costo CS ventilacion": "precio fabrica"
        }
        
        col_venta = col_precio_map[tipo_cliente]
        col_costo = "precio fabrica"
        
        st.info(f"Cotizando con: **{tipo_cliente}**")

    with c_conf2:
        nom_proy = st.text_input("Nombre Proyecto")
        ciudad = st.text_input("Ciudad/Estado")
    
    with c_conf3:
        celular = st.text_input("Celular de Contacto")
        if st.button("🗑️ Limpiar Carrito"):
            st.session_state['carrito'] = []
            st.rerun()

    st.markdown("---")
    
    if df.empty:
        st.error("No se cargaron datos. Verifica 'productos.xlsx' en GitHub.")
        st.stop()

    col_sel, col_res = st.columns([1, 1.5])

    with col_sel:
        st.subheader("1. Selección de Modelo")
        
        cats_excluded = ['MONOFASICO', 'TRIFASICO', 'MOTOR'] + cat_trans
        cats_display = sorted([c for c in df['CATEGORIA'].unique() if c not in cats_excluded])
        
        categoria = st.selectbox("Categoría", cats_display)
        
        modelos_disp = sorted(df[df['CATEGORIA'] == categoria]['Modelo'].unique())
        modelo = st.selectbox("Modelo", modelos_disp)
        
        # Datos Base
        row_base = df[(df['CATEGORIA'] == categoria) & (df['Modelo'] == modelo)].iloc[0]
        desc_base = row_base['PRODUCTO']
        moneda = row_base['Moneda']
        
        # Precios dinámicos según columnas seleccionadas
        p_base_venta = row_base.get(col_venta, 0)
        p_base_costo = row_base.get(col_costo, 0)

    with col_res:
        st.subheader("2. Configuración y Precio")
        
        precio_unit_venta = p_base_venta
        precio_unit_costo = p_base_costo
        desc_final = desc_base
        error_msg = ""
        
        # --- LÓGICA MULTICURVA ---
        if categoria == "MULTICURVA":
            st.info("🛠️ Configuración de Motor y Transmisión requerida.")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                hps_disp = sorted(df_motors['HP_Val'].unique())
                hp_sel = st.selectbox("Potencia (HP)", hps_disp, format_func=lambda x: f"{x} HP")
            with c2:
                fase_sel = st.radio("Fase", ["MONOFASICO", "TRIFASICO"])
            with c3:
                rpm_req = st.number_input("RPM", 301, 2600, 1000, 50)
                
            # Motor
            motor_match = df_motors[(df_motors['HP_Val'] == hp_sel) & (df_motors['CATEGORIA'] == fase_sel)]
            p_motor_venta, p_motor_costo = 0, 0
            
            if not motor_match.empty:
                m_row = motor_match.iloc[0]
                p_motor_venta = m_row.get(col_venta, 0)
                p_motor_costo = m_row.get(col_costo, 0)
                st.success(f"✅ Motor: ${p_motor_venta:,.2f}")
            else:
                st.error("❌ Motor no disponible.")
                error_msg = "Motor no encontrado"
                
            # Transmisión
            cat_t = get_trans_cat(hp_sel)
            p_trans_venta, p_trans_costo = 0, 0
            
            if cat_t:
                trans_subset = df_trans[df_trans['CATEGORIA'] == cat_t]
                found_trans = False
                for _, t_row in trans_subset.iterrows():
                    try:
                        txt = str(t_row['PRODUCTO']).lower().replace(' a ', '-').strip()
                        r_min, r_max = map(int, txt.split('-'))
                        if r_min <= rpm_req <= r_max:
                            p_trans_venta = t_row.get(col_venta, 0)
                            p_trans_costo = t_row.get(col_costo, 0)
                            found_trans = True
                            break
                    except: continue
                
                if found_trans:
                    st.success(f"✅ Transmisión ({cat_t}): ${p_trans_venta:,.2f}")
                else:
                    st.warning(f"⚠️ Sin transmisión para {rpm_req} RPM")
            
            # Sumar todo
            precio_unit_venta += (p_motor_venta + p_trans_venta)
            precio_unit_costo += (p_motor_costo + p_trans_costo)
            
            desc_limpia = str(desc_base).replace("NO INCLUYE MOTOR NI TRANSMISION", "").replace(".", "")
            desc_final = f"{desc_limpia}. INCLUYE MOTOR {hp_sel} HP {fase_sel} Y TRANSMISIÓN PARA {rpm_req} RPM."
        else:
            st.write(f"**Descripción:** {desc_base}")
        
        # --- VISUALIZACIÓN ---
        st.markdown("---")
        st.markdown(f'<div class="price-tag">Precio Venta Unitario: ${precio_unit_venta:,.2f} {moneda}</div>', unsafe_allow_html=True)
        
        # CÁLCULO DE GANANCIA (PRIVADO)
        ganancia_unit = precio_unit_venta - precio_unit_costo
        porcentaje_margen = (ganancia_unit / precio_unit_venta * 100) if precio_unit_venta > 0 else 0
        
        st.markdown(f"""
        <div class="profit-tag">
            💰 Costo Real: ${precio_unit_costo:,.2f} | Utilidad: ${ganancia_unit:,.2f} ({porcentaje_margen:.1f}%)
        </div>
        """, unsafe_allow_html=True)
        
        qty = st.number_input("Cantidad", 1, 100, 1)
        
        total_venta = precio_unit_venta * qty
        total_costo = precio_unit_costo * qty
        total_ganancia = ganancia_unit * qty
        
        if 'carrito' not in st.session_state: st.session_state['carrito'] = []

        if st.button("🛒 Agregar al Pedido"):
            if error_msg:
                st.error(f"Error: {error_msg}")
            else:
                st.session_state['carrito'].append({
                    "Modelo": modelo,
                    "Descripción": desc_final,
                    "Cantidad": qty,
                    "Precio Unit.": precio_unit_venta,
                    "Total Venta": total_venta,
                    "Total Costo": total_costo,
                    "Ganancia": total_ganancia,
                    "Moneda": moneda
                })
                st.success("¡Agregado!")
                st.rerun()

    # --- RESUMEN ---
    st.markdown("---")
    st.header("📋 Resumen Económico del Proyecto")

    if len(st.session_state['carrito']) > 0:
        df_cart = pd.DataFrame(st.session_state['carrito'])
        
        st.dataframe(df_cart[["Cantidad", "Modelo", "Descripción", "Precio Unit.", "Total Venta", "Total Costo", "Ganancia", "Moneda"]], use_container_width=True)
        
        st.markdown("### 📊 Totales por Moneda")
        monedas = df_cart['Moneda'].unique()
        
        for m in monedas:
            df_m = df_cart[df_cart['Moneda'] == m]
            sum_venta = df_m['Total Venta'].sum()
            sum_costo = df_m['Total Costo'].sum()
            sum_ganancia = df_m['Ganancia'].sum()
            
            c1, c2, c3 = st.columns(3)
            with c1: st.metric(f"Venta Total ({m})", f"${sum_venta:,.2f}")
            with c2: st.metric(f"Costo Total ({m})", f"${sum_costo:,.2f}")
            with c3: st.metric(f"UTILIDAD NETA ({m})", f"${sum_ganancia:,.2f}", delta="Ganancia")
            st.markdown("---")

        # Botón de Correo
        subject = f"Pedido: {nom_proy} ({ciudad})"
        body = f"""SOLICITUD DE COMPRA / COTIZACIÓN

DATOS DEL CLIENTE:
Proyecto: {nom_proy}
Ciudad: {ciudad}
Celular: {celular}
Lista de Precios Usada: {tipo_cliente}

DETALLE DEL PEDIDO:
"""
        for item in st.session_state['carrito']:
            body += f"\n- ({item['Cantidad']}) {item['Modelo']}\n  {item['Descripción']}\n  Precio Venta: ${item['Total Venta']:,.2f} {item['Moneda']}\n"
        
        body += "\nRESUMEN VENTA:\n"
        for m in monedas:
            df_m = df_cart[df_cart['Moneda'] == m]
            body += f"Total ({m}): ${df_m['Total Venta'].sum():,.2f}\n"
        
        safe_sub = urllib.parse.quote(subject)
        safe_body = urllib.parse.quote(body)
        mailto = f"mailto:ventas@csventilacion.mx?subject={safe_sub}&body={safe_body}"
        
        st.markdown(f"""
        <a href="{mailto}" target="_blank" style="
            display: inline-block;
            background-color: #28a745;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            font-size: 18px;">
            ✉️ ENVIAR SOLICITUD A VENTAS@CS
        </a>
        """, unsafe_allow_html=True)

    else:
        st.info("El carrito está vacío.")

# ==========================================
# --- TAB 2: ANÁLISIS ENERGÍA (ROI) ---
# ==========================================
with tab2:
    st.markdown('<div class="main-header">COMPARATIVA DE CONSUMO Y ROI</div>', unsafe_allow_html=True)
    st.caption("Compara una opción eficiente (inversión alta) vs opción económica (consumo alto)")
    
    # --- 1. DATOS GENERALES ---
    st.subheader("1. Datos de Operación")
    c_dat1, c_dat2 = st.columns(2)
    with c_dat1:
        costo_kwh = st.number_input("Costo por kWh (MXN)", 0.5, 10.0, 4.0, 0.1)
        horas_dia = st.number_input("Horas de uso diario", 1, 24, 8)
    with c_dat2:
        dias_ano = st.number_input("Días de operación al año", 1, 365, 300)
        horas_anuales = horas_dia * dias_ano
        st.metric("Horas Anuales", f"{horas_anuales:,} h")
        
    st.markdown("---")
    
    # --- 2. COMPARATIVA EQUIPOS ---
    c_eq1, c_eq2 = st.columns(2)
    
    # EQUIPO A (Económico)
    with c_eq1:
        st.markdown("### 🔴 Opción A (Económica)")
        st.caption("Generalmente menor precio, mayor consumo.")
        modelo_a = st.text_input("Modelo A", "Axial Estándar")
        precio_a = st.number_input("Precio Equipo A ($)", 0.0, value=15000.0)
        bhp_a = st.number_input("BHP (Potencia al Freno) A", 0.1, 100.0, 5.0, 0.1)
        
        tipo_motor_a = st.selectbox("Eficiencia Motor A", ["Estándar (85%)", "Alta (89%)", "Premium (93%)", "Manual"], key="ma")
        if tipo_motor_a == "Manual": eff_a = st.number_input("Eficiencia % A", 50, 100, 85) / 100
        elif "85" in tipo_motor_a: eff_a = 0.85
        elif "89" in tipo_motor_a: eff_a = 0.89
        else: eff_a = 0.93
        
        # Cálculo Consumo A
        # kW = (BHP * 0.746) / Eficiencia
        kw_a = (bhp_a * 0.746) / eff_a
        gasto_anual_a = kw_a * horas_anuales * costo_kwh
        
        st.markdown(f"""
        <div class="roi-box">
            <h5>Consumo: {kw_a:.2f} kW</h5>
            <h4 style="color:#721c24">Gasto Anual Luz: ${gasto_anual_a:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)
        
    # EQUIPO B (Eficiente)
    with c_eq2:
        st.markdown("### 🟢 Opción B (Eficiente)")
        st.caption("Generalmente mayor precio, menor consumo.")
        modelo_b = st.text_input("Modelo B", "Centrífugo Premium")
        precio_b = st.number_input("Precio Equipo B ($)", 0.0, value=25000.0)
        bhp_b = st.number_input("BHP (Potencia al Freno) B", 0.1, 100.0, 3.5, 0.1)
        
        tipo_motor_b = st.selectbox("Eficiencia Motor B", ["Estándar (85%)", "Alta (89%)", "Premium (93%)", "Manual"], index=2, key="mb")
        if tipo_motor_b == "Manual": eff_b = st.number_input("Eficiencia % B", 50, 100, 93) / 100
        elif "85" in tipo_motor_b: eff_b = 0.85
        elif "89" in tipo_motor_b: eff_b = 0.89
        else: eff_b = 0.93
        
        # Cálculo Consumo B
        kw_b = (bhp_b * 0.746) / eff_b
        gasto_anual_b = kw_b * horas_anuales * costo_kwh
        
        st.markdown(f"""
        <div class="roi-box">
            <h5>Consumo: {kw_b:.2f} kW</h5>
            <h4 style="color:#155724">Gasto Anual Luz: ${gasto_anual_b:,.2f}</h4>
        </div>
        """, unsafe_allow_html=True)

    # --- 3. RESULTADOS ROI ---
    st.markdown("---")
    st.header("📊 Análisis de Retorno de Inversión")
    
    sobrecosto = precio_b - precio_a
    ahorro_anual = gasto_anual_a - gasto_anual_b
    
    c_res1, c_res2 = st.columns(2)
    
    with c_res1:
        st.metric("Inversión Adicional", f"${sobrecosto:,.2f}", help="Diferencia de precio entre B y A")
        st.metric("Ahorro Anual en Luz", f"${ahorro_anual:,.2f}", delta="Ahorro", delta_color="normal")
        
    with c_res2:
        if ahorro_anual > 0:
            roi_anos = sobrecosto / ahorro_anual
            roi_meses = roi_anos * 12
            
            st.markdown(f"""
            <div class="win-box">
                <h3>⏱️ Tiempo de Recuperación:</h3>
                <h1>{roi_meses:.1f} Meses</h1>
                <p>({roi_anos:.2f} años)</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Gráfica simple
            st.write(" **Proyección a 5 años:**")
            data = {
                "Año": [1, 2, 3, 4, 5],
                f"Gasto Acumulado {modelo_a}": [(precio_a + (gasto_anual_a * i)) for i in range(1, 6)],
                f"Gasto Acumulado {modelo_b}": [(precio_b + (gasto_anual_b * i)) for i in range(1, 6)]
            }
            df_chart = pd.DataFrame(data).set_index("Año")
            st.line_chart(df_chart)
            
        else:
            st.error("⚠️ La Opción B consume más energía que la A. No hay retorno de inversión por ahorro energético.")
