import os
import sys
import json
import signal
import ctypes
import asyncio
import subprocess
import threading
from time import sleep
from ctypes import wintypes
from selenium import webdriver
from streaming_cli import start_agent
from flask import Flask, request, jsonify
from selenium.webdriver.common.by import By
from tools import *

vicidial_automation = None
app = Flask(__name__)

automation_thread = None
automation_loop = None
shutdown_file = r"C:\AgentedeVozPython\shutdown.txt"

def _run_automation_safe():
    # Wrapper que arranca tu automatización
    _run_automation('config.json')

def _cleanup():
    global vicidial_automation
    if vicidial_automation:
        vicidial_automation._stop = True
        try:
            vicidial_automation.cerrar_sesion_y_salir()
        except Exception:
            pass
        vicidial_automation = None

# Windows: manejo de cierre de consola
if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    HandlerRoutine = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    def _console_ctrl_handler(ctrl_type):
        if ctrl_type in (0, 1, 2, 5):
            _cleanup()
            return True
        return False
    kernel32.SetConsoleCtrlHandler(HandlerRoutine(_console_ctrl_handler), True)

# POSIX: manejo de señales como Ctrl+C
def _signal_handler(sig, frame):
    print(f"🛑 Señal {sig} recibida. Cerrando todo...")
    _cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)
if hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, _signal_handler)

# Clase principal
class VicidialAutomation:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.driver = None
        self._stop = False

    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            return json.load(f)

    def _login(self, username, password):
        user_field = self.driver.find_element(By.XPATH,
            '//*[@id="vicidial_form"]/center/table/tbody/tr[3]/td[2]/input')
        pass_field = self.driver.find_element(By.XPATH,
            '//*[@id="vicidial_form"]/center/table/tbody/tr[4]/td[2]/input')
        user_field.send_keys(username)
        pass_field.send_keys(password)
        sleep(2)

    def _select_campaign(self, campaign_value):
        try:
            select_campaign = self.driver.find_element(By.XPATH, '//*[@id="VD_campaign"]')
            select_campaign.click()
        except Exception:
            self.driver.quit(); sys.exit(1)
        sleep(2)
        if campaign_value == "3006 - PruebaBot":
            xpath = ('/html/body/form/center/table/tbody/tr[5]/td[2]/font/span/select/option[3]')
        else:
            xpath = ('/html/body/form/center/table/tbody/tr[5]/td[2]/font/span/select/option[2]')
        self.driver.find_element(By.XPATH, xpath).click()
        sleep(2)

    def _close_popup(self):
        try:
            ok = self.driver.find_element(By.XPATH,
                '//*[@id="DeactivateDOlDSessioNSpan"]/table/tbody/tr/td/font/a')
            ok.click()
        except:
            pass

    def cerrar_sesion_y_salir(self):
        try:
            logout_button = self.driver.find_element(By.XPATH,
                '/html/body/form[1]/span[2]/table/tbody/tr/td[2]/font/a')
            logout_button.click()
            sleep(2)
        except:
            pass
        finally:
            if self.driver:
                self.driver.quit()

            status='session cerrada'
            return status

    async def run(self):
        actualizar_stauts(True)
        actualizar_actividad("Encendido")
        login_success = False
        while not self._stop and not login_success:
            try:
                if self.driver:
                    self.driver.quit()
                self.driver = webdriver.Chrome()
                print("🔗 Navegando a la URL de Vicidial...")
                self.driver.get(self.config['url'])
                sleep(2)

                print("🔐 Realizando primer login con extensión...")
                self._login(self.config['extension'], self.config['password'])
                self.driver.find_element(By.XPATH,
                    '//*[@id="vicidial_form"]/center/table/tbody/tr[5]/td/input').click()
                sleep(2)

                print("🔐 Realizando segundo login con extensión + password...")
                self._login(self.config['username'], self.config['user_password'])
                sleep(2)

                print("📋 Seleccionando campaña...")
                self._select_campaign(self.config['campaign_value'])
                sleep(2)

                print("Boton submit")
                self.driver.find_element(By.XPATH,
                    '/html/body/form/center/table/tbody/tr[6]/td/input').click()
                sleep(5)

                print("❎ Verificando si hay popup que cerrar...")
                self._close_popup()
                sleep(5)

                print("🟢 Colocando estado en DISPONIBLE...")
                self.driver.find_element(By.XPATH,
                    '//*[@id="DiaLControl"]/a/img').click()
                login_success = True
                print("✅ Inicio de sesión completado correctamente.")

            except Exception as e:
                print("❌ Error al iniciar sesión:", e)
                if self._stop:
                    return
                print("🔄 Reintentando reinicio del navegador en 5s...")
                sleep(5)

        if login_success:
            print("✅ Sesión Vicidial lista, arrancando agente…")
            while not self._stop:
                if os.path.exists(shutdown_file):
                    print("🔴 Deteniendo automatización archivo shutdown")
                    actualizar_stauts(False)
                    actualizar_actividad("Apagado")
                    os.remove(shutdown_file)
                    break

                await start_agent(self)

        session = self.cerrar_sesion_y_salir()
        return session

# -------------------------------------
# Función asíncrona principal
# -------------------------------------
async def iniciar_automatizacion_async(config_file='config.json'):
    global vicidial_automation
    vicidial_automation = VicidialAutomation(config_file)
    await vicidial_automation.run()

def _run_automation(config_file):
    global automation_loop
    # Cada hilo necesita su propio event loop
    automation_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(automation_loop)
    # Esto bloqueará hasta que termine _stop = True
    automation_loop.run_until_complete(iniciar_automatizacion_async(config_file))
    automation_loop.close()

@app.route('/actualizacion', methods=['POST'])
def actualizar_repositorio():
    global automation_thread

    data   = request.get_json(force=True)
    status = data.get('status', False)

    # Sólo procedemos si status es True
    if status is not True:
        return jsonify(error="status debe ser true"), 400

    # 1) Si el agente está corriendo, lo detenemos
    if automation_thread and automation_thread.is_alive():
        open(shutdown_file, 'w').close()
        # esperamos a que el hilo realmente termine
        automation_thread.join(timeout=30)

    # 2) Hacemos el git pull en tu carpeta de proyecto
    try:
        # Opcional: cambiar de directorio si es necesario
        # os.chdir(r"C:\ruta\a\tu\proyecto")
        resultado = subprocess.run(
            ["git", "pull", "--rebase"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return jsonify(
            error="Error al hacer git pull",
            salida=e.stdout,
            error_output=e.stderr
        ), 500

    # 3) (Re)iniciamos el agente
    automation_thread = threading.Thread(
        target=_run_automation_safe,
        daemon=True
    )
    automation_thread.start()

    return jsonify(
        actualizado=True,
        git_stdout=resultado.stdout
    ), 200

@app.route('/estado', methods=['POST'])
def control_automation_post():
    global automation_thread

    data   = request.get_json(force=True)
    estado = bool(data.get('estado', False))

    if estado:
        # == INICIO ==
        if not automation_thread or not automation_thread.is_alive():
            if os.path.exists(shutdown_file):
                os.remove(shutdown_file)
            automation_thread = threading.Thread(
                target=_run_automation,
                args=('config.json',),
                daemon=True
            )
            automation_thread.start()
            return jsonify(status="Iniciando"), 200
        else:
            return jsonify(status="iniciado"), 200
    else:
        # == PARADA ==
        if automation_thread and automation_thread.is_alive():
            open(shutdown_file, 'w').close()
            return jsonify(status="Deteniendo"), 200
        return jsonify(status="detenido"), 200

# Ruta sólo para GET (consultar estado)
@app.route('/estado', methods=['GET'])
def control_automation_get():
    is_running = bool(automation_thread and automation_thread.is_alive())
    return jsonify(running=is_running), 200


def _run_automation_safe():
    # Wrapper que arranca tu automatización
    _run_automation('config.json')


@app.route('/actualizacion', methods=['POST'])
def actualizar_repositorio():
    global automation_thread

    data   = request.get_json(force=True)
    status = data.get('status', False)

    # Sólo procedemos si status es True
    if status is not True:
        return jsonify(error="status debe ser true"), 400

    # 1) Si el agente está corriendo, lo detenemos
    if automation_thread and automation_thread.is_alive():
        open(shutdown_file, 'w').close()
        # esperamos a que el hilo realmente termine
        automation_thread.join(timeout=30)

    # 2) Hacemos el git pull en tu carpeta de proyecto
    try:
        # Opcional: cambiar de directorio si es necesario
        # os.chdir(r"C:\ruta\a\tu\proyecto")
        resultado = subprocess.run(
            ["git", "pull", "--rebase"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        return jsonify(
            error="Error al hacer git pull",
            salida=e.stdout,
            error_output=e.stderr
        ), 500

    # 3) (Re)iniciamos el agente
    automation_thread = threading.Thread(
        target=_run_automation_safe,
        daemon=True
    )
    automation_thread.start()

    return jsonify(
        actualizado=True,
        git_stdout=resultado.stdout
    ), 200


if __name__ == '__main__':
    # Arranca solo Flask; la automatización la lanzas vía POST /automation
    app.run(host='0.0.0.0', port=3000)

# if __name__ == "__main__":
#     asyncio.run(iniciar_automatizacion_async())