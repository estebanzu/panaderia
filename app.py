import streamlit as st
import streamlit_authenticator as stauth
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime, date
import re

# --- 0. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="Panadería Esteban", layout="wide")

# Inicialización de la conexión con Logs
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    client = create_client(url, key)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] LOG: Conexión con Supabase establecida.")
    return client

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error("Error al conectar con la base de datos.")
    st.stop()

# --- 1. AUTENTICACIÓN ---
my_hashed_password = '$2b$12$wCDqwrJdP0PxofFY3uLQNeHDlfEc0ujdJDIp8JVTH3fd9GkQlhYIS'
config = {
    "credentials": {"usernames": {"esteban": {"name": "Esteban Zuniga", "password": my_hashed_password}}},
    "cookie": {"expiry_days": 30, "key": "esta_es_una_llave_super_secreta_y_larga_para_la_panaderia_zuniga", "name": "bakery_cookie"},
    "pre-authorized": {"emails": []}
}
authenticator = stauth.Authenticate(config['credentials'], config['cookie']['name'], config['cookie']['key'], config['cookie']['expiry_days'])

authenticator.login(location='main')

if st.session_state.get("authentication_status"):
    authenticator.logout('Cerrar Sesión', 'sidebar')
    
    # --- MENÚ DE NAVEGACIÓN ---
    tab_ventas, tab_admin = st.tabs(["🛒 Nueva Venta", "📋 Tablero de Control (Trello)"])

    # ---------------------------------------------------------
    # TAB 1: VENTAS
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

        c1, c2 = st.columns(2)
        cust_name = c1.text_input("Nombre Cliente")
        phone = c2.text_input("WhatsApp (8 dígitos)")
        address = st.text_area("Dirección")

        st.subheader("Selección")
        order = {}
        for p in PRODUCTOS:
            col_n, col_p, col_q = st.columns([3, 1, 1])
            col_n.write(f"**{p['name']}**")
            col_p.write(f"₡{p['price']:,}")
            qty = col_q.number_input("Cant.", min_value=0, step=1, key=f"v_{p['name']}")
            if qty > 0:
                order[p['name']] = {"qty": qty, "sub": qty * p['price']}

        if st.button("Confirmar Pedido ✅", use_container_width=True):
            if cust_name and order:
                total = sum(item['sub'] for item in order.values())
                resumen_cocina = "\n".join([f"- {v['qty']}x {k}" for k, v in order.items()])
                
                # --- LOG DE ESCRITURA ---
                with st.spinner("Escribiendo pedido en Supabase..."):
                    data = {
                        "cliente": cust_name,
                        "telefono": phone,
                        "direccion": address,
                        "detalle_cocina": resumen_cocina,
                        "total": total,
                        "estado": "Pendiente"
                    }
                    try:
                        supabase.table("pedidos").insert(data).execute()
                        st.toast(f"✅ Pedido de {cust_name} guardado en DB", icon="💾")
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] DB WRITE: Nuevo pedido de {cust_name} insertado.")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

                clean_phone = re.sub(r'\D', '', phone)
                wa_phone = f"506{clean_phone}" if len(clean_phone) == 8 else clean_phone
                msg_wa = f"Pedido Panadería\nCliente: {cust_name}\nTotal: ₡{total:,}\nSINPE: 88830657"
                
                st.success("¡Pedido listo!")
                st.link_button("🚀 Enviar a Cliente", f"https://wa.me/{wa_phone}?text={urllib.parse.quote(msg_wa)}")
                st.link_button("👩‍🍳 Enviar a Cocina", f"https://wa.me/50688554445?text={urllib.parse.quote(resumen_cocina)}")
            else:
                st.warning("Faltan datos.")

    # ---------------------------------------------------------
    # TAB 2: ADMIN (EL TRELLO)
    # ---------------------------------------------------------
    with tab_admin:
        st.title("Tablero de Pedidos")
        
        def actualizar_estado(id_pedido, nuevo_estado):
            # --- LOG DE ACTUALIZACIÓN ---
            try:
                supabase.table("pedidos").update({"estado": nuevo_estado}).eq("id", id_pedido).execute()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] DB UPDATE: Pedido {id_pedido} cambiado a {nuevo_estado}.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al actualizar: {e}")

        # --- LOG DE LECTURA ---
        with st.status("Sincronizando con Supabase...", expanded=False) as status:
            try:
                res = supabase.table("pedidos").select("*").not_.eq("estado", "Entregado").execute()
                df = pd.DataFrame(res.data)
                status.update(label="Sincronización completada", state="complete", expanded=False)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] DB READ: {len(df)} pedidos cargados.")
            except Exception as e:
                st.error(f"Error de lectura: {e}")
                df = pd.DataFrame()

        if not df.empty:
            col_pend, col_coci, col_list = st.columns(3)

            with col_pend:
                st.subheader("⏳ Pendientes")
                for _, p in df[df['estado'] == 'Pendiente'].iterrows():
                    with st.expander(f"📦 {p['cliente']}"):
                        st.caption(f"📍 {p['direccion']}")
                        st.write(p['detalle_cocina'])
                        if st.button("Empezar Cocina 🔥", key=f"btn_c_{p['id']}"):
                            actualizar_estado(p['id'], 'Cocina')

            with col_coci:
                st.subheader("🍳 En Cocina")
                for _, p in df[df['estado'] == 'Cocina'].iterrows():
                    with st.expander(f"🔥 {p['cliente']}"):
                        st.write(p['detalle_cocina'])
                        if st.button("Marcar como Listo ✅", key=f"btn_l_{p['id']}"):
                            actualizar_estado(p['id'], 'Listo')

            with col_list:
                st.subheader("🥡 Listos")
                for _, p in df[df['estado'] == 'Listo'].iterrows():
                    with st.expander(f"✅ {p['cliente']}"):
                        st.write(f"Total: ₡{p['total']:,}")
                        if st.button("Entregado 🏁", key=f"btn_e_{p['id']}"):
                            actualizar_estado(p['id'], 'Entregado')
        else:
            st.info("No hay pedidos activos por ahora.")

elif st.session_state.get("authentication_status") == False:
    st.error("Login incorrecto")