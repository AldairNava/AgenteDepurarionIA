import apiCyberHubOrdenes as api
from time import sleep
from selenium.webdriver.common.by import By
from funcionalidad import *
from login import loginSiebel
from flask import Flask, request, jsonify
import threading
import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tele import send_msg

app = Flask(__name__)

def disponibilidad(numero_orden, driver):
    
    fechas = buscar_orden(driver,numero_orden)

    print(fechas)
    
    return fechas


def start_attention_flow(numero_orden, fecha_atencion, horario):
    # TODO: Implementa aquí el flujo de atención
    print(f"Iniciando flujo de atención: {numero_orden}, {fecha_atencion}, {horario}")
    # Llama a tus funciones de apiCyberHubOrdenes u otras


@app.route('/orden', methods=['POST'])
def recibir_orden():
    global driver
    data = request.get_json(force=True)
    numero_orden = data.get('numero_orden')
    if not numero_orden:
        return jsonify({'error': 'Falta numero_orden'}), 400
    if not re.match(r'^\d+-\d+$', numero_orden):
        return jsonify({'error': 'Formato numero_orden inválido'}), 400

    # 2) Arranca el hilo pasando ambos argumentos
    threading.Thread(
        target=disponibilidad,
        args=(numero_orden, driver),
        daemon=True
    ).start()

    return jsonify({'message': 'Flujo de orden iniciado'}), 200


@app.route('/atencion', methods=['POST'])
def recibir_atencion():
    data = request.get_json(force=True)
    numero_orden = data.get('numero_orden')
    fecha_atencion = data.get('fecha_atencion')
    horario = data.get('horario')
    if not all([numero_orden, fecha_atencion, horario]):
        return jsonify({'error': 'Faltan campos'}), 400
    threading.Thread(target=start_attention_flow, args=(numero_orden, fecha_atencion, horario), daemon=True).start()
    return jsonify({'message': 'Flujo de atención iniciado'}), 200


def mantener_session(driver):
    """
    Cada minuto busca un elemento en pantalla y hace click.
    Reemplaza 'TU_XPATH_AQUI' con el XPATH real de tu elemento.
    """
    max_intentos = 5
    intentos = 0
    while True:
        try:
            elemento = driver.find_element(By.XPATH, pagina_inicial)
            elemento.click()
        except Exception as e:
            intentos += 1
            print(f"Error en mantener_sesion intento {intentos}: {e}")
            if intentos >= max_intentos:
                send_msg('Mantenimiento de sesión fallido después de 5 intentos')
                try:
                    driver.quit()
                except:
                    pass
                sys.exit(1)
        sleep(60)


def main():
    global driver
    usuario = 'p-efgarciac'
    password = 'Me&gG28032204'

    # limpiar equipo
    delTemporales()

    # Intentos de login
    max_intentos = 5
    intentos = 0
    driver = None
    status = False
    while intentos < max_intentos and not status:
        print(f'Intento de login {intentos+1} de {max_intentos}')
        driver, status = loginSiebel(usuario, password)
        if status:
            break
        intentos += 1
        sleep(5)

    if not status:
        print('Error: No se pudo iniciar sesión después de 5 intentos')
        send_msg('Login fallido después de 5 intentos agente depuracion 5')
        return

    print('LOGIN EXITOSO')

    disponibilidad('1-221006827290',driver)

    # # Iniciar tarea periódica cada minuto
    # hilo_sesion = threading.Thread(target=mantener_session, args=(driver,), daemon=True)
    # hilo_sesion.start()

    # # Levantar servidor Flask en el puerto 8080 SIN el parámetro args
    # app.run(host='0.0.0.0', port=9090, use_reloader=False)


if __name__ == '__main__':
    main()
