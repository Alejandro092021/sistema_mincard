import streamlit as st
import pandas as pd
import qrcode
import base64
from io import BytesIO
from config.database import conectar_db

def ejecutar_query(query, params=(), retornar_datos=False):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(query, params)
        if retornar_datos:
            datos = cursor.fetchall()
            columnas = [col[0] for col in cursor.description]
            return pd.DataFrame(datos, columns=columnas)
        conn.commit()
    except Exception as e:
        st.error(f"Error en la base de datos: {e}")
    finally:
        conn.close()

def inicializar_estructura_db():
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE empleados ADD COLUMN area_restringida_id INTEGER DEFAULT 0;")
        conn.commit()
    except Exception:
        pass 
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cargos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                activo INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

# --- MODAL: MUESTRA DATOS DE LA MIN-CARD Y PERMITE IMPRESIÓN/PDF ---
@st.dialog("🪪 Vista de MIN-CARD Profesional")
def mostrar_modal_qr(empleado_datos):
    st.markdown('<div id="min-card-print">', unsafe_allow_html=True)
    st.write(f"### Trabajador: {empleado_datos['Nombre']}")
    
    col_info, col_qr = st.columns([1.2, 1])
    tareas = empleado_datos['Tareas Asignadas'] if empleado_datos['Tareas Asignadas'] else 'Sin tareas asignadas'
    area_restringida = empleado_datos['Área Restringida']
    tiene_restriccion = area_restringida and area_restringida != "Ninguna"
    
    with col_info:
        st.markdown(f"**Código MIN-CARD:** `{empleado_datos['MIN-CARD']}`")
        st.markdown(f"**Turno:** {empleado_datos['Turno']}")
        st.markdown(f"**Área Común:** {empleado_datos['Área']}")
        if tiene_restriccion:
            st.markdown(f"⚠️ **Acceso NO Autorizado:** <span style='color:#ff4b4b; font-weight:bold;'>{area_restringida} (ZONA RESTRINGIDA)</span>", unsafe_allow_html=True)
        st.markdown(f"**Equipo Operando:** {empleado_datos['Equipo']}")
        st.markdown(f"**Funciones:**\n_{tareas}_\n")
    
    with col_qr:
        linea_restriccion = f"Zona Restringida: {area_restringida}\n" if tiene_restriccion else ""
        datos_para_qr = (
            f"=== MIN-CARD DIGITAL ===\n"
            f"ID: {empleado_datos['MIN-CARD']}\n"
            f"Trabajador: {empleado_datos['Nombre']}\n"
            f"Turno: {empleado_datos['Turno']}\n"
            f"Area Comun: {empleado_datos['Área']}\n"
            f"{linea_restriccion}"
            f"Equipo: {empleado_datos['Equipo']}\n"
            f"Tareas: {tareas}"
        )
        
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
        qr.add_data(datos_para_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img_qr.save(buf, format="PNG")
        byte_im = buf.getvalue()
        qr_base64 = base64.b64encode(byte_im).decode("utf-8")
        st.image(byte_im, caption="Escanea para verificar accesos", use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    html_impresion = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 25px; background-color: #ffffff; color: #000000; }}
            .card {{ border: 3px solid #111111; padding: 25px; border-radius: 12px; width: 460px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 2px solid #111; padding-bottom: 6px; text-align: center; }}
            .alert {{ color: #d32f2f; font-weight: bold; margin-top: 12px; border: 1px solid #d32f2f; padding: 6px; border-radius: 4px; background-color: #ffebee; }}
            .qr-container {{ text-align: center; margin-top: 20px; margin-bottom: 15px; }}
            .qr-image {{ width: 180px; height: 180px; border: 1px solid #ccc; padding: 5px; border-radius: 4px; }}
            .footer-note {{ font-size: 11px; color: #555555; text-align: center; margin-top: 20px; line-height: 1.4; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="card">
            <div class="title">🪪 REPORTE MIN-CARD CREDENCIAL</div>
            <p><strong>Trabajador:</strong> {empleado_datos['Nombre']}</p>
            <p><strong>Código ID / Tarjeta:</strong> {empleado_datos['MIN-CARD']}</p>
            <p><strong>Turno Asignado:</strong> {empleado_datos['Turno']}</p>
            <p><strong>Área de Trabajo Común:</strong> {empleado_datos['Área']}</p>
            {"<div class='alert'>⚠️ ACCESO NO AUTORIZADO A: " + area_restringida + " (ZONA RESTRINGIDA)</div>" if tiene_restriccion else ""}
            <p><strong>Maquinaria/Equipo:</strong> {empleado_datos['Equipo']}</p>
            <p><strong>Operaciones del Día:</strong> {tareas}</p>
            <div class="qr-container">
                <img class="qr-image" src="data:image/png;base64,{qr_base64}" alt="Código QR MIN-CARD">
                <div style="font-size: 12px; margin-top: 5px; color: #333;">Escanea para verificar accesos</div>
            </div>
            <div class="footer-note">
                Documento generado correctamente.<br>Use el menú del sistema para <strong>Guardar como PDF</strong> o enviar a su impresora.
            </div>
        </div>
    </body>
    </html>
    """
    
    st.download_button(
        label="💾 Guardar como PDF / Imprimir",
        data=html_impresion,
        file_name=f"MIN_CARD_{empleado_datos['MIN-CARD']}.html",
        mime="text/html",
        use_container_width=True,
        help="Descarga el formato limpio para impresión rápida nativa."
    )

# --- FUNCIÓN CENTRAL DE RENDERIZADO DEL PANEL ---
def render_admin():
    if "editing_uid" not in st.session_state:
        st.session_state.editing_uid = None

    inicializar_estructura_db()
    st.subheader("⚙️ Panel de Configuración Inicial (CRUD)")
    
    tab_emp, tab_are, tab_tur, tab_maq, tab_car, tab_ope = st.tabs([
        "👤 Personal y MIN-CARD", "📍 Áreas", "⏰ Turnos", "🚜 Maquinaria", "🪪 Cargos", "🔧 Catálogo de Tareas"
    ])
    
    # =========================================================================
    # --- PESTAÑA ÁREAS ---
    # =========================================================================
    with tab_are:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.markdown("##### 📝 Registrar Nueva Área")
            with st.form("f_areas", clear_on_submit=True):
                nom = st.text_input("Nombre del Área/Zona")
                rest = st.checkbox("¿Es zona restringida?")
                if st.form_submit_button("Registrar Área") and nom:
                    ejecutar_query("INSERT INTO areas (nombre, es_restringida, activo) VALUES (?, ?, 1) ON CONFLICT(nombre) DO UPDATE SET activo=1, es_restringida=?", (nom.strip(), 1 if rest else 0, 1 if rest else 0))
                    st.success("Área guardada con éxito."); st.rerun()
                    
        with col_der:
            st.markdown("##### ✏️ Modificar / Desactivar Área")
            df_as = ejecutar_query("SELECT id, nombre, es_restringida FROM areas WHERE activo = 1", retornar_datos=True)
            if df_as is not None and not df_as.empty:
                dict_as = {row['nombre']: row['id'] for _, row in df_as.iterrows()}
                area_sel = st.selectbox("Selecciona Área a gestionar:", list(dict_as.keys()), key="sb_areas")
                idx_row = df_as[df_as['id'] == dict_as[area_sel]].iloc[0]
                
                with st.form("f_edit_area"):
                    new_nom = st.text_input("Nombre de la Zona", value=idx_row['nombre'])
                    new_rest = st.checkbox("¿Es restringida?", value=bool(idx_row['es_restringida']))
                    b_save, b_del = st.columns(2)
                    if b_save.form_submit_button("💾 Guardar"):
                        ejecutar_query("UPDATE areas SET nombre=?, es_restringida=? WHERE id=?", (new_nom.strip(), 1 if new_rest else 0, dict_as[area_sel]))
                        st.success("Cambios aplicados."); st.rerun()
                    if b_del.form_submit_button("🗑️ Desactivar"):
                        ejecutar_query("UPDATE areas SET activo=0 WHERE id=?", (dict_as[area_sel],))
                        st.warning("Área desactivada del sistema."); st.rerun()
            else:
                st.info("No existen áreas activas para modificar.")
                
        st.markdown("---")
        df_view = ejecutar_query("SELECT id as 'ID', nombre as 'Área / Zona', case es_restringida when 1 then 'SÍ' else 'NO' end as 'Restringida' FROM areas WHERE activo=1", retornar_datos=True)
        if df_view is not None and not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)

    # =========================================================================
    # --- PESTAÑA TURNOS ---
    # =========================================================================
    with tab_tur:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.markdown("##### 📝 Registrar Nuevo Turno")
            with st.form("f_turnos", clear_on_submit=True):
                nom_t = st.text_input("Turno (Ej: Mañana)")
                ini = st.text_input("Inicio (HH:MM)")
                fin = st.text_input("Fin (HH:MM)")
                if st.form_submit_button("Registrar Turno") and nom_t:
                    ejecutar_query("INSERT INTO turnos (nombre, hora_inicio, hora_fin, activo) VALUES (?, ?, ?, 1) ON CONFLICT(nombre) DO UPDATE SET activo=1, hora_inicio=?, hora_fin=?", (nom_t.strip(), ini, fin, ini, fin))
                    st.success("Turno guardado."); st.rerun()
                    
        with col_der:
            st.markdown("##### ✏️ Modificar / Desactivar Turno")
            df_ts = ejecutar_query("SELECT id, nombre, hora_inicio, hora_fin FROM turnos WHERE activo = 1", retornar_datos=True)
            if df_ts is not None and not df_ts.empty:
                dict_ts = {row['nombre']: row['id'] for _, row in df_ts.iterrows()}
                turno_sel = st.selectbox("Selecciona Turno a gestionar:", list(dict_ts.keys()), key="sb_turnos")
                idx_row = df_ts[df_ts['id'] == dict_ts[turno_sel]].iloc[0]
                
                with st.form("f_edit_turno"):
                    new_nom = st.text_input("Nombre del Turno", value=idx_row['nombre'])
                    new_ini = st.text_input("Hora Inicio", value=idx_row['hora_inicio'])
                    new_fin = st.text_input("Hora Fin", value=idx_row['hora_fin'])
                    b_save, b_del = st.columns(2)
                    if b_save.form_submit_button("💾 Guardar"):
                        ejecutar_query("UPDATE turnos SET nombre=?, hora_inicio=?, hora_fin=? WHERE id=?", (new_nom.strip(), new_ini, new_fin, dict_ts[turno_sel]))
                        st.success("Turno modificado."); st.rerun()
                    if b_del.form_submit_button("🗑️ Desactivar"):
                        ejecutar_query("UPDATE turnos SET activo=0 WHERE id=?", (dict_ts[turno_sel],))
                        st.warning("Turno inactivado."); st.rerun()
            else:
                st.info("No existen turnos activos.")
                
        st.markdown("---")
        df_view = ejecutar_query("SELECT id as 'ID', nombre as 'Turno', hora_inicio as 'Hora Inicio', hora_fin as 'Hora Fin' FROM turnos WHERE activo=1", retornar_datos=True)
        if df_view is not None and not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)

    # =========================================================================
    # --- PESTAÑA MAQUINARIA ---
    # =========================================================================
    with tab_maq:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.markdown("##### 📝 Registrar Equipo")
            with st.form("f_maq", clear_on_submit=True):
                mod = st.text_input("Modelo del Equipo")
                cod = st.text_input("Código Interno")
                if st.form_submit_button("Registrar Equipo") and mod:
                    ejecutar_query("INSERT INTO maquinarias (modelo, codigo_interno, activo) VALUES (?, ?, 1) ON CONFLICT(codigo_interno) DO UPDATE SET activo=1, modelo=?", (mod.strip(), cod.strip(), mod.strip()))
                    st.success("Equipo registrado."); st.rerun()
                    
        with col_der:
            st.markdown("##### ✏️ Modificar / Desactivar Equipo")
            df_ms = ejecutar_query("SELECT id, modelo, codigo_interno FROM maquinarias WHERE activo = 1", retornar_datos=True)
            if df_ms is not None and not df_ms.empty:
                dict_ms = {f"{row['modelo']} ({row['codigo_interno']})": row['id'] for _, row in df_ms.iterrows()}
                maq_sel = st.selectbox("Selecciona Equipo:", list(dict_ms.keys()), key="sb_maq")
                idx_row = df_ms[df_ms['id'] == dict_ms[maq_sel]].iloc[0]
                
                with st.form("f_edit_maq"):
                    new_mod = st.text_input("Modelo", value=idx_row['modelo'])
                    new_cod = st.text_input("Código Interno (Único)", value=idx_row['codigo_interno'])
                    b_save, b_del = st.columns(2)
                    if b_save.form_submit_button("💾 Guardar"):
                        ejecutar_query("UPDATE maquinarias SET modelo=?, codigo_interno=? WHERE id=?", (new_mod.strip(), new_cod.strip(), dict_ms[maq_sel]))
                        st.success("Equipo actualizado."); st.rerun()
                    if b_del.form_submit_button("🗑️ Desactivar"):
                        ejecutar_query("UPDATE maquinarias SET activo=0 WHERE id=?", (dict_ms[maq_sel],))
                        st.warning("Equipo archivado."); st.rerun()
            else:
                st.info("No hay maquinarias activas.")
                
        st.markdown("---")
        df_view = ejecutar_query("SELECT id as 'ID', modelo as 'Modelo Equipo', codigo_interno as 'Código de Control' FROM maquinarias WHERE activo=1", retornar_datos=True)
        if df_view is not None and not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)

    # =========================================================================
    # --- PESTAÑA CARGOS ---
    # =========================================================================
    with tab_car:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.markdown("##### 📝 Registrar Cargo")
            with st.form("f_cargo", clear_on_submit=True):
                nom_c = st.text_input("Nombre del Cargo Operativo")
                if st.form_submit_button("Registrar Cargo") and nom_c:
                    ejecutar_query("INSERT INTO cargos (nombre, activo) VALUES (?, 1) ON CONFLICT(nombre) DO UPDATE SET activo=1", (nom_c.strip(),))
                    st.success("Cargo añadido."); st.rerun()
                    
        with col_der:
            st.markdown("##### ✏️ Modificar / Desactivar Cargo")
            df_cs = ejecutar_query("SELECT id, nombre FROM cargos WHERE activo = 1", retornar_datos=True)
            if df_cs is not None and not df_cs.empty:
                dict_cs = {row['nombre']: row['id'] for _, row in df_cs.iterrows()}
                car_sel = st.selectbox("Selecciona Cargo:", list(dict_cs.keys()), key="sb_cargos")
                
                with st.form("f_edit_cargo"):
                    new_car = st.text_input("Nombre del Cargo", value=car_sel)
                    b_save, b_del = st.columns(2)
                    if b_save.form_submit_button("💾 Guardar"):
                        ejecutar_query("UPDATE cargos SET nombre=? WHERE id=?", (new_car.strip(), dict_cs[car_sel]))
                        st.success("Cargo actualizado."); st.rerun()
                    if b_del.form_submit_button("🗑️ Desactivar"):
                        ejecutar_query("UPDATE cargos SET activo=0 WHERE id=?", (dict_cs[car_sel],))
                        st.warning("Cargo retirado del catálogo."); st.rerun()
            else:
                st.info("No hay cargos operativos activos.")
                
        st.markdown("---")
        df_view = ejecutar_query("SELECT id as 'ID', nombre as 'Cargo Operativo' FROM cargos WHERE activo=1", retornar_datos=True)
        if df_view is not None and not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)

    # =========================================================================
    # --- PESTAÑA CATÁLOGO DE TAREAS ---
    # =========================================================================
    with tab_ope:
        col_izq, col_der = st.columns(2)
        with col_izq:
            st.markdown("##### 📝 Registrar Actividad")
            with st.form("f_ope", clear_on_submit=True):
                ope = st.text_input("Nueva Tarea/Actividad General")
                if st.form_submit_button("Registrar Tarea") and ope:
                    ejecutar_query("INSERT INTO operaciones (nombre, activo) VALUES (?, 1) ON CONFLICT(nombre) DO UPDATE SET activo=1", (ope.strip(),))
                    st.success("Tarea añadida."); st.rerun()
                    
        with col_der:
            st.markdown("##### ✏️ Modificar / Desactivar Tarea")
            df_ops = ejecutar_query("SELECT id, nombre FROM operaciones WHERE activo = 1", retornar_datos=True)
            if df_ops is not None and not df_ops.empty:
                dict_ops = {row['nombre']: row['id'] for _, row in df_ops.iterrows()}
                ope_sel = st.selectbox("Selecciona Tarea:", list(dict_ops.keys()), key="sb_operaciones")
                
                with st.form("f_edit_ope"):
                    new_ope = st.text_input("Nombre de la Actividad", value=ope_sel)
                    b_save, b_del = st.columns(2)
                    if b_save.form_submit_button("💾 Guardar"):
                        ejecutar_query("UPDATE operaciones SET nombre=? WHERE id=?", (new_ope.strip(), dict_ops[ope_sel]))
                        st.success("Actividad actualizada."); st.rerun()
                    if b_del.form_submit_button("🗑️ Desactivar"):
                        ejecutar_query("UPDATE operaciones SET activo=0 WHERE id=?", (dict_ops[ope_sel],))
                        st.warning("Actividad desactivada."); st.rerun()
            else:
                st.info("No hay tareas registradas activas.")
                
        st.markdown("---")
        df_view = ejecutar_query("SELECT id as 'ID', nombre as 'Tarea / Actividad' FROM operaciones WHERE activo=1", retornar_datos=True)
        if df_view is not None and not df_view.empty:
            st.dataframe(df_view, use_container_width=True, hide_index=True)

    # =========================================================================
    # --- PESTAÑA PERSONAL (FORMULARIOS DINÁMICOS CON FILTRADO ACTIVO) ---
    # =========================================================================
    with tab_emp:
        # MEJORA CRÍTICA: Filtramos usando WHERE activo = 1 para que lo desactivado no aparezca aquí
        areas_comunes = ejecutar_query("SELECT id, nombre FROM areas WHERE es_restringida = 0 AND activo = 1", retornar_datos=True)
        areas_restringidas = ejecutar_query("SELECT id, nombre FROM areas WHERE es_restringida = 1 AND activo = 1", retornar_datos=True)
        turnos = ejecutar_query("SELECT id, nombre FROM turnos WHERE activo = 1", retornar_datos=True)
        maquinas = ejecutar_query("SELECT id, codigo_interno FROM maquinarias WHERE activo = 1", retornar_datos=True)
        operaciones = ejecutar_query("SELECT id, nombre FROM operaciones WHERE activo = 1", retornar_datos=True)
        
        if (areas_comunes is None or areas_comunes.empty) or (turnos is None or turnos.empty) or (maquinas is None or maquinas.empty):
            st.warning("⚠️ Asegúrate de tener registrado al menos un Área Común, un Turno y una Maquinaria ACTIVA antes de emitir tarjetas.")
        else:
            col1, col2 = st.columns([1, 1])
            opciones_rest_ids = [0] + (areas_restringidas['id'].tolist() if areas_restringidas is not None and not areas_restringidas.empty else [])
            
            def mapear_area_restringida(x):
                if x == 0: return "Ninguna"
                return areas_restringidas[areas_restringidas['id'] == x]['nombre'].values[0]

            with col1:
                st.markdown("### 📝 Registrar Nuevo Trabajador")
                with st.form("f_emp", clear_on_submit=True):
                    uid = st.text_input("Código MIN-CARD (ID Único)")
                    nombre = st.text_input("Nombre completo")
                    a_sel = st.selectbox("Asignar Área Común", options=areas_comunes['id'].tolist(), format_func=lambda x: areas_comunes[areas_comunes['id']==x]['nombre'].values[0])
                    a_rest_sel = st.selectbox("Asignar Área Restringida (Opcional)", options=opciones_rest_ids, format_func=mapear_area_restringida)
                    t_sel = st.selectbox("Asignar Turno", options=turnos['id'].tolist(), format_func=lambda x: turnos[turnos['id']==x]['nombre'].values[0])
                    m_sel = st.selectbox("Asignar Maquinaria", options=maquinas['id'].tolist(), format_func=lambda x: maquinas[maquinas['id']==x]['codigo_interno'].values[0])
                    
                    ops_seleccionadas = st.multiselect(
                        "Asignar Tareas del Día", 
                        options=operaciones['id'].tolist() if operaciones is not None and not operaciones.empty else [],
                        format_func=lambda x: operaciones[operaciones['id']==x]['nombre'].values[0]
                    )
                    
                    if st.form_submit_button("Emitir MIN-CARD") and uid and nombre:
                        # Guardamos con activo = 1 por defecto
                        ejecutar_query("INSERT OR REPLACE INTO empleados (uid_tarjeta, nombre, turno_id, area_id, maquinaria_id, area_restringida_id, activo) VALUES (?, ?, ?, ?, ?, ?, 1)", 
                                       (uid.strip(), nombre.strip(), t_sel, a_sel, m_sel, a_rest_sel))
                        ejecutar_query("DELETE FROM empleado_operaciones WHERE empleado_uid = ?", (uid.strip(),))
                        for op_id in ops_seleccionadas:
                            ejecutar_query("INSERT INTO empleado_operaciones (empleado_uid, operacion_id) VALUES (?, ?)", (uid.strip(), op_id))
                        st.success(f"🎉 MIN-CARD {uid} emitida con éxito."); st.rerun()

            with col2:
                if st.session_state.editing_uid is not None:
                    st.markdown("### ✏️ Modificar Registro Seleccionado")
                    emp_uid = st.session_state.editing_uid
                    df_emp_data = ejecutar_query("SELECT * FROM empleados WHERE uid_tarjeta = ?", (emp_uid,), retornar_datos=True)
                    
                    if df_emp_data is not None and not df_emp_data.empty:
                        datos_emp = df_emp_data.iloc[0]
                        ops_actuales = ejecutar_query("SELECT operacion_id FROM empleado_operaciones WHERE empleado_uid = ?", (emp_uid,), retornar_datos=True)
                        lista_ops_actuales = ops_actuales['operacion_id'].tolist() if ops_actuales is not None and not ops_actuales.empty else []

                        with st.form("f_edicion"):
                            st.markdown(f"**Modificando la MIN-CARD:** `{emp_uid}`")
                            nuevo_nombre = st.text_input("Nombre Completo", value=datos_emp['nombre'])
                            
                            idx_area = areas_comunes['id'].tolist().index(datos_emp['area_id']) if datos_emp['area_id'] in areas_comunes['id'].tolist() else 0
                            val_rest_db = datos_emp['area_restringida_id'] if 'area_restringida_id' in datos_emp else 0
                            idx_area_rest = opciones_rest_ids.index(val_rest_db) if val_rest_db in opciones_rest_ids else 0
                            idx_turno = turnos['id'].tolist().index(datos_emp['turno_id']) if datos_emp['turno_id'] in turnos['id'].tolist() else 0
                            idx_maq = maquinas['id'].tolist().index(datos_emp['maquinaria_id']) if datos_emp['maquinaria_id'] in maquinas['id'].tolist() else 0

                            nuevo_a_sel = st.selectbox("Área Común", options=areas_comunes['id'].tolist(), index=idx_area, format_func=lambda x: areas_comunes[areas_comunes['id']==x]['nombre'].values[0])
                            nuevo_a_rest_sel = st.selectbox("Área Restringida", options=opciones_rest_ids, index=idx_area_rest, format_func=mapear_area_restringida)
                            nuevo_t_sel = st.selectbox("Turno", options=turnos['id'].tolist(), index=idx_turno, format_func=lambda x: turnos[turnos['id']==x]['nombre'].values[0])
                            nuevo_m_sel = st.selectbox("Maquinaria", options=maquinas['id'].tolist(), index=idx_maq, format_func=lambda x: maquinas[maquinas['id']==x]['codigo_interno'].values[0])
                            
                            nuevas_ops = st.multiselect(
                                "Tareas/Actividades del Día", 
                                options=operaciones['id'].tolist() if operaciones is not None and not operaciones.empty else [],
                                default=lista_ops_actuales,
                                format_func=lambda x: operaciones[operaciones['id']==x]['nombre'].values[0]
                            )
                            
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if st.form_submit_button("💾 Guardar Cambios"):
                                    ejecutar_query('''
                                        UPDATE empleados SET nombre=?, turno_id=?, area_id=?, maquinaria_id=?, area_restringida_id=? 
                                        WHERE uid_tarjeta=?
                                    ''', (nuevo_nombre.strip(), nuevo_t_sel, nuevo_a_sel, nuevo_m_sel, nuevo_a_rest_sel, emp_uid))
                                    ejecutar_query("DELETE FROM empleado_operaciones WHERE empleado_uid = ?", (emp_uid,))
                                    for op_id in nuevas_ops:
                                        ejecutar_query("INSERT INTO empleado_operaciones (empleado_uid, operacion_id) VALUES (?, ?)", (emp_uid, op_id))
                                    st.session_state.editing_uid = None
                                    st.success("Cambios aplicados correctamente."); st.rerun()
                            with col_b2:
                                if st.form_submit_button("❌ Cancelar"):
                                    st.session_state.editing_uid = None; st.rerun()
                    else:
                        st.session_state.editing_uid = None
                else:
                    st.markdown("### 💡 Centro de Operaciones")
                    st.info("Para gestionar la información de un trabajador, usa los botones de la tabla inferior:\n\n- Acciones visuales con el ojo (👁️).\n- Modificación interactiva con el lápiz (✏️).")

            # --- TABLA DE PERSONAL ACTIVO ---
            st.markdown("---")
            st.subheader("📋 Personal Activo en Sistema")
            
            df_lista = ejecutar_query('''
                SELECT e.uid_tarjeta as 'MIN-CARD', e.nombre as 'Nombre', t.nombre as 'Turno', a.nombre as 'Área', 
                COALESCE((SELECT ar.nombre FROM areas ar WHERE ar.id = e.area_restringida_id), 'Ninguna') as 'Área Restringida',
                m.codigo_interno as 'Equipo',
                (SELECT GROUP_CONCAT(op.nombre, ', ') FROM empleado_operaciones eo JOIN operaciones op ON eo.operacion_id = op.id WHERE eo.empleado_uid = e.uid_tarjeta) as 'Tareas Asignadas'
                FROM empleados e 
                JOIN turnos t ON e.turno_id=t.id 
                JOIN areas a ON e.area_id=a.id 
                JOIN maquinarias m ON e.maquinaria_id=m.id
                WHERE e.activo = 1
            ''', retornar_datos=True)
            
            if df_lista is not None and not df_lista.empty:
                grid_head = st.columns([1, 2, 1, 1, 1.2, 1, 2, 1.6])
                grid_head[0].markdown("**MIN-CARD**")
                grid_head[1].markdown("**Nombre**")
                grid_head[2].markdown("**Turno**")
                grid_head[3].markdown("**Área**")
                grid_head[4].markdown("**Zona Rest.**")
                grid_head[5].markdown("**Equipo**")
                grid_head[6].markdown("**Tareas**")
                grid_head[7].markdown("**Acción**")
                st.markdown("<hr style='margin: 5px 0px 15px 0px; border-color: gray;'>", unsafe_allow_html=True)
                
                for _, row in df_lista.iterrows():
                    grid_row = st.columns([1, 2, 1, 1, 1.2, 1, 2, 1.6])
                    grid_row[0].write(str(row['MIN-CARD']))
                    grid_row[1].write(row['Nombre'])
                    grid_row[2].write(row['Turno'])
                    grid_row[3].write(row['Área'])
                    grid_row[4].write(row['Área Restringida'])
                    grid_row[5].write(row['Equipo'])
                    grid_row[6].write(row['Tareas Asignadas'] if row['Tareas Asignadas'] else "Sin tareas")
                    
                    col_btn_view, col_btn_edit, col_btn_del = grid_row[7].columns(3)
                    if col_btn_view.button("👁️", key=f"view_{row['MIN-CARD']}"):
                        mostrar_modal_qr(row)
                    if col_btn_edit.button("✏️", key=f"edit_{row['MIN-CARD']}"):
                        st.session_state.editing_uid = row['MIN-CARD']; st.rerun()
                    if col_btn_del.button("🗑️", key=f"del_{row['MIN-CARD']}"):
                        # Eliminación lógica (Safe soft-delete) para no romper el historial de accesos
                        ejecutar_query("UPDATE empleados SET activo = 0 WHERE uid_tarjeta = ?", (row['MIN-CARD'],))
                        if st.session_state.editing_uid == row['MIN-CARD']:
                            st.session_state.editing_uid = None
                        st.toast(f"🗑️ Empleado inactivado: {row['Nombre']}")
                        st.rerun()
            else:
                st.info("No hay trabajadores activos registrados.")