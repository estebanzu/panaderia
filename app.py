import streamlit as st
import streamlit_authenticator as stauth
import urllib.parse
import os
import pandas as pd
from datetime import datetime, date
import re

# --- 0. PAGE CONFIGURATION ---
st.set_page_config(page_title="Pedidos Panadería", page_icon="🍞")

# --- 1. PRODUCTOS EMBEBIDOS ---
PRODUCTOS_LISTA = [
    {"name": "Bollo de pan relleno de chiverre", "price": 2500},
    {"name": "Bollo de pan relleno de dulce de leche", "price": 2500},
    {"name": "Bollo de pan relleno de queso", "price": 2500},
    {"name": "Bollo de pan sin relleno", "price": 2000},
    {"name": "Bolsa de 4 bollitos de pan casero", "price": 1000},
    {"name": "Bolsa de 4 empanadas de chiverre", "price": 1200},
    {"name": "1 kilo de chiverre", "price": 4500},
    {"name": "1/2 kg de chiverre", "price": 2300},
    {"name": "1/4 kg de chiverre", "price": 1300},
    {"name": "1/4 kg de miel de coco", "price": 2000}
]

# --- 2. AUTHENTICATION ---
my_hashed_password = '$2b$12$wCDqwrJdP0PxofFY3uLQNeHDlfEc0ujdJDIp8JVTH3fd9GkQlhYIS'
config = {
    "credentials": {"usernames": {"esteban": {"name": "Esteban Zuniga", "password": my_hashed_password}}},
    "cookie": {"expiry_days": 30, "key": "bakery_key", "name": "bakery_cookie"},
    "pre-authorized": {"emails": []}
}
authenticator = stauth.Authenticate(config['credentials'], config['cookie']['name'], config['cookie']['key'], config['cookie']['expiry_days'])

authenticator.login(location='main')
auth_status = st.session_state.get("authentication_status")

if auth_status:
    authenticator.logout('Cerrar Sesión', 'sidebar')
    
    st.title("🍞 Gestión de Pedidos")
    
    if st.button("🔄 Nuevo Cliente / Limpiar Todo"):
        st.rerun()

    # --- UI SECTIONS ---
    st.subheader("👤 Datos Cliente")
    c1, c2 = st.columns(2)
    cust_name = c1.text_input("Nombre")
    phone = c2.text_input("WhatsApp Cliente (8 dígitos)")
    address = st.text_area("Dirección / Casa #")

    st.subheader("⏰ Entrega")
    t1, t2 = st.columns(2)
    delivery_date = t1.date_input("Día", date.today())
    delivery_time = t2.selectbox("Rango", ["9-10am", "10-11am", "11am-12pm", "3-4pm", "4-5pm", "5-6pm"])

    st.subheader("🛒 Productos")
    order = {}
    for prod in PRODUCTOS_LISTA:
        col_n, col_p, col_c = st.columns([3, 1, 1])
        col_n.write(f"**{prod['name']}**")
        col_p.write(f"₡{prod['price']:,}")
        qty = col_c.number_input("Cant.", min_value=0, step=1, key=f"q_{prod['name']}")
        if qty > 0:
            order[prod['name']] = {"qty": qty, "sub": qty * prod['price']}

    st.markdown("---")
    
    if st.button("Generar Resúmenes ✅", use_container_width=True):
        if not cust_name or not order:
            st.warning("Complete el nombre y el pedido.")
        else:
            fecha_str = delivery_date.strftime("%d/%m/%Y")
            
            # 1. MENSAJE PARA EL CLIENTE (Completo)
            msg_cliente = (
                f"*PEDIDO PANADERÍA*\n"
                f"👤 *Cliente:* {cust_name}\n"
                f"📅 *Entrega:* {fecha_str} ({delivery_time})\n"
                f"🏠 *Dirección:* {address}\n"
                f"------------------\n"
            )
            total = 0
            for item, d in order.items():
                msg_cliente += f"• {d['qty']}x {item} (₡{d['sub']:,})\n"
                total += d['sub']
            
            msg_cliente += f"------------------\n"
            msg_cliente += f"*TOTAL: ₡{total:,}*\n\n"
            msg_cliente += f"💳 *SINPE:* 88830657\n"
            msg_cliente += f"Favor enviar comprobante. ¡Gracias!"

            # 2. MENSAJE PARA COCINA (Sencillo)
            msg_cocina = (
                f"👩‍🍳 *RESUMEN COCINA*\n"
                f"Cliente: {cust_name}\n"
                f"Fecha: {fecha_str} ({delivery_time})\n"
                f"------------------\n"
            )
            for item, d in order.items():
                msg_cocina += f"- {d['qty']}x {item}\n"
            
            # --- LINKS DE WHATSAPP ---
            # Limpiar número del cliente
            clean_phone = re.sub(r'\D', '', phone)
            wa_cliente = f"506{clean_phone}" if len(clean_phone) == 8 else clean_phone
            
            # Tu número fijo para cocina
            wa_mio = "50688554445"

            st.subheader("📲 Enviar Mensajes")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.link_button("🚀 Enviar a Cliente", 
                               f"https://wa.me/{wa_cliente}?text={urllib.parse.quote(msg_cliente)}", 
                               use_container_width=True)
            
            with col_b:
                st.link_button("👩‍🍳 Enviar a Cocina", 
                               f"https://wa.me/{wa_mio}?text={urllib.parse.quote(msg_cocina)}", 
                               use_container_width=True)

            st.text_area("Vista previa (Cocina):", msg_cocina, height=150)

elif auth_status == False:
    st.error('Usuario/Contraseña incorrectos')