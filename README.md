# 🍞 Panadería Esteban: Order Management System

[cite_start]Una aplicación web robusta y optimizada para móviles diseñada para gestionar pedidos de panadería artesanal en el mercado de Costa Rica. [cite_start]Este sistema automatiza la toma de pedidos, centraliza la logística en la nube y facilita la comunicación directa con clientes y personal de cocina a través de WhatsApp.

## 🚀 Características Principales

* [cite_start]**Autenticación Segura**: Control de acceso integrado con `streamlit-authenticator` y soporte para persistencia de sesión mediante cookies de 30 días[cite: 1, 3].
* [cite_start]**Gestión de Inventario Dinámica**: Catálogo integrado de productos tradicionales (bollos, empanadas de chiverre, etc.) con cálculo automático de totales en Colones (₡)[cite: 1, 3].
* **Integración Inteligente con WhatsApp**:
    * [cite_start]**Cliente**: Envío de resumen detallado con instrucciones de pago SINPE Móvil[cite: 1, 4].
    * [cite_start]**Cocina**: Envío de comandas simplificadas directamente al personal de producción[cite: 1, 4].
* **Tablero de Control en Tiempo Real**:
    * [cite_start]Métricas de rendimiento como pedidos activos, confirmados, en preparación y listos[cite: 1, 28].
    * [cite_start]Flujo logístico por estados: Pendiente → Confirmado → Preparación → Listo → Ruta → Entregado[cite: 1, 21].
* **Historial Rápido**: Visualización de las últimas 5 ventas en el sidebar para una referencia operativa inmediata.
* [cite_start]**Optimización Mobile-First**: Interfaz diseñada con CSS personalizado para facilitar la entrada de datos en pantallas táctiles con botones y campos numéricos de gran tamaño[cite: 1, 3].

## 🛠️ Stack Tecnológico

* [cite_start]**Lenguaje**: Python 3.12+.
* [cite_start]**Frontend**: Streamlit.
* [cite_start]**Base de Datos**: Supabase (PostgreSQL) para persistencia de datos en tiempo real[cite: 1, 4].
* [cite_start]**Autenticación**: `streamlit-authenticator` v0.4.2.
* [cite_start]**Procesamiento de Datos**: Pandas.

## 📂 Estructura del Proyecto

```text
├── app.py                # Lógica principal de la interfaz y flujo de la aplicación
├── config.py             # Configuraciones globales, catálogo de productos y estilos CSS
├── utils.py              # Funciones auxiliares e integración con la API de Supabase
├── requirements.txt      # Dependencias del proyecto para despliegue
└── .streamlit/secrets.toml # Credenciales de base de datos y configuración de seguridad
