import time
import requests
from time import sleep
from instrucciones import client_context
from pathlib import Path
import os
from pymysql.cursors import DictCursor
from instrucciones import actualizar_status
import json
import socket
from datetime import datetime
import pytz
import pymysql

config_file= r'C:\AgentedeVozPython\config.json'
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

ip_local = socket.gethostbyname(socket.gethostname())

try:
    conn = pymysql.connect(
        host='192.168.50.13',
        user='lhernandez',
        password='lhernandez10',
        database='asterisk',
        cursorclass=DictCursor,
        connect_timeout=5,
        charset='utf8mb4'
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT alias, nombre FROM agentesDepuracion WHERE ip = %s LIMIT 1",
            (ip_local,)
        )
        row = cur.fetchone()
    conn.close()
except Exception as e:
    print(f"❌ Error al conectar a BD: {e}")
    row = None

if row:
    config['extension']     = row['alias']
    config['username']      = row['nombre']
    if row['nombre'] == "BOTo":
        config['user_password'] = "Cyberbot2024"
    print(f"✅ Datos desde BD: ext={config['extension']}, user={config['username']}")
else:
    print(f"⚠️ No encontré registro para IP {ip_local}; uso config.json")

API_BASE   = "http://192.168.50.13/agc/api.php"
SOURCE     = "test"
USER       = config['username']
PASSWORD   = config['user_password']
AGENT_USER = config['username']

def call_vicidial_tool(function: str, value: str = "1", extra_args: dict = {}) -> dict:
    params = {
        "source": SOURCE,
        "user": USER,
        "pass": PASSWORD,
        "agent_user": AGENT_USER,
        "function": function,
        "value": value,
        **extra_args
    }
    try:
        response = requests.get(API_BASE, params=params)
        toolEjecutado= f"tool: {function} ejecutado con {value} como accion"
        return {"result": response.ok}
    except Exception as e:
        return {"result": False, "error": str(e)}
    
def set_pending_tipificacion(tipificacion: str) -> None:
    """
    Guarda la tipificación pendiente para ejecutarse al cierre de sesión.
    """
    global pending_tipificacion
    pending_tipificacion = tipificacion

def execute_pending_tipificacion() -> None:
    """
    Ejecuta la tipificación pendiente (llama a external_status_*)
    y luego limpia la variable global.
    """
    global pending_cn_type, pending_cn_motivo, pending_tipificacion

    if pending_tipificacion is None:
        return

    # Mapeo de tipificaciones
    if pending_tipificacion == 'SCCAVT':
        external_status_SCCAVT()
        insertar_base_not_done_via_api()
    elif pending_tipificacion == 'SCCOVT':
        external_status_SCCOVT()
    elif pending_tipificacion == 'SCTSVT':
        external_status_SCTSVT()
    elif pending_tipificacion == 'SCMADI':
        external_status_SCMADI()
    elif pending_tipificacion == 'SCCCUE':
        external_status_SCCCUE()
    elif pending_tipificacion == 'NCBUZ':
        external_status_NCBUZ()
    elif pending_tipificacion == 'SCNUEQ':
        external_status_SCNUEQ()
    elif pending_tipificacion == 'OSCOM':
        external_status_OSCOM()
    elif pending_tipificacion == 'SIN CONTACTO':
        external_status_SCCCUE()
    elif pending_tipificacion == 'NI':
        external_status_CLMLST()
    else:
        print("⚠️ Tipificación no reconocida:", pending_tipificacion)

    # Actualizar status final en BD
    from instrucciones import actualizar_status, client_context
    actualizar_status(client_context["CUENTA"], 'Completada')

    # Limpiar la pendiente
    pending_cn_type = pending_cn_motivo = pending_tipificacion = None

def insertar_base_not_done_via_api() -> bool:
    """
    Llama al servicio InsertarBaseNotDone de DepuracionNotdone
    usando los valores en client_context.
    Devuelve True si el servicio responde OK, False en caso contrario.
    """
    ip_local = socket.gethostbyname(socket.gethostname())
    
    tz_cdmx = pytz.timezone('America/Mexico_City')
    ahora = datetime.now(tz_cdmx).strftime("%Y-%m-%d %H:%M:%S")
    
    url = "https://rpabackizzi.azurewebsites.net/DepuracionNotdone/InsertarDepuracionEXTAGENT"
    payload = {
        "lead_id":           client_context.get("lead_id"),
        "Cuenta":            client_context.get("CUENTA"),
        "Compania":          client_context.get("Compania"),
        "NumOrden":          client_context.get("NUMERO_ORDEN"),
        "Tipo":              client_context.get("Tipo"),
        "MotivoOrden":       client_context.get("MotivoOrden"),
        "Source":            "IA AGENT",
        "time_carga":        ahora,
        "Status":            "Registro pendiente",
        "usuario_creo":      config['username'],
        "User_registro":     f"{ip_local}",
        "Procesando":        "0",
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        # Si el servicio devuelve JSON con { message: "..."}:
        data = resp.json()
        print(f"✅ Inserción exitosa: {data.get('message', data)}")
        return True

    except requests.HTTPError as errh:
        print(f"❌ Error HTTP: {errh} – {resp.text}")
    except requests.ConnectionError as errc:
        print(f"❌ Error de conexión: {errc}")
    except requests.Timeout as errt:
        print(f"❌ Timeout: {errt}")
    except Exception as err:
        print(f"❌ Error inesperado: {err}")

    return False

# === TOOLS ===
# Colgar llamada
def external_hangup() -> dict: time.sleep(2); return call_vicidial_tool("external_hangup")
# retirar pausa
def external_pause(action: str) -> dict: time.sleep(1); return call_vicidial_tool("external_pause", action)
#transeferir llamada a un grupo
def transfer_conference(value="1", ingroup="SOME") -> dict: return call_vicidial_tool("transfer_conference", value, {"ingroup_choices": ingroup})
# Cliente confirma servicio
def external_status_SCCAVT() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "SCCAVT")
# Cliente confirma visita técnica por troubleshooting y/o cancela por lo mismo
def external_status_SCTSVT() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "SCTSVT")
# Falla continua
def external_status_SCCOVT() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "SCCOVT")
# Reagendar llamada
def external_status_SCMADI() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "SCMADI")
# Cliente cuelga
def external_status_SCCCUE() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "SCCCUE")
# buzon de voz
def external_status_NCBUZ() -> dict:    time.sleep(2); return call_vicidial_tool("external_status", "NCBUZ")
# nuemro equivocado
def external_status_SCNUEQ() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "SCNUEQ")

def external_status_OSCOM() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "OSCOM")

def external_status_DESCONECT() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "DESCONECT")

def external_status_CLMLST() -> dict:   time.sleep(2); return call_vicidial_tool("external_status", "CLMLST")

def send_cn_type(cuenta: str, cn_type: str, cn_motivo: str) -> dict:
    try:
        print("Ejecutando send_cn_type con cuenta:", cuenta, "tipo cn:", cn_type, "motivo:", cn_motivo)
        sleep(5)
        return {"result": "ok"}
    except Exception as e:
        return {"result": "False", "error": str(e)}

def external_pause_and_flag_exit(cn_type: str, cn_motivo: str, tipificacion: str) -> dict:
    sleep(5)
    external_hangup()
    sleep(2)

    registro = client_context.copy()
    registro.pop("Colonia", None)
    registro.pop("Status", None)
    registro.pop("status", None)
    registro["status"]    = "Pendiente"
    registro["cn_type"]   = cn_type
    registro["cn_motivo"] = cn_motivo
    registro["tipoficacion"] = tipificacion

    columnas     = ", ".join(registro.keys())
    marcadores   = ", ".join(["%s"] * len(registro))
    sql   = f"INSERT INTO CNAgenteDepuracion ({columnas}) VALUES ({marcadores})"
    valores      = list(registro.values())

    try:
        conn = pymysql.connect(
            host='192.168.50.13',
            user='lhernandez',
            password='lhernandez10',
            database='asterisk',
            connect_timeout=5,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, valores)
            conn.commit()
        print("✅ Registro insertado correctamente en CNAgenteDepuracion")

    except Exception as e:
        print(f"❌ Error al insertar en CNAgenteDepuracion: {e}")
        return {"result": "error", "error": str(e)}

    # Enviar tipo de CN y motivo
    SALIDA_ARCHIVO = r"C:\AgentedeVozPython\salir.txt"

    # Crear archivo de salida y pausar
    os.makedirs(os.path.dirname(SALIDA_ARCHIVO), exist_ok=True)
    Path(SALIDA_ARCHIVO).write_text("salir", encoding="utf-8")
    actualizar_actividad("En Espera")

    set_pending_tipificacion(tipificacion)

    actualizar_status(registro["CUENTA"],'Completada')

    return {"result": "ok"}

def actualizar_actividad(actividad: str):
    ip_local = socket.gethostbyname(socket.gethostname())

    try:
        conn = pymysql.connect(
            host='192.168.50.13',
            user='lhernandez',
            password='lhernandez10',
            database='asterisk',
            connect_timeout=5,
            charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE agentesDepuracion SET actividad = %s WHERE ip= %s",
                (actividad, ip_local)
            )
        conn.commit()
        print(f"✅ Actividad actualizada a '{actividad}'")
    except Exception as e:
        print(f"❌ Error al actualizar actividad: {e}")
    finally:
        conn.close()

def actualizar_stauts(status):
    ip_local = socket.gethostbyname(socket.gethostname())

    try:
        conn = pymysql.connect(
            host='192.168.50.13',
            user='lhernandez',
            password='lhernandez10',
            database='asterisk',
            connect_timeout=5,
            charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE agentesDepuracion SET status = %s WHERE ip= %s",
                (status, ip_local)
            )
        conn.commit()
        print(f"✅ status actualizada a '{status}'")
    except Exception as e:
        print(f"❌ Error al status actividad: {e}")
    finally:
        conn.close()


