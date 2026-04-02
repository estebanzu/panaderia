from __future__ import annotations

import re
import urllib.parse
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st
from supabase import Client, create_client

from config import (
    DEFAULT_SINPE_MOVIL,
    DEFAULT_WA_COCINA,
    ESTADO_ENTREGADO,
    ESTADO_CANCELADO,
    TABLA_PEDIDOS,
    WA_PREFIX_CR,
    get_secret,
)


def obtener_ultimas_ventas(supabase: Client, limite: int = 5) -> pd.DataFrame:
    """Retorna las últimas N ventas (incluyendo entregadas) para el historial rápido."""
    try:
        response = (
            supabase
            .table(TABLA_PEDIDOS)
            .select("cliente, total, fecha_entrega, estado")
            .order("created_at", desc=True)
            .limit(limite)
            .execute()
        )
        return pd.DataFrame(response.data or [])
    except Exception:
        return pd.DataFrame()

def normalize_text(value: Any) -> str:
    """Normalizes text inputs while preserving original functionality."""
    if value is None:
        return ""
    return str(value).strip()


@st.cache_resource
def init_supabase() -> Client:
    """Creates and caches a Supabase client using Streamlit secrets."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        st.error("Error Critico: No se encontraron los Secrets de Supabase.")
        st.stop()


def sanitize_phone(phone: str) -> str:
    """Keeps only digits in a phone number."""
    return re.sub(r"\D", "", normalize_text(phone))



def build_whatsapp_phone(phone: str) -> str:
    """Builds a WhatsApp-ready phone number preserving current app behavior."""
    clean_phone = sanitize_phone(phone)
    return f"{WA_PREFIX_CR}{clean_phone}" if len(clean_phone) == 8 else clean_phone



def format_delivery_date(delivery_date: date) -> str:
    """Formats the delivery date exactly as the current app expects."""
    return delivery_date.strftime("%d/%m/%Y")


def eliminar_pedido(supabase, id_pedido):
    """Elimina un pedido por ID"""
    return supabase.table("pedidos").delete().eq("id", id_pedido).execute()


def eliminar_pedido_ui(st, supabase, id_pedido):
    try:
        eliminar_pedido(supabase, id_pedido)
        st.toast("Pedido eliminado")
        st.rerun()
    except Exception as e:
        st.error(f"Error eliminando pedido: {e}")


def build_resumen_cocina(
    cust_name: str,
    fecha_str: str,
    delivery_time: str,
    address: str,
    order: dict,
    observaciones: str,
) -> str:
    """Builds the kitchen summary text."""
    encabezado = (
        f"RESUMEN COCINA\n"
        f"Cliente: {cust_name}\n"
        f"Fecha: {fecha_str} ({delivery_time})\n"
        f"Direccion: {address}\n"
        f"-------------------\n"
    )
    detalle = "\n".join([f"- {value['qty']}x {key}" for key, value in order.items()])

    if observaciones:
        resumen += f"\n-------------------\nObservaciones: {observaciones}"

    return encabezado + detalle



def build_msg_cliente(
    cust_name: str,
    phone: str,
    address: str,
    fecha_str: str,
    delivery_time: str,
    total: int,
) -> str:
    """Builds the customer WhatsApp text."""
    sinpe_movil = get_secret("SINPE_MOVIL", DEFAULT_SINPE_MOVIL)
    return (
        f"*PEDIDO PANADERIA*\n\n"
        f"*Cliente:* {cust_name}\n"
        f"*Telefono:* {phone}\n"
        f"*Direccion:* {address}\n"
        f"*Entrega:* {fecha_str}\n"
        f"*Hora:* {delivery_time}\n"
        f"-------------------\n"
        f"*TOTAL:* Colones {total:,}\n\n"
        f"SINPE Movil: {sinpe_movil}\n"
        f"Favor enviar el comprobante. ¡Gracias!"
    )



def build_cliente_whatsapp_url(phone: str, message: str) -> str:
    """Builds the WhatsApp URL for the client."""
    return f"https://wa.me/{build_whatsapp_phone(phone)}?text={urllib.parse.quote(message)}"



def build_cocina_whatsapp_url(resumen_cocina: str) -> str:
    """Builds the WhatsApp URL for the kitchen."""
    cocina_phone = get_secret("WHATSAPP_COCINA", DEFAULT_WA_COCINA)
    return f"https://wa.me/{cocina_phone}?text={urllib.parse.quote(resumen_cocina)}"



def build_pedido_payload(
    cust_name: str,
    phone: str,
    address: str,
    observaciones: str,
    resumen_cocina: str,
    total: int,
    fecha_str: str,
    delivery_time: str,
) -> dict:
    """Builds the database payload for a new order."""
    return {
        "cliente": cust_name,
        "telefono": phone,
        "direccion": address,
        "observaciones": observaciones,
        "detalle_cocina": resumen_cocina,
        "total": total,
        "estado": "Pendiente",
        "fecha_entrega": fecha_str,
        "horario": delivery_time,
    }



def guardar_pedido(supabase: Client, data: dict) -> None:
    """Inserts an order into Supabase."""
    supabase.table(TABLA_PEDIDOS).insert(data).execute()



def actualizar_estado_pedido(supabase: Client, id_pedido: Any, nuevo_estado: str) -> None:
    """Updates the status of a specific order."""
    supabase.table(TABLA_PEDIDOS).update({"estado": nuevo_estado}).eq("id", id_pedido).execute()



def obtener_pedidos_activos(supabase: Client) -> pd.DataFrame:
    """Returns all active (non-delivered, non-cancelled) orders as a DataFrame."""
    try:
        response = (
            supabase
            .table(TABLA_PEDIDOS)
            .select("*")
            .not_.in_("estado", [ESTADO_ENTREGADO, ESTADO_CANCELADO])
            .execute()
        )
        return pd.DataFrame(response.data or [])
    except Exception:
        return pd.DataFrame()
