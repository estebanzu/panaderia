from __future__ import annotations

import streamlit as st

PAGE_TITLE = "Panaderia Esteban"
PAGE_LAYOUT = "wide"
PAGE_ICON = "Bread"

TABLA_PEDIDOS = "pedidos"
WA_PREFIX_CR = "506"
DEFAULT_WA_COCINA = "50688554445"
DEFAULT_SINPE_MOVIL = "8883-0657"
DEFAULT_AUTH_USERNAME = "esteban"
DEFAULT_AUTH_NAME = "Esteban Zuniga"
DEFAULT_AUTH_HASHED_PASSWORD = "$2b$12$wCDqwrJdP0PxofFY3uLQNeHDlfEc0ujdJDIp8JVTH3fd9GkQlhYIS"
DEFAULT_AUTH_COOKIE_NAME = "bakery_cookie"
DEFAULT_AUTH_COOKIE_KEY = "esta_es_una_llave_super_secreta_y_larga_para_la_panaderia_zuniga_2026"
DEFAULT_AUTH_COOKIE_EXPIRY_DAYS = 30

ESTADO_PENDIENTE = "Pendiente"
ESTADO_COCINA = "Cocina"
ESTADO_LISTO = "Listo"
ESTADO_ENTREGADO = "Entregado"
ESTADOS_ACTIVOS = [ESTADO_PENDIENTE, ESTADO_COCINA, ESTADO_LISTO]

TIME_OPTIONS = [
    "9-10am",
    "10-11am",
    "11-12pm",
    "3-4pm",
    "4-5pm",
    "5-6pm",
]

PRODUCTOS = [
    {"name": "Bollo de pan relleno de chiverre", "price": 2500},
    {"name": "Bollo de pan relleno de dulce de leche", "price": 2500},
    {"name": "Bollo de pan relleno de queso", "price": 2500},
    {"name": "Bollo de pan sin relleno", "price": 2000},
    {"name": "Bolsa de 4 bollitos de pan casero", "price": 1000},
    {"name": "Bolsa de 4 empanadas de chiverre", "price": 1200},
    {"name": "1 kilo de chiverre", "price": 4500},
    {"name": "1/2 kg de chiverre", "price": 2300},
]

MOBILE_CSS = """
<style>

/* Botones principales */
div.stButton > button:first-child {
    height: 3.8em;
    width: 100%;
    border-radius: 12px;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 10px;
    border: 2px solid #e0e0e0;
}

/* Campo number input grande */
div[data-testid="stNumberInput"] input {
    height: 70px !important;
    font-size: 26px !important;
    text-align: center !important;
}

/* Botones + y - grandes */
button[aria-label="Increment value"],
button[aria-label="Decrement value"] {
    height: 70px !important;
    width: 70px !important;
    font-size: 22px !important;
}

/* Espaciado entre filas */
div[data-testid="stNumberInput"] {
    margin-top: 6px;
    margin-bottom: 12px;
}

/* Ajuste extra para pantallas pequeñas */
@media (max-width: 768px) {

    div[data-testid="stNumberInput"] input {
        height: 80px !important;
        font-size: 28px !important;
    }

    button[aria-label="Increment value"],
    button[aria-label="Decrement value"] {
        height: 80px !important;
        width: 80px !important;
    }

}

</style>
"""


def get_secret(key: str, default=None):
    """Returns a Streamlit secret when available, otherwise the provided default."""
    try:
        return st.secrets[key]
    except Exception:
        return default


def build_auth_config() -> dict:
    """Builds the streamlit-authenticator config using Streamlit secrets with safe defaults."""
    username = get_secret("AUTH_USERNAME", DEFAULT_AUTH_USERNAME)
    display_name = get_secret("AUTH_NAME", DEFAULT_AUTH_NAME)
    hashed_password = get_secret("AUTH_HASHED_PASSWORD", DEFAULT_AUTH_HASHED_PASSWORD)
    cookie_name = get_secret("AUTH_COOKIE_NAME", DEFAULT_AUTH_COOKIE_NAME)
    cookie_key = get_secret("AUTH_COOKIE_KEY", DEFAULT_AUTH_COOKIE_KEY)
    cookie_expiry_days = int(get_secret("AUTH_COOKIE_EXPIRY_DAYS", DEFAULT_AUTH_COOKIE_EXPIRY_DAYS))

    return {
        "credentials": {
            "usernames": {
                username: {
                    "name": display_name,
                    "password": hashed_password,
                }
            }
        },
        "cookie": {
            "expiry_days": cookie_expiry_days,
            "key": cookie_key,
            "name": cookie_name,
        },
    }
