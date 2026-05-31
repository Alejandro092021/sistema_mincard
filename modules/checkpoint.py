import streamlit as st
from modules.validaciones import validar_acceso_minero
from config.database import registrar_intento_acceso, obtener_perfil_mincard

def render_checkpoint():
    st.title("🚧 Punto de Control y Validación (MIN-CARD)")
    st.write("Consulta de perfiles y reglas de acceso en tiempo real desde la Base de Datos.")
    
    # 1. Selección de la zona de control operativo
    zonas_operativas = ["Interior mina", "Polvorín", "Talleres", "Planta", "Oficinas", "Subestaciones"]
    zona_actual = st.selectbox("📍 Seleccione el Punto de Control Actual:", zonas_operativas)
    
    st.divider()
    
    # 2. Entrada del Código (Simulación de lectura de QR)
    id_tarjeta = st.text_input("💳 Escanee el QR o digite el código MIN-CARD (Ej: A-01, M-01, V-02):").strip().upper()
    
    if id_tarjeta:
        # CONSULTA DIRECTA A LA BASE DE DATOS (No usa Excel)
        datos_perfil = obtener_perfil_mincard(id_tarjeta)
        
        if datos_perfil:
            # Ejecutar el motor de validación de texto de la tarjeta
            # (Nota: en la BD la columna se llama 'acceso' y 'restriccion' en minúsculas)
            # Adaptamos las llaves para que la función de validación las lea correctamente
            perfil_adaptado = {
                'Acceso': datos_perfil.get('acceso', ''),
                'Restricción': datos_perfil.get('restriccion', '')
            }
            
            es_valido, mensaje = validar_acceso_minero(perfil_adaptado, zona_actual)
            
            # Recuperar el color guardado en la base de datos
            color_tarjeta = datos_perfil.get('color', 'Gray')
            if not color_tarjeta: 
                color_tarjeta = 'Gray'
            
            # Interfaz visual de los datos del maestro
            st.subheader("Datos del Perfil Detectado en Base de Datos:")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Cargo Asignado", value=datos_perfil['cargo'])
                st.write(f"**Área:** {datos_perfil['area']}")
                st.write(f"**Maquinaria Autorizada:** {datos_perfil['maquinaria']}")
            with col2:
                st.write(f"**Color de Fotocheck:** {color_tarjeta}")
                st.markdown(f"<div style='background-color:{color_tarjeta.lower()}; width:50px; height:20px; border-radius:5px; border:1px solid black;'></div>", unsafe_allow_html=True)

            st.divider()

            # Resolver visualmente la autorización
            if es_valido:
                st.success(f"🟢 **{mensaje}**")
                registrar_intento_acceso("EMP-SIMULADO", id_tarjeta, zona_actual, "PERMITIDO", mensaje)
            else:
                st.error(f"🔴 **{mensaje}**")
                registrar_intento_acceso("EMP-SIMULADO", id_tarjeta, zona_actual, "DENEGADO", mensaje)
                
        else:
            st.warning(f"⚠️ El código MIN-CARD '{id_tarjeta}' no está registrado en el maestro de la Base de Datos.")