import sqlite3

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

    # 6. NUEVA: Tabla intermedia para asignar Tareas/Operaciones del día a cada empleado
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
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    inicializar_sistema()