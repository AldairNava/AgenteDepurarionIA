import time
import requests
from time import sleep
from instrucciones import client_context
from pathlib import Path
import os
import json
import socket
import pymysql
config_file= r'C:\AgentedeVozPython\config.json'
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

API_BASE = "http://192.168.50.13/agc/api.php"
SOURCE = "test"
USER = config['username']
PASSWORD = config['user_password']
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

def send_cn_type(cuenta: str, cn_type: str, cn_motivo: str) -> dict:
    try:
        print("Ejecutando send_cn_type con cuenta:", cuenta, "tipo cn:", cn_type, "motivo:", cn_motivo)
        sleep(5)
        return {"result": "ok"}
    except Exception as e:
        return {"result": "False", "error": str(e)}

def external_pause_and_flag_exit(cn_type: str, cn_motivo: str, tipoficacion: str) -> dict:
    sleep(5)
    external_hangup()

    registro = client_context.copy()
    registro.pop("Colonia", None)
    registro.pop("Status", None)
    registro.pop("status", None)
    registro["status"]    = "Pendiente"
    registro["cn_type"]   = cn_type
    registro["cn_motivo"] = cn_motivo
    registro["tipoficacion"] = tipoficacion

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

    # Mapeo completo de tipificaciones
    if tipoficacion == 'SCCAVT':
        external_status_SCCAVT()
    elif tipoficacion == 'SCCOVT':
        external_status_SCCOVT()
    elif tipoficacion == 'SCTSVT':
        external_status_SCTSVT()
    elif tipoficacion == 'SCMADI':
        external_status_SCMADI()
    elif tipoficacion == 'SCCCUE':
        external_status_SCCCUE()
    elif tipoficacion == 'SCMADI':
        external_status_SCMADI()
    elif tipoficacion == 'SIN CONTACTO':
        external_status_SCCCUE()
    elif tipoficacion == 'NI':
        external_status_SCCCUE()
    elif tipoficacion == 'NCBUZ':
        external_status_NCBUZ()
    elif tipoficacion == 'SCNUEQ':
        external_status_SCNUEQ()
    else:
        tipoficacion = "OTRO"
        print("⚠️ Tipificación incorrecta o no reconocida.")

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


