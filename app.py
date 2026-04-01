import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime, date
import re

# --- 0. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Panadería Esteban", layout="wide", page_icon="🍞")

# --- 1. ESTILOS CSS PARA UX MÓVIL (Botones Grandes) ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3.5em;
        width: 100%;
        border-radius: 12px;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        border: 2px solid #e0e0e0;
    }
    div.stButton > button:first-child:contains("Confirmar") {
        background-color: #28a745;
        color: white;
        border: none;
    }
    div.stButton > button:first-child:contains("WhatsApp"), 
    div.stButton > button:first-child:contains("Enviar a") {
        background-color: #25D366;
        color: white;
        border: none;
    }
    div.stButton > button:first-child:contains("Empezar") { background-color: #ffc107; color: black; }
    div.stButton > button:first-child:contains("Listo") { background-color: #17a2b8; color: white; }
    div.stButton > button:first-child:contains("Entregado") { background-color: #6c757d; color: white; }
    div.stNumberInput input { height: 3em !important; font-size: 18px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        client = create_client(url, key)
        return client
    except Exception as e:
        st.error("Error Crítico: No se encontraron los Secrets de Supabase.")
        st.stop()

supabase: Client = init_supabase()

# --- 3. AUTENTICACIÓN ---
my_hashed_password = '$2b$12$wCDqwrJdP0PxofFY3uLQNeHDlfEc0ujdJDIp8JVTH3fd9GkQlhYIS'
config = {
    "credentials": {"usernames": {"esteban": {"name": "Esteban Zuniga", "password": my_hashed_password}}},
    "cookie": {
        "expiry_days": 30, 
        "key": "esta_es_una_llave_super_secreta_y_larga_para_la_panaderia_zuniga_2026", 
        "name": "bakery_cookie"
    }
}

authenticator = stauth.Authenticate(config['credentials'], config['cookie']['name'], config['cookie']['key'], config['cookie']['expiry_days'])
authenticator.login(location='main')

if st.session_state.get("authentication_status"):
    authenticator.logout('Cerrar Sesión', 'sidebar')
    
    tab_ventas, tab_admin = st.tabs(["🛒 Nueva Venta", "📋 Tablero de Control"])

    # ---------------------------------------------------------
    # TAB 1: VENTAS (CON FECHA Y HORARIO RESTAURADOS)
    # ---------------------------------------------------------
    with tab_ventas:
        st.title("Generar Pedido")
        
        PRODUCTOS = [
            {"name": "Bollo de pan relleno de chiverre", "price": 2500},
            {"name": "Bollo de pan relleno de dulce de leche", "price": 2500},
            {"name": "Bollo de pan relleno de queso", "price": 2500},
            {"name": "Bollo de pan sin relleno", "price": 2000},
            {"name": "Bolsa de 4 bollitos de pan casero", "price": 1000},
            {"name": "Bolsa de 4 empanadas de chiverre", "price": 1200},
            {"name": "1 kilo de chiverre", "price": 4500},
            {"name": "1/2 kg de chiverre", "price": 2300}
        ]

        # Datos del Cliente
        with st.container():
            c1, c2 = st.columns(2)
            cust_name = c1.text_input("Nombre Cliente")
            phone = c2.text_input("WhatsApp (8 dígitos)", placeholder="88888888")
            address = st.text_area("Dirección Exacta")

        # --- SECCIÓN RESTAURADA: FECHA Y HORA ---
        st.subheader("⏰ Programación de Entrega")
        t1, t2 = st.columns(2)
        delivery_date = t1.date_input("Día de entrega", date.today())
        time_options = ["Mañana: 9-10am", "Mañana: 10-11am", "Mañana: 11-12pm", "Tarde: 3-4pm", "Tarde: 4-5pm", "Tarde: 5-6pm"]
        delivery_time = t2.selectbox("Rango horario", time_options)

        st.divider()
        st.subheader("Selección de Productos")
        order = {}
        for p in PRODUCTOS:
            col_n, col_p, col_q = st.columns([3, 1, 1])
            col_n.write(f"**{p['name']}**")
            col_p.write(f"₡{p['price']:,}")
            qty = col_q.number_input("Cant.", min_value=0, step=1, key=f"v_{p['name']}")
            if qty > 0:
                order[p['name']] = {"qty": qty, "sub": qty * p['price']}

        st.divider()
        
        if st.button("Confirmar Pedido ✅", use_container_width=True):
            if cust_name and order:
                total = sum(item['sub'] for item in order.values())
                fecha_str = delivery_date.strftime("%d/%m/%Y")
                
                # Resumen para cocina
                resumen_cocina = f"FECHA: {fecha_str} | HORA: {delivery_time}\n" + "\n".join([f"- {v['qty']}x {k}" for k, v in order.items()])
                
                try:
                    data = {
                        "cliente": cust_name, 
                        "telefono": phone, 
                        "direccion": address,
                        "detalle_cocina": resumen_cocina, 
                        "total": total, 
                        "estado": "Pendiente",
                        "fecha_entrega": fecha_str,  # Asegúrate de que estas columnas existan en Supabase
                        "horario": delivery_time
                    }
                    supabase.table("pedidos").insert(data).execute()
                    st.toast(f"💾 Guardado: {cust_name}", icon="✅")
                except Exception as e:
                    st.error(f"Error DB: {e}")

                # WhatsApp
                clean_phone = re.sub(r'\D', '', phone)
                wa_phone = f"506{clean_phone}" if len(clean_phone) == 8 else clean_phone
                msg_wa = (
                    f"*PEDIDO PANADERÍA*\n"
                    f"👤 Cliente: {cust_name}\n"
                    f"📅 Entrega: {fecha_str}\n"
                    f"⏰ Hora: {delivery_time}\n"
                    f"🏠 Dir: {address}\n"
                    f"Total: ₡{total:,}\n"
                    f"💳 SINPE: 8883-0657"
                )
                
                st.subheader("📲 Enviar Resúmenes")
                st.link_button("🚀 Enviar a Cliente (WhatsApp)", f"https://wa.me/{wa_phone}?text={urllib.parse.quote(msg_wa)}", use_container_width=True)
                st.link_button("👩‍🍳 Enviar a Mi Cocina (Tracking)", f"https://wa.me/50688554445?text={urllib.parse.quote(resumen_cocina)}", use_container_width=True)
            else:
                st.warning("Faltan datos.")

    # ---------------------------------------------------------
    # TAB 2: ADMIN (TRELLO)
    # ---------------------------------------------------------
    with tab_admin:
        st.title("Tablero de Pedidos")
        
        def actualizar_estado(id_pedido, nuevo_estado):
            supabase.table("pedidos").update({"estado": nuevo_estado}).eq("id", id_pedido).execute()
            st.rerun()

        try:
            res = supabase.table("pedidos").select("*").not_.eq("estado", "Entregado").execute()
            df = pd.DataFrame(res.data)
        except:
            df = pd.DataFrame()

        if not df.empty:
            col_pend, col_coci, col_list = st.columns(3)

            with col_pend:
                st.subheader("⏳ Pendientes")
                for _, p in df[df['estado'] == 'Pendiente'].iterrows():
                    with st.expander(f"📦 {p['cliente']}", expanded=True):
                        st.write(p['detalle_cocina'])
                        if st.button("Empezar Cocina 🔥", key=f"btn_c_{p['id']}", use_container_width=True):
                            actualizar_estado(p['id'], 'Cocina')

            with col_coci:
                st.subheader("🍳 Cocinando")
                for _, p in df[df['estado'] == 'Cocina'].iterrows():
                    with st.expander(f"🔥 {p['cliente']}", expanded=True):
                        st.write(p['detalle_cocina'])
                        if st.button("Marcar como Listo ✅", key=f"btn_l_{p['id']}", use_container_width=True):
                            actualizar_estado(p['id'], 'Listo')

            with col_list:
                st.subheader("🥡 Listos")
                for _, p in df[df['estado'] == 'Listo'].iterrows():
                    with st.expander(f"✅ {p['cliente']}", expanded=True):
                        st.write(f"Total: ₡{p['total']:,}")
                        if st.button("Entregado 🏁", key=f"btn_e_{p['id']}", use_container_width=True):
                            actualizar_estado(p['id'], 'Entregado')
        else:
            st.info("No hay pedidos activos.")

elif st.session_state.get("authentication_status") == False:
    st.error("Error de login")