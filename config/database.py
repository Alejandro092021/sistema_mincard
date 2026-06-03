import sqlite3
import os
import pandas as pd

DB_NAME = "mincard.db"

def conectar_db():
    """Establece la conexión con la base de datos SQLite configurando el row_factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite mapear los resultados por nombre de columna
    return conn

def ejecutar_query(query, params=(), retornar_datos=False):
    """
    Ejecuta cualquier instrucción SQL de forma segura y centralizada.
    - Si retornar_datos es True: Devuelve un DataFrame de Pandas (ideal para tus tablas de interfaz).
    - Para inserciones/actualizaciones/eliminaciones: Devuelve True si se realizó con éxito o False si falló.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON;")  # Forzar integridad de llaves foráneas
        cursor.execute(query, params)
        
        if retornar_datos:
            datos = cursor.fetchall()
            columnas = [col[0] for col in cursor.description] if cursor.description else []
            lista_datos = [list(row) for row in datos]
            return pd.DataFrame(lista_datos, columns=columnas)
            
        conn.commit()
        return True  # Devuelve True si la operación de escritura fue exitosa
    except Exception as e:
        print(f"❌ Error en la base de datos: {e}")
        return False  # Devuelve False si hubo una violación de restricción (ej: UNIQUE constraint failed)
    finally:
        conn.close()

def inicializar_sistema():
    """Crea la base de datos y todas las tablas estructuradas desde cero."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Tabla Áreas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            es_restringida INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    # 2. Tabla Turnos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    # 3. Tabla Maquinarias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquinarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            codigo_interno TEXT NOT NULL UNIQUE,
            activo INTEGER DEFAULT 1
        )
    ''')

    # 4. Tabla Operaciones (Catálogo de Tareas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            activo INTEGER DEFAULT 1
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
            activo INTEGER DEFAULT 1,
            FOREIGN KEY(turno_id) REFERENCES turnos(id),
            FOREIGN KEY(area_id) REFERENCES areas(id),
            FOREIGN KEY(maquinaria_id) REFERENCES maquinarias(id)
        )
    ''')

    # 6. Tabla intermedia 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleado_operaciones (
            empleado_uid TEXT,
            operacion_id INTEGER,
            estado TEXT DEFAULT 'Pendiente',
            PRIMARY KEY (empleado_uid, operacion_id),
            FOREIGN KEY(empleado_uid) REFERENCES empleados(uid_tarjeta) ON DELETE CASCADE,
            FOREIGN KEY(operacion_id) REFERENCES operaciones(id) ON DELETE CASCADE
        )
    ''')
    
    # 7. Tabla Maestra de Perfiles MIN-CARD 
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

    # 8. Tabla de Historial de Accesos
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

    # 9. Tabla de Catálogo de Cargos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cargos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            activo INTEGER DEFAULT 1
        )
    ''')
    
    # =========================================================================
    # PRECARGA AUTOMÁTICA DE DATOS DESDE EL CSV MAESTRO
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

    conn.commit()
    conn.close()

# --- FUNCIONES HELPER PARA EL SISTEMA REFACTORIZADAS ---

def registrar_intento_acceso(empleado_uid, min_card_codigo, zona, resultado, motivo):
    """Registra los eventos de entrada utilizando la función centralizada."""
    query = '''
        INSERT INTO historial_accesos (empleado_uid, min_card_codigo, zona_intentada, resultado, motivo)
        VALUES (?, ?, ?, ?, ?)
    '''
    return ejecutar_query(query, (empleado_uid, min_card_codigo, zona, resultado, motivo))

def obtener_perfil_mincard(codigo):
    """Busca un perfil MIN-CARD por su código de tarjeta y lo devuelve en formato diccionario."""
    df = ejecutar_query("SELECT * FROM perfiles_mincard WHERE codigo = ?", (codigo,), retornar_datos=True)
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

if __name__ == "__main__":
    inicializar_sistema()