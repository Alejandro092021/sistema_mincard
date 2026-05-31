import streamlit as st

def validar_acceso_minero(perfil_excel, zona_a_ingresar):
    """
    perfil_excel: Diccionario o fila de Pandas con los datos del código (Ej: M-01)
    zona_a_ingresar: String con la zona donde está el punto de control (Ej: 'Polvorín')
    """
    # Limpiar y estandarizar los textos para evitar errores por mayúsculas o espacios
    accesos_permitidos = [a.strip().lower() for a in str(perfil_excel.get('Acceso', '')).split(',')]
    restricciones = [r.strip().lower() for r in str(perfil_excel.get('Restricción', '')).split(',')]
    zona = zona_a_ingresar.strip().lower()
    
    # 1. Validar restricción explícita primero
    for restriccion in restricciones:
        if zona in restriccion or "sin autorización" in restriccion:
            if f"{zona} sin autorización" in restricciones or zona in restricciones:
                return False, f"Acceso Denegado: El perfil cuenta con restricción explícita para ingresar a {zona_a_ingresar}."
                
    # 2. Validar accesos globales de seguridad (como SSO V-02 que accede a 'Toda operación')
    if "toda operación" in accesos_permitidos or "toda operacion" in accesos_permitidos:
        return True, "Acceso Autorizado: Perfil con acceso global de supervisión."
        
    # 3. Validar acceso estándar asignado
    if zona in accesos_permitidos or "operaciones mineras" in accesos_permitidos:
        return True, "Acceso Autorizado."
        
    # 4. Si no cumple nada, por defecto se deniega por seguridad
    return False, f"Acceso Denegado: La zona {zona_a_ingresar} no está asignada a las funciones de este perfil."