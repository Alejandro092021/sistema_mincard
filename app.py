import streamlit as st
from config.database import inicializar_sistema
from modules.admin import render_admin

# Inicializar la base de datos al arrancar
inicializar_sistema()

st.set_page_config(page_title="Plataforma MIN-CARD", layout="wide")
st.title("🛡️ Sistema Inteligente MIN-CARD")

# Menú de navegación lateral
menu = st.sidebar.radio(
    "Seleccione un Módulo:",
    ["⚙️ Administrador (CRUD)", "📊 Dashboard de Producción", "🤖 Asistente IA"]
)

if menu == "⚙️ Administrador (CRUD)":
    render_admin()
elif menu == "📊 Dashboard de Producción":
    st.info("Próxima Fase: Aquí pintaremos los paneles visuales de Miguel Romero y las gráficas generales.")
elif menu == "🤖 Asistente IA":
    st.info("Próxima Fase: Aquí conectaremos el LLM (IA) para interactuar con los datos cargados.")