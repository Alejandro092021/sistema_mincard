import sqlite3
import os
import pandas as pd

def conectar_db():
    return sqlite3.connect('mincard.db')

def inicializar_sistema():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Tabla Áreas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            es_restringida INTEGER DEFAULT 0
        )
    ''')
    
    # 2. Tabla Turnos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL
        )
    ''')
    
    # 3. Tabla Maquinarias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            codigo_interno TEXT NOT NULL UNIQUE
        )
    ''')

    # 4. Tabla Operaciones (Catálogo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    ''')
    
    # 5. Tabla Empleados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            uid_tarjeta TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            turno_id INTEGER,
            area_id INTEGER,
            maquinaria_id INTEGER,
            FOREIGN KEY(turno_id) REFERENCES turnos(id),
            FOREIGN KEY(area_id) REFERENCES areas(id),
            FOREIGN KEY(maquinaria_id) REFERENCES maquinarias(id)
        )
    ''')

    # 6. Tabla intermedia para asignar Tareas/Operaciones del día a cada empleado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleado_operaciones (
            empleado_uid TEXT,
            operacion_id INTEGER,
            estado TEXT DEFAULT 'Pendiente', -- 'Realizada' o 'Pendiente'
            PRIMARY KEY (empleado_uid, operacion_id),
            FOREIGN KEY(empleado_uid) REFERENCES empleados(uid_tarjeta) ON DELETE CASCADE,
            FOREIGN KEY(operacion_id) REFERENCES operaciones(id) ON DELETE CASCADE
        )
    ''')
    
    # 7. Tabla Maestra de Perfiles MIN-CARD (Datos del Excel)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfiles_mincard (
            codigo TEXT PRIMARY KEY,       
            color TEXT,                     
            cargo TEXT NOT NULL,            
            area TEXT,                      
            equipo TEXT,                    
            maquinaria TEXT,                
            funcion TEXT,                   
            acceso TEXT,                    
            restriccion TEXT                
        )
    ''')

    # 8. Tabla de Historial de Accesos (Auditoría de validaciones)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_uid TEXT,
            min_card_codigo TEXT,
            zona_intentada TEXT NOT NULL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resultado TEXT NOT NULL,         
            motivo TEXT
        )
    ''')
    
    # =========================================================================
    # MEJORA: PRECARGA AUTOMÁTICA DE DATOS DESDE EL CSV MAESTRO
    # =========================================================================
    cursor.execute("SELECT COUNT(*) FROM perfiles_mincard")
    if cursor.fetchone()[0] == 0:
        csv_path = "MINCAR.xlsx - MINCARD_COMPLETO.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    codigo = str(row['MIN-CARD']).strip() if pd.notna(row['MIN-CARD']) else None
                    if codigo:
                        cursor.execute('''
                            INSERT OR IGNORE INTO perfiles_mincard 
                            (codigo, color, cargo, area, equipo, maquinaria, funcion, acceso, restriccion)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            codigo,
                            str(row['Color']).strip() if pd.notna(row['Color']) else None,
                            str(row['Cargo']).strip() if pd.notna(row['Cargo']) else "Sin Cargo",
                            str(row['Área']).strip() if pd.notna(row['Área']) else None,
                            str(row['Equipo']).strip() if pd.notna(row['Equipo']) else None,
                            str(row['Maquinaria']).strip() if pd.notna(row['Maquinaria']) else None,
                            str(row['Función']).strip() if pd.notna(row['Función']) else None,
                            str(row['Acceso']).strip() if pd.notna(row['Acceso']) else None,
                            str(row['Restricción']).strip() if pd.notna(row['Restricción']) else None
                        ))
                print("🟢 Base de datos sincronizada: Se han cargado los perfiles maestros con éxito.")
            except Exception as e:
                print(f"⚠️ Error al migrar datos iniciales: {e}")
    # =========================================================================

    conn.commit()
    conn.close()

# --- FUNCIONES HELPER PARA EL SISTEMA ---

def registrar_intento_acceso(empleado_uid, min_card_codigo, zona, resultado, motivo):
    """Guarda en la base de datos cada escaneo realizado."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historial_accesos (empleado_uid, min_card_codigo, zona_intentada, resultado, motivo)
        VALUES (?, ?, ?, ?, ?)
    ''', (empleado_uid, min_card_codigo, zona, resultado, motivo))
    conn.commit()
    conn.close()

def obtener_perfil_mincard(codigo):
    """Busca un perfil MIN-CARD directamente en la base de datos y lo devuelve como diccionario."""
    conn = conectar_db()
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM perfiles_mincard WHERE codigo = ?", (codigo,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

if __name__ == "__main__":
    inicializar_sistema()