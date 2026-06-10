import streamlit as st
import re
from datetime import datetime
from config.database import registrar_intento_acceso, ejecutar_query

# Intentar importar librerías para la cámara y procesamiento de imagen (OpenCV)
try:
    import cv2
    import numpy as np
    from PIL import Image
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# =========================================================================
# --- MODAL: VALIDACIÓN PARA ACTUALIZAR TAREA (TERMINADO / NO TERMINADO) ---
# =========================================================================
@st.dialog("🔒 Validar Actualización de Tarea")
def modal_actualizar_tarea(empleado_uid, operacion_id, nombre_tarea, nuevo_estado):
    st.markdown(f"Para marcar la actividad **{nombre_tarea}** como **{nuevo_estado}**, escanee la credencial del trabajador.")
    
    qr_val_data = None
    tab_cam, tab_file, tab_man = st.tabs(["📷 Cámara", "📁 Subir QR", "⌨️ Manual"])
    
    with tab_cam:
        if HAS_CV2:
            foto_capturada = st.camera_input("Capturar QR para validar", key=f"cam_val_{operacion_id}_{nuevo_estado}")
            if foto_capturada is not None:
                img_pil = Image.open(foto_capturada)
                img_array = np.array(img_pil)
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                detector = cv2.QRCodeDetector()
                texto_qr, _, _ = detector.detectAndDecode(img_bgr)
                if texto_qr:
                    qr_val_data = texto_qr
                else:
                    st.error("❌ No se pudo leer el QR.")
    
    with tab_file:
        if HAS_CV2:
            archivo_subido = st.file_uploader("Subir QR para validar", type=["jpg", "png", "jpeg"], key=f"file_val_{operacion_id}_{nuevo_estado}")
            if archivo_subido is not None:
                img_pil = Image.open(archivo_subido)
                img_array = np.array(img_pil)
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                detector = cv2.QRCodeDetector()
                texto_qr, _, _ = detector.detectAndDecode(img_bgr)
                if texto_qr:
                    qr_val_data = texto_qr
                else:
                    st.error("❌ No se encontró QR legible.")
                    
    with tab_man:
        entrada_manual = st.text_input("Digite el código MIN-CARD:", key=f"man_val_{operacion_id}_{nuevo_estado}").strip()
        if entrada_manual:
            qr_val_data = entrada_manual

    if qr_val_data:
        id_val = qr_val_data.upper()
        if "MIN-CARD DIGITAL" in qr_val_data:
            match = re.search(r"MIN-CARD:\s*([A-Z0-9-]+)", qr_val_data, re.IGNORECASE)
            if match:
                id_val = match.group(1).upper()
                
        if id_val == empleado_uid:
            ejecutar_query("UPDATE empleado_operaciones SET estado = ? WHERE empleado_uid = ? AND operacion_id = ?", (nuevo_estado, empleado_uid, operacion_id))
            st.success(f"✅ Tarea actualizada a '{nuevo_estado}' exitosamente.")
            if st.button("Cerrar y Actualizar Pantalla", use_container_width=True):
                st.rerun()
        else:
            st.error(f"❌ El código escaneado ({id_val}) NO corresponde al trabajador asignado ({empleado_uid}).")

# =========================================================================
# --- VISTA PRINCIPAL ---
# =========================================================================
def render_checkpoint():
    if "checkpoint_emp_id" not in st.session_state:
        st.session_state.checkpoint_emp_id = None

    st.title("🚧 Punto de Control y Validación (Garita)")
    st.write("Control de accesos con registro de tiempo y gestión estricta de tareas operativas.")
    
    col_izq, col_der = st.columns([1, 1.2], gap="large")
    nuevo_qr_escaneado = None  
    
    # =========================================================================
    # --- PANEL IZQUIERDO: CONFIGURACIÓN Y ESCÁNER ---
    # =========================================================================
    with col_izq:
        st.markdown("### ⚙️ Configuración del Control")
        df_areas_db = ejecutar_query("SELECT nombre FROM areas WHERE activo = 1", retornar_datos=True)
        if df_areas_db is not None and not df_areas_db.empty:
            zonas_operativas = df_areas_db['nombre'].tolist()
        else:
            zonas_operativas = ["Interior mina", "Polvorín", "Talleres", "Planta", "Oficinas", "Subestaciones"]
            
        zona_actual = st.selectbox("📍 Punto de Control Actual:", zonas_operativas)
        
        st.divider()
        st.markdown("### 🔍 Escanear Nueva Credencial")
        
        if not HAS_CV2:
            st.error("⚠️ Falta instalar librerías. Ejecuta: `pip install opencv-python numpy pillow`")
        
        tab_cam, tab_file, tab_man = st.tabs(["📷 Cámara Web", "📁 Subir Imagen QR", "⌨️ Manual"])
        
        with tab_cam:
            if HAS_CV2:
                foto_capturada = st.camera_input("Capturar QR", key="main_cam")
                if foto_capturada is not None:
                    img_pil = Image.open(foto_capturada)
                    img_array = np.array(img_pil)
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    detector = cv2.QRCodeDetector()
                    texto_qr, _, _ = detector.detectAndDecode(img_bgr)
                    if texto_qr:
                        nuevo_qr_escaneado = texto_qr
                    else:
                        st.error("❌ No se pudo leer el QR.")
            
        with tab_file:
            if HAS_CV2:
                archivo_subido = st.file_uploader("Seleccionar archivo de imagen:", type=["jpg", "png", "jpeg"], key="main_file")
                if archivo_subido is not None:
                    img_pil = Image.open(archivo_subido)
                    img_array = np.array(img_pil)
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    detector = cv2.QRCodeDetector()
                    texto_qr, _, _ = detector.detectAndDecode(img_bgr)
                    if texto_qr:
                        nuevo_qr_escaneado = texto_qr
                    else:
                        st.error("❌ No se encontró QR legible.")

        with tab_man:
            entrada_manual = st.text_input("💳 Digite el código MIN-CARD:", key="main_man").strip()
            if entrada_manual:
                nuevo_qr_escaneado = entrada_manual

        if nuevo_qr_escaneado:
            id_extraido = nuevo_qr_escaneado.upper()
            if "MIN-CARD DIGITAL" in nuevo_qr_escaneado:
                match_mincard = re.search(r"MIN-CARD:\s*([A-Z0-9-]+)", nuevo_qr_escaneado, re.IGNORECASE)
                if match_mincard:
                    id_extraido = match_mincard.group(1).upper()
            
            st.session_state.checkpoint_emp_id = id_extraido

    # =========================================================================
    # --- PANEL DERECHO: RESULTADOS Y REGLAS ESTRICTAS DE NEGOCIO ---
    # =========================================================================
    with col_der:
        if st.session_state.checkpoint_emp_id:
            emp_id = st.session_state.checkpoint_emp_id
            st.markdown("### 🖥️ Panel Operativo")
            
            # --- CONSULTA DEL EMPLEADO ---
            query_emp = '''
                SELECT e.idempleado, e.uid_tarjeta, e.nombre, e.activo,
                       a.nombre as area_comun, a.es_restringida as comun_es_rest,
                       COALESCE(ar.nombre, 'Ninguna') as area_restringida, 
                       COALESCE(ar.es_restringida, 0) as asignada_es_rest
                FROM empleados e 
                LEFT JOIN areas a ON e.area_id = a.id 
                LEFT JOIN areas ar ON e.area_restringida_id = ar.id
                WHERE e.uid_tarjeta = ?
            '''
            df_emp = ejecutar_query(query_emp, (emp_id,), retornar_datos=True)
            
            if df_emp is not None and not df_emp.empty:
                emp = df_emp.iloc[0]
                
                if emp['activo'] == 0:
                    st.error(f"🔴 **BLOQUEADO:** El trabajador {emp['nombre']} está INACTIVO.")
                    if st.button("❌ Cerrar Perfil"):
                        st.session_state.checkpoint_emp_id = None
                        st.rerun()
                    return

                # --- CABECERA ---
                st.markdown(f"#### 👤 {emp['nombre']}")
                st.caption(f"**ID Sistema:** {emp['idempleado']} | **MIN-CARD:** {emp_id} | **Área Asignada:** {emp['area_comun']}")
                
                # =====================================================================
                # --- VALIDACIÓN DE ZONAS (HARD BLOCK) ---
                # =====================================================================
                es_valido = False
                df_zona_control = ejecutar_query("SELECT es_restringida FROM areas WHERE nombre = ?", (zona_actual,), retornar_datos=True)
                zona_es_restringida = df_zona_control.iloc[0]['es_restringida'] if (df_zona_control is not None and not df_zona_control.empty) else 0

                # Lista de nombres que NO cuentan como autorización real
                nombres_invalidos = ["ninguna", "áreas no autorizadas", "areas no autorizadas", "no autorizada"]

                if zona_actual == emp['area_comun']:
                    es_valido = True
                    mensaje_zona = f"Autorizado (Área común asignada)."
                elif zona_actual == emp['area_restringida'] and str(zona_actual).strip().lower() not in nombres_invalidos:
                    es_valido = True
                    mensaje_zona = f"Acceso especial autorizado a Zona Restringida: {zona_actual}."
                elif zona_es_restringida == 1:
                    es_valido = False
                    mensaje_zona = f"DENEGADO. No tiene permiso para ingresar a la zona restringida: {zona_actual}."
                else:
                    es_valido = True
                    mensaje_zona = f"Autorizado (Tránsito libre por zona común)."

                # LÍNEA CORPORATIVA
                prefijo = emp_id[0] if emp_id else "B"
                colores = {"AM": "#ca8a04", "A": "#2563eb", "V": "#10b981", "G": "#64748b", "M": "#92400e", "R": "#ef4444", "B": "#cbd5e1"}
                st.markdown(f"<div style='background-color:{colores.get(prefijo, '#111111')}; width:100%; height:8px; border-radius:5px; margin-bottom:15px;'></div>", unsafe_allow_html=True)
                
                # --- SI EL ACCESO ESTÁ DENEGADO POR ZONA (BLOQUEO TOTAL) ---
                if not es_valido:
                    st.error(f"🔴 **ALERTA DE SEGURIDAD:** {mensaje_zona}")
                    st.warning("⛔ **PROCESO BLOQUEADO:** El trabajador no está autorizado en este Punto de Control. No se pueden registrar tiempos ni tareas.")
                    
                    st.divider()
                    if st.button("🚪 Cerrar Perfil (Rechazado)", use_container_width=True):
                        st.session_state.checkpoint_emp_id = None
                        st.rerun()
                
                # --- SI EL ACCESO ESTÁ PERMITIDO (MUESTRA LOS BOTONES) ---
                else:
                    st.info(f"🟢 **ZONA CORRECTA:** {mensaje_zona}")

                    # --- OBTENER ESTADO ACTUAL (ENTRADA/SALIDA DEL DÍA) ---
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                    query_historial = '''
                        SELECT resultado, datetime(fecha_hora, 'localtime') as fecha_hora, motivo 
                        FROM historial_accesos 
                        WHERE empleado_uid = ? AND date(fecha_hora, 'localtime') = date('now', 'localtime') 
                        ORDER BY id ASC
                    '''
                    df_historial = ejecutar_query(query_historial, (emp_id,), retornar_datos=True)
                    
                    ya_entro = False
                    ya_salio = False
                    
                    if df_historial is not None and not df_historial.empty:
                        if any("PERMITIDO (Entrada)" in str(res) for res in df_historial['resultado']):
                            ya_entro = True
                        if any("PERMITIDO (Salida)" in str(res) for res in df_historial['resultado']):
                            ya_salio = True

                    # Tareas pendientes
                    df_tareas = ejecutar_query("SELECT o.id, o.nombre, eo.estado FROM empleado_operaciones eo JOIN operaciones o ON eo.operacion_id = o.id WHERE eo.empleado_uid = ?", (emp_id,), retornar_datos=True)
                    tareas_pendientes = len(df_tareas[df_tareas['estado'] == 'Pendiente']) if df_tareas is not None and not df_tareas.empty else 0

                    # --- BOTONES INTELIGENTES ---
                    c_ent, c_sal = st.columns(2)
                    
                    with c_ent:
                        if st.button("🟢 Registrar ENTRADA", use_container_width=True):
                            if ya_salio:
                                st.error("❌ Jornada finalizada. Ya se registró una salida completa el día de hoy.")
                            elif ya_entro:
                                st.warning("⚠️ Ya existe una ENTRADA registrada para hoy. No puede volver a ingresar.")
                            else:
                                registrar_intento_acceso(emp_id, emp_id, zona_actual, "PERMITIDO (Entrada)", f"Entrada Exitosa - {zona_actual}")
                                st.success("✅ Entrada registrada exitosamente.")
                                st.rerun()

                    with c_sal:
                        if st.button("🔴 Registrar SALIDA", use_container_width=True):
                            if ya_salio:
                                st.warning("⚠️ Ya se registró la SALIDA de este trabajador el día de hoy.")
                            elif not ya_entro:
                                st.error("❌ Bloqueo: No puede registrar una SALIDA sin haber registrado una ENTRADA el día de hoy.")
                            elif tareas_pendientes > 0:
                                msg_bloqueo = f"Bloqueo de Salida: {tareas_pendientes} tarea(s) 'Pendiente(s)'."
                                registrar_intento_acceso(emp_id, emp_id, zona_actual, "DENEGADO (Salida)", msg_bloqueo)
                                st.error(f"❌ {msg_bloqueo} Actualícelas antes de salir.")
                            else:
                                registrar_intento_acceso(emp_id, emp_id, zona_actual, "PERMITIDO (Salida)", "Salida completada. Jornada Cerrada.")
                                st.success("✅ Salida registrada con éxito.")
                                st.rerun()

                    # --- HISTORIAL FIJO DEL DÍA ---
                    st.markdown("**🕒 Control de Asistencia (Hoy):**")
                    
                    df_historial_fresco = ejecutar_query(query_historial, (emp_id,), retornar_datos=True)
                    
                    if df_historial_fresco is not None and not df_historial_fresco.empty:
                        for _, row in df_historial_fresco.iterrows():
                            if "PERMITIDO" in row['resultado']:
                                hora_sola = str(row['fecha_hora']).split(" ")[1] if " " in str(row['fecha_hora']) else str(row['fecha_hora'])
                                tipo = "Entrada" if "Entrada" in row['resultado'] else "Salida"
                                color = "green" if tipo == "Entrada" else "red"
                                st.markdown(f"- <span style='color:{color};'><b>{tipo} Registrada</b></span> a las <b>{hora_sola}</b>", unsafe_allow_html=True)
                    else:
                        st.caption("Aún no hay ingresos válidos hoy.")

                    # --- TABLA DE TAREAS OPERATIVAS ---
                    st.divider()
                    st.markdown("##### 📋 Tareas del Día")
                    
                    if df_tareas is not None and not df_tareas.empty:
                        c1, c2, c3 = st.columns([2.5, 1.5, 1.5])
                        c1.markdown("**Actividad**")
                        c2.markdown("**Estado**")
                        c3.markdown("**Acción**")
                        st.markdown("<hr style='margin: 0px; border-color: gray;'>", unsafe_allow_html=True)
                        
                        for _, row in df_tareas.iterrows():
                            c1, c2, c3 = st.columns([2.5, 1.5, 1.5])
                            c1.write(f"🔧 {row['nombre']}")
                            
                            if row['estado'] == 'Terminado':
                                c2.markdown("✅ **Terminado**")
                                c3.write("✔️")
                            elif row['estado'] == 'No Terminado':
                                c2.markdown("❌ **No Terminado**")
                                c3.write("✖️")
                            else:
                                c2.markdown("⏳ *Pendiente*")
                                b1, b2 = c3.columns(2)
                                if b1.button("✅", key=f"btn_done_{row['id']}", help="Marcar como Terminado"):
                                    modal_actualizar_tarea(emp_id, row['id'], row['nombre'], "Terminado")
                                if b2.button("❌", key=f"btn_not_{row['id']}", help="Marcar como No Terminado"):
                                    modal_actualizar_tarea(emp_id, row['id'], row['nombre'], "No Terminado")
                    else:
                        st.info("No se encontraron tareas asignadas en la jornada actual.")
                        
                    st.divider()
                    if st.button("🚪 Cerrar Perfil del Trabajador", use_container_width=True):
                        st.session_state.checkpoint_emp_id = None
                        st.rerun()

            else:
                st.error(f"❌ La tarjeta '{emp_id}' no está vinculada a ningún empleado en el sistema.")
                if st.button("Limpiar Búsqueda"):
                    st.session_state.checkpoint_emp_id = None
                    st.rerun()
        else:
            st.info("Esperando lectura de credencial...")