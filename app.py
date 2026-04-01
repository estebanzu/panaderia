from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from supabase import Client

from config import (
    ESTADO_COCINA,
    ESTADO_ENTREGADO,
    ESTADO_LISTO,
    ESTADO_PENDIENTE,
    MOBILE_CSS,
    PAGE_ICON,
    PAGE_LAYOUT,
    PAGE_TITLE,
    PRODUCTOS,
    TIME_OPTIONS,
    build_auth_config,
)
from utils import (
    actualizar_estado_pedido,
    build_cliente_whatsapp_url,
    build_cocina_whatsapp_url,
    build_msg_cliente,
    build_pedido_payload,
    build_resumen_cocina,
    format_delivery_date,
    guardar_pedido,
    init_supabase,
    normalize_text,
    obtener_pedidos_activos,
    eliminar_pedido,   # <-- NUEVO
)


st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT, page_icon=PAGE_ICON)
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

supabase: Client = init_supabase()


def create_authenticator() -> stauth.Authenticate:
    config = build_auth_config()
    return stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )


def eliminar_pedido_ui(id_pedido: int) -> None:
    """UI wrapper para eliminar pedidos con confirmación."""
    try:
        eliminar_pedido(supabase, id_pedido)
        st.toast("Pedido eliminado")
        st.session_state.pop(f"confirm_delete_{id_pedido}", None)
        st.rerun()
    except Exception as exc:
        st.error(f"Error eliminando pedido: {exc}")


def collect_customer_data() -> tuple[str, str, str]:
    with st.container():
        col_left, col_right = st.columns(2)
        cust_name = normalize_text(col_left.text_input("Nombre Cliente"))
        phone = normalize_text(col_right.text_input("WhatsApp (8 digitos)", placeholder="88888888"))
        address = normalize_text(st.text_area("Direccion Exacta"))
    return cust_name, phone, address


def collect_delivery_data() -> tuple[date, str]:
    st.subheader("Programacion de Entrega")
    col_left, col_right = st.columns(2)
    delivery_date = col_left.date_input("Dia de entrega", date.today())
    delivery_time = col_right.selectbox("Rango horario", TIME_OPTIONS)
    return delivery_date, delivery_time


def collect_order_items() -> dict:
    """Renders product quantity inputs and returns the selected order items."""
    order: dict = {}

    st.divider()

    header_name, header_price, header_qty = st.columns([3, 1, 1])
    header_name.markdown("**Producto**")
    header_price.markdown("**Precio**")
    header_qty.markdown("**Cant.**")

    st.divider()

    for product in PRODUCTOS:
        col_name, col_price, col_qty = st.columns([3, 1, 1])

        col_name.markdown(product["name"])
        col_price.markdown(f"₡ {product['price']:,}")

        qty = col_qty.number_input(
            "",
            min_value=0,
            step=1,
            key=f"v_{product['name']}"
        )

        if qty > 0:
            order[product["name"]] = {
                "qty": qty,
                "sub": qty * product["price"]
            }

    subtotal = sum(item["sub"] for item in order.values())

    st.divider()
    st.markdown(f"### Subtotal: ₡ {subtotal:,}")

    return order


def process_new_order(
    cust_name: str,
    phone: str,
    address: str,
    delivery_date: date,
    delivery_time: str,
    order: dict,
) -> None:
    """Persists an order and renders the WhatsApp action buttons."""
    errores = validar_pedido(cust_name, phone, address, order)
    if errores:
        for error in errores:
            st.warning(error)
        return

    total = sum(item["sub"] for item in order.values())
    fecha_str = format_delivery_date(delivery_date)
    resumen_cocina = build_resumen_cocina(cust_name, fecha_str, delivery_time, address, order)

    try:
        data = build_pedido_payload(
            cust_name=cust_name,
            phone=phone,
            address=address,
            resumen_cocina=resumen_cocina,
            total=total,
            fecha_str=fecha_str,
            delivery_time=delivery_time,
        )
        guardar_pedido(supabase, data)
        st.toast(f"Guardado: {cust_name}")
    except Exception as exc:
        st.error(f"Error DB: {exc}")
    
    msg_cliente = build_msg_cliente(cust_name, phone, address, fecha_str, delivery_time, total)
    st.link_button(
        "Enviar a Cliente",
        build_cliente_whatsapp_url(phone, msg_cliente),
        use_container_width=True,
    )
    st.link_button(
        "Enviar a Cocina",
        build_cocina_whatsapp_url(resumen_cocina),
        use_container_width=True,
    )


def render_admin_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica filtros de búsqueda y estado."""
    st.subheader("Filtros")

    col1, col2 = st.columns(2)
    search_term = col1.text_input("Buscar por cliente o teléfono")
    estado_filtro = col2.selectbox(
        "Filtrar por estado",
        ["Todos", ESTADO_PENDIENTE, ESTADO_COCINA, ESTADO_LISTO],
    )

    filtered_df = df.copy()

    if search_term:
        term = search_term.lower()
        filtered_df = filtered_df[
            filtered_df["cliente"].fillna("").str.lower().str.contains(term)
            | filtered_df["telefono"].fillna("").astype(str).str.lower().str.contains(term)
        ]

    if estado_filtro != "Todos":
        filtered_df = filtered_df[filtered_df["estado"] == estado_filtro]

    return filtered_df

def render_tab_ventas() -> None:
    """Renders the sales tab."""
    st.title("Generar Pedido")
    cust_name, phone, address = collect_customer_data()
    delivery_date, delivery_time = collect_delivery_data()
    order = collect_order_items()

    render_order_summary(cust_name, phone, address, delivery_date, delivery_time, order)

    st.divider()
    if st.button("Confirmar Pedido", use_container_width=True):
        process_new_order(cust_name, phone, address, delivery_date, delivery_time, order)

def validar_pedido(cust_name: str, phone: str, address: str, order: dict) -> list[str]:
    """Valida los campos del pedido y retorna lista de errores."""
    errores: list[str] = []

    if not cust_name:
        errores.append("Debes ingresar el nombre del cliente.")

    if not order:
        errores.append("Debes seleccionar al menos un producto.")

    if phone:
        clean_phone = "".join(ch for ch in phone if ch.isdigit())
        if len(clean_phone) != 8:
            errores.append("El WhatsApp debe tener 8 dígitos.")

    if not address:
        errores.append("Debes ingresar la dirección exacta.")

    return errores

def render_download_and_summary(df: pd.DataFrame) -> None:
    with st.expander("Herramientas de Resumen y Descarga", expanded=False):
        st.write("Usa estas herramientas para revisar todos los pedidos de un solo vistazo.")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar Historial (CSV)",
            data=csv,
            file_name=f"pedidos_panaderia_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.subheader("Vista rapida para Cocina")
        df_resumen = df[["fecha_entrega", "horario", "cliente", "detalle_cocina", "estado"]]
        st.table(df_resumen)


def render_estado_column(df: pd.DataFrame, source_state: str, title: str, button_label: str, next_state: str, prefix: str) -> None:
    """Renders a status column with expandable order cards."""
    st.subheader(title)
    df_filtrado = df[df["estado"] == source_state]

    for _, pedido in df_filtrado.iterrows():
        with st.expander(f"{prefix}: {pedido['cliente']}", expanded=True):
            if source_state == ESTADO_LISTO:
                st.write(f"Total: {pedido['total']:,}")
            else:
                st.write(pedido["detalle_cocina"])

            col1, col2 = st.columns(2)

            with col1:
                if st.button(button_label, key=f"btn_{next_state}_{pedido['id']}", use_container_width=True):
                    actualizar_estado_pedido(supabase, pedido["id"], next_state)
                    st.rerun()

            confirm_key = f"confirm_delete_{pedido['id']}"

            with col2:
                if not st.session_state.get(confirm_key, False):
                    if st.button("Eliminar", key=f"btn_del_{pedido['id']}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("¿Seguro que deseas eliminar este pedido?")

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("Sí, eliminar", key=f"btn_yes_del_{pedido['id']}", use_container_width=True):
                            eliminar_pedido_ui(pedido["id"])

                    with c2:
                        if st.button("Cancelar", key=f"btn_cancel_del_{pedido['id']}", use_container_width=True):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()


def render_admin_metrics(df: pd.DataFrame) -> None:
    """Muestra métricas rápidas del tablero."""
    total_pedidos = len(df)
    pendientes = len(df[df["estado"] == ESTADO_PENDIENTE])
    cocina = len(df[df["estado"] == ESTADO_COCINA])
    listos = len(df[df["estado"] == ESTADO_LISTO])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Activos", total_pedidos)
    col2.metric("Pendientes", pendientes)
    col3.metric("Cocinando", cocina)
    col4.metric("Listos", listos)

    st.divider()

def render_tab_admin() -> None:
    """Renders the admin board."""
    st.title("Tablero de Pedidos")
    df = obtener_pedidos_activos(supabase)

    if df.empty:
        st.info("No hay pedidos activos.")
        return

    render_admin_metrics(df)

    df_filtrado = render_admin_filters(df)

    if df_filtrado.empty:
        st.info("No hay pedidos que coincidan con los filtros.")
        return

    render_download_and_summary(df_filtrado)
    st.divider()

    col_pend, col_coci, col_list = st.columns(3)
    with col_pend:
        render_estado_column(df_filtrado, ESTADO_PENDIENTE, "Pendientes", "Empezar Cocina", ESTADO_COCINA, "Pedido")
    with col_coci:
        render_estado_column(df_filtrado, ESTADO_COCINA, "Cocinando", "Marcar como Listo", ESTADO_LISTO, "En proceso")
    with col_list:
        render_estado_column(df_filtrado, ESTADO_LISTO, "Listos", "Entregado", ESTADO_ENTREGADO, "Listo")

def render_order_summary(
    cust_name: str,
    phone: str,
    address: str,
    delivery_date: date,
    delivery_time: str,
    order: dict,
) -> None:
    """Muestra un resumen en vivo del pedido."""
    subtotal = sum(item["sub"] for item in order.values())

    st.divider()
    st.subheader("Resumen del Pedido")

    st.markdown(f"**Cliente:** {cust_name or '-'}")
    st.markdown(f"**WhatsApp:** {phone or '-'}")
    st.markdown(f"**Dirección:** {address or '-'}")
    st.markdown(f"**Entrega:** {format_delivery_date(delivery_date)}")
    st.markdown(f"**Horario:** {delivery_time}")

    if order:
        resumen_df = pd.DataFrame(
            [
                {
                    "Producto": nombre,
                    "Cant.": data["qty"],
                    "Subtotal": f"₡ {data['sub']:,}",
                }
                for nombre, data in order.items()
            ]
        )
        st.table(resumen_df)
    else:
        st.info("Aún no has agregado productos.")

    st.success(f"Subtotal actual: ₡ {subtotal:,}")

def main() -> None:
    authenticator = create_authenticator()
    authenticator.login(location="main")

    if st.session_state.get("authentication_status"):
        authenticator.logout("Cerrar Sesion", "sidebar")
        tab_ventas, tab_admin = st.tabs(["Nueva Venta", "Tablero de Control"])
        with tab_ventas:
            render_tab_ventas()
        with tab_admin:
            render_tab_admin()
    elif st.session_state.get("authentication_status") is False:
        st.error("Error de login")


if __name__ == "__main__":
    main()