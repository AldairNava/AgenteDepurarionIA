from os import environ, path, remove, listdir
import apiCyberHubOrdenes as api
from login import loginSiebel
from shutil import rmtree
from funcionalidad import *
import socket
import os
from time import sleep
from selenium.common.exceptions import WebDriverException as WDE
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

# Estado global del driver y flags
drivers = {
    "driver": None,
    "keepalive": False,
    "in_request": False,
}

# Credenciales globales
USUARIO = 'p-efgarciac'
PASSWORD = 'Me&gG28032204'

def delTemporales():
    """
    Elimina todos los archivos y carpetas del directorio temporal del sistema.
    """
    temp_folder = environ.get('TEMP')
    if not temp_folder:
        print('Variable TEMP no definida.')
        return
    try:
        for temp_file in listdir(temp_folder):
            temp_file_path = path.join(temp_folder, temp_file)
            try:
                if path.isfile(temp_file_path):
                    remove(temp_file_path)
                elif path.isdir(temp_file_path):
                    rmtree(temp_file_path)
            except Exception:
                pass
        print('Eliminación de temporales OK!')
    except Exception as e:
        print(f'Error al eliminar temporales: {e}')

def iniciar_sesion_permanente(usuario, password):
    """
    Intenta iniciar sesión hasta que tenga éxito.
    """
    while True:
        try:
            driver, status = loginSiebel(usuario, password)
            if status:
                print('→ LOGIN EXITOSO ←')
                return driver
            print('→ LOGIN INCORRECTO, reintentando en 5s...')
        except Exception as e:
            print(f'Error login: {e}, reintentando en 5s...')
        sleep(5)

def keep_alive(driver):
    """
    Realiza un clic cada 15 segundos en el body para mantener la sesión activa,
    pero solo cuando no estemos procesando una petición.
    """
    while True:
        if not drivers["in_request"]:
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                ActionChains(driver).move_to_element(body).click().perform()
                print('Keepalive: clic realizado')
            except Exception as e:
                print(f'Keepalive: error al clicar {e}')
        else:
            print('Keepalive: petición en curso, posponiendo click')
        sleep(60)

def get_driver():
    """
    Devuelve un WebDriver válido; si no existe o la sesión expira, crea uno nuevo.
    Además, inicia un thread de keep-alive si aún no está activo.
    """
    drv = drivers.get('driver')
    needs_login = False

    if not drv:
        needs_login = True
    else:
        try:
            _ = drv.current_url  # ping para validar sesión
        except Exception:
            needs_login = True

    if needs_login:
        print('Obteniendo nuevo driver...')
        try:
            if drv:
                drv.quit()
        except:
            pass
        drv = iniciar_sesion_permanente(USUARIO, PASSWORD)
        delTemporales()
        drivers['driver'] = drv

        # Iniciar keepalive una sola vez
        if not drivers['keepalive']:
            ka_thread = threading.Thread(target=keep_alive, args=(drv,), daemon=True)
            ka_thread.start()
            drivers['keepalive'] = True

    return drv

@app.route('/set_serial', methods=['POST'])
def set_serial():
    drivers["in_request"] = True
    try:
        data = request.get_json() or {}
        cuenta = data.get('cuenta')
        serial = data.get('serial')
        if not cuenta or not serial:
            return jsonify(False)   # faltan datos → false

        driver = get_driver()
        resultado = manejar_serial(driver, cuenta, serial)
        return jsonify(True)       # todo OK → true
    except Exception as e:
        print(f'Error set_serial: {e}')
        return jsonify(False)      # cualquier excepción → false
    finally:
        drivers["in_request"] = False

@app.route('/set_cn_type', methods=['POST'])
def set_cn_type():
    drivers["in_request"] = True
    try:
        data = request.get_json() or {}
        cuenta    = data.get('cuenta')
        cn_type   = data.get('cn_type')
        cn_motivo = data.get('cn_motivo')
        if not cuenta or not cn_type or not cn_motivo:
            return jsonify(False)   # faltan datos → false

        driver = get_driver()
        resultado = inicio(driver, cuenta, cn_type, cn_motivo)
        return jsonify(True)       # todo OK → true
    except Exception as e:
        print(f'Error set_cn_type: {e}')
        return jsonify(False)      # cualquier excepción → false
    finally:
        drivers["in_request"] = False


if __name__ == '__main__':
    # Inicia el driver en background
    threading.Thread(target=get_driver, daemon=True).start()
    # Arranca Flask en el mismo proceso, puerto 8000, sin reloader
    app.run(
        host='0.0.0.0',
        port=8000,
        threaded=True,
        debug=False,
        use_reloader=False
    )
