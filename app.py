import streamlit as st
import streamlit_authenticator as stauth
import urllib.parse
import os
import pandas as pd
from datetime import datetime, date
import re  # Importamos para limpiar el número de teléfono

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

# --- 2. USER AUTHENTICATION CONFIG ---
my_hashed_password = '$2b$12$wCDqwrJdP0PxofFY3uLQNeHDlfEc0ujdJDIp8JVTH3fd9GkQlhYIS'

config = {
    "credentials": {
        "usernames": {
            "esteban": {
                "email": "estebanzu@gmail.com",
                "name": "Esteban Zuniga",
                "password": my_hashed_password 
            }
        }
    },
    "cookie": {
        "expiry_days": 30,
        "key": "bakery_secret_key",
        "name": "bakery_cookie"
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 3. RENDER LOGIN ---
authenticator.login(location='main')
auth_status = st.session_state.get("authentication_status")

if auth_status == False:
    st.error('Usuario o contraseña incorrectos.')
elif auth_status == None:
    st.info('Inicie sesión. (Usuario: esteban / Pass: admin123)')

# --- 4. PROTECTED CONTENT ---
elif auth_status:
    authenticator.logout('Cerrar Sesión', 'sidebar')
    st.sidebar.success(f"Hola, {st.session_state.get('name')}")

    def guardar_en_historial(nombre_cliente, telefono, direccion, fecha_entrega, horario, detalle_pedido, total):
        if not os.path.exists('pedidos'):
            os.makedirs('pedidos')
        
        filename = f"pedidos/{nombre_cliente.replace(' ', '_')}_{telefono}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(detalle_pedido)
        
        csv_file = 'pedidos_historial.csv'
        nuevo_registro = {
            "Fecha Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Fecha Entrega": fecha_entrega,
            "Cliente": nombre_cliente,
            "Telefono": telefono,
            "Direccion": direccion,
            "Horario": horario,
            "Total": total,
            "Metodo Pago": "SINPE Móvil"
        }
        df_nuevo = pd.DataFrame([nuevo_registro])
        if not os.path.isfile(csv_file):
            df_nuevo.to_csv(csv_file, index=False, encoding='utf-8')
        else:
            df_nuevo.to_csv(csv_file, mode='a', header=False, index=False, encoding='utf-8')

    st.title("🍞 Gestión de Pedidos Móvil")
    
    if st.button("🔄 Nuevo Cliente / Limpiar Todo"):
        st.rerun()

    st.info("💳 SINPE Móvil: **+506 8883-0657**")
    
    # UI Sections
    st.subheader("👤 Datos Cliente")
    c1, c2 = st.columns(2)
    cust_name = c1.text_input("Nombre")
    phone = c2.text_input("WhatsApp (8 dígitos)", placeholder="88888888")
    address = st.text_area("Dirección / Casa #", height=68)

    st.subheader("⏰ Entrega")
    t1, t2 = st.columns(2)
    delivery_date = t1.date_input("Día", date.today())
    time_options = ["Mañana: 9-10am", "Mañana: 10-11am", "Mañana: 11-12pm", "Tarde: 3-4pm", "Tarde: 4-5pm", "Tarde: 5-6pm"]
    delivery_time = t2.selectbox("Rango", time_options)

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
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        generar_btn = st.button("Generar y Guardar ✅", use_container_width=True)
    with btn_col2:
        if st.button("Limpiar Formulario 🗑️", use_container_width=True):
            st.rerun()

    if generar_btn:
        if not cust_name or not order:
            st.warning("Complete el nombre y el pedido.")
        else:
            fecha_str = delivery_date.strftime("%d/%m/%Y")
            
            # --- LIMPIEZA DEL NÚMERO DE TELÉFONO ---
            # Eliminamos cualquier cosa que no sea un número (espacios, guiones, etc)
            clean_phone = re.sub(r'\D', '', phone)
            
            # Si el usuario puso el número de 8 dígitos, le ponemos el 506
            if len(clean_phone) == 8:
                wa_phone = f"506{clean_phone}"
            else:
                wa_phone = clean_phone # Si ya traía el 506 o es otro formato, lo dejamos así

            msg = (
                f"*PEDIDO DE PANADERÍA*\n"
                f"👤 *Cliente:* {cust_name}\n"
                f"📞 *Tel:* {phone}\n"
                f"🏠 *Dirección:* {address}\n"
                f"📅 *Entrega:* {fecha_str}\n"
                f"⏰ *Horario:* {delivery_time}\n"
                f"----------------------------------\n"
            )
            total = 0
            for item, d in order.items():
                msg += f"• {d['qty']}x {item} (₡{d['sub']:,})\n"
                total += d['sub']
            
            msg += f"----------------------------------\n"
            msg += f"*TOTAL: ₡{total:,}*\n\n"
            msg += f"💳 *SINPE Móvil:* +506 88830657\n"
            msg += f"Favor enviar el comprobante. ¡Gracias!"
            
            try:
                guardar_en_historial(cust_name, phone, address, fecha_str, delivery_time, msg, total)
                st.success("Pedido guardado con éxito.")
            except:
                st.error("Error al guardar historial.")
            
            st.text_area("Copia el mensaje:", msg, height=200)
            
            # --- BOTÓN DE WHATSAPP ACTUALIZADO ---
            # Usamos la estructura https://wa.me/NÚMERO?text=MENSAJE
            url_wa = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(msg)}"
            st.link_button("🚀 Enviar a WhatsApp", url_wa, use_container_width=True)