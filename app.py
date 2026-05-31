import streamlit as st
from config.database import inicializar_sistema
from modules.admin import render_admin
from modules.checkpoint import render_checkpoint  # <-- Importamos el nuevo módulo

# Inicializar la base de datos al arrancar
inicializar_sistema()

# Configuración de página
st.set_page_config(page_title="Sistema MIN-CARD", page_icon="🪪", layout="wide")

# Menú de Navegación Lateral
st.sidebar.title("🪪 Menú MIN-CARD")
opcion = st.sidebar.radio("Ir a:", ["Punto de Control (Garita)", "Panel de Administración", "Asistente de IA"])

if opcion == "Punto de Control (Garita)":
    render_checkpoint()  # Llama al nuevo archivo que creamos

elif opcion == "Panel de Administración":
    render_admin()  # Llama a tu función original que ya tenías arreglada

elif opcion == "Asistente de IA":
    st.title("🤖 Asistente de Seguridad Minera")
    st.write("Próximamente: Integración del chatbot con el contexto del Excel.")