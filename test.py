
import requests
# from datetime import datetime
# from time import sleep

# fecha_captura = datetime.now().isoformat()

# sleep(1)

# payload = {
#             "nombre": "aldair",
#             "telefono": "telefonoVar",
#             "cuenta": "cuenta",
#             "orden": "ordenServicio",
#             "TipoCN": "",
#             "CNGenrado": "",
#             "status": "Marcando",
#             "fechaCaptura": fecha_captura,
#             "fechaCompletado": None
#         }

# url = "https://rpabackizzi.azurewebsites.net/AgenciasExternas/insertDepuracion"

# try:
#     response = requests.post(url, json=payload)
#     if response.status_code == 200:
#         print("Datos enviados exitosamente a la base de datos.")
#     else:
#         print(f"Error al enviar datos: {response.status_code} - {response.text}")
# except Exception as e:
#     print(f"Excepción al enviar datos: {str(e)}")


# import requests
# from typing import Dict

# def send_cn_type(cuenta: str, cn_type: str, cn_motivo: str) -> Dict[str,str]:
#     try:
#         print(f"Ejecutando send_cn_type con cuenta={cuenta}, tipo={cn_type}, motivo={cn_motivo}")
#         res = requests.post(
#             "http://192.168.49.76:5000/set_cn_type",
#             json={
#                 "cuenta": cuenta,
#                 "cn_type": cn_type,
#                 "cn_motivo": cn_motivo
#             },
#             timeout=15
#         )
#         res.raise_for_status()  # lanza excepción si response.status_code >= 400
#         return {"result": "ok"}
#     except requests.RequestException as e:
#         print(f"[Error HTTP] {e}")
#         return {"result": "False", "error": str(e)}

# def send_serial(cuenta: str, serial: str) -> Dict[str,str]:
#     try:
#         print(f"Ejecutando send_serial con cuenta={cuenta} y serial={serial}")
#         res = requests.post(
#             "http://192.168.46.76:5000/set_serial",
#             json={"cuenta": cuenta, "serial": serial},
#             timeout=15
#         )
#         res.raise_for_status()
#         return {"result": "ok"}
#     except requests.RequestException as e:
#         print(f"[Error HTTP] {e}")
#         return {"result": "False", "error": str(e)}
    
# try:
#     response = requests.post(
#         "http://localhost:8080/send",
#         json={"message": "!Holas¡"}
#     )
#     if response.status_code == 200:
#         print("✅ Mensaje enviado al agente:", response.json().get("status"))
#     else:
#         print(f"❌ Falló envío (status {response.status_code}): {response.text}")
# except Exception as e:
#     print(f"⚠️ Error enviando mensaje HTTP: {e}")

# if __name__ == "__main__":
#     # Este llamado enviará el POST y mostrará el resultado por consola
#     salida = send_cn_type("25877482", "1", "FALLA CONTINUA")
#     print("send_cn_type ->", salida)

    # Y si quieres probar también el serial:
    # salida2 = send_serial("25877482", "BS10094431010912")
    # print("send_serial ->", salida2)


# import pyaudio

# p = pyaudio.PyAudio()

# # 🔊 Salida (output) predeterminada
# default_output_index = p.get_default_output_device_info()['index']
# default_output_name = p.get_device_info_by_index(default_output_index)['name']

# # 🎙 Entrada (input) predeterminada
# default_input_index = p.get_default_input_device_info()['index']
# default_input_name = p.get_device_info_by_index(default_input_index)['name']

# print(f"🎙 Entrada predeterminada → Index: {default_input_index} | Nombre: {default_input_name}")
# print(f"🔊 Salida predeterminada  → Index: {default_output_index} | Nombre: {default_output_name}")


# import sounddevice as sd

# duration = 3  # segundos
# fs = 44100
# print("Grabando…")
# recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
# sd.wait()
# print("¡Listo!")


# import pyaudio

# pa = pyaudio.PyAudio()
# for i in range(pa.get_device_count()):
#     info = pa.get_device_info_by_index(i)
#     print(f"{i}: {info['name']}  –  In:{info['maxInputChannels']}  Out:{info['maxOutputChannels']}")
# pa.terminate()


# import pyaudio
# import wave

# p = pyaudio.PyAudio()

# CHUNK = 1024
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 24000
# RECORD_SECONDS = 5
# WAVE_OUTPUT_FILENAME = "prueba_microfono.wav"

# print("🎙 Grabando 5 segundos...")

# stream = p.open(format=FORMAT,
#                 channels=CHANNELS,
#                 rate=RATE,
#                 input=True,
#                 frames_per_buffer=CHUNK)

# frames = []

# for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
#     data = stream.read(CHUNK)
#     frames.append(data)

# stream.stop_stream()
# stream.close()

# wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
# wf.setnchannels(CHANNELS)
# wf.setsampwidth(p.get_sample_size(FORMAT))
# wf.setframerate(RATE)
# wf.writeframes(b''.join(frames))
# wf.close()

# print("✅ Grabado. Reproduce el archivo para verificar.")


# import requests

# resp = requests.post(
#     "http://localhost:8080/send",
#     json={"message": "!Holas¡"}
# )
# print(resp.status_code, resp.json())


# MAIN_SERVICE_URL = "http://localhost:4040/control"
# try:
#     resp = requests.post(MAIN_SERVICE_URL, json={"status": False})
#     print("→ Reenvío a main:", resp.status_code, resp.text)
# except Exception as e:
#     print("⚠️ Error reenviando a main:", e)

# import requests

# STATUS_URL = "http://localhost:3000/estado"

# try:
#     resp = requests.post(STATUS_URL)
#     resp.raise_for_status()
#     data = resp.json()
#     print("Estado del streaming:", data.post("status"))  # True o False
# except requests.RequestException as e:
#     print("Error al consultar estado:", e)

# def controlar_proceso(estado: bool):
#     """
#     Envía una petición al servicio Flask para iniciar o detener el proceso.

#     :param estado: True para iniciar, False para detener.
#     """
import requests

# Ajusta la URL si quieres probar en otra interfaz (127.0.0.1 o tu IP de red)
# url = 'http://127.0.0.1:9090/orden'

# # El número de orden que quieras probar
# payload = {
#     'numero_orden': '1-221006827290'
# }

# try:
#     resp = requests.post(url, json=payload)
#     print(f"Status code: {resp.status_code}")
#     print("Respuesta JSON:", resp.json())
# except Exception as e:
#     print("Error al enviar la petición:", e)
# MAIN_SERVICE_URL = "http://localhost:3000/estado"
# try:
#     resp = requests.post(MAIN_SERVICE_URL, json={"estado": False},timeout=180)
#     print("→ Reenvío a main:", resp.status_code, resp.text)
# except Exception as e:
#     print("⚠️ Error reenviando True a main:", e)

UPDATE_URL = "http://localhost:3000/actualizacion"

try:
    resp = requests.post(
        UPDATE_URL,
        json={"status": True},
        timeout=30
    )
    print("→ POST /actualizacion:", resp.status_code, resp.text)
except Exception as e:
    print("⚠️ Error al llamar a /actualizacion:", e)

# controlar_proceso(True)

#!/usr/bin/env python3
# import argparse
# import requests

# def test_set_serial(cuenta: str, serial: str, host: str = "localhost", port: int = 8000):
#     url = f"http://{host}:{port}/set_serial"
#     payload = {"cuenta": cuenta, "serial": serial}
#     try:
#         resp = requests.post(url, json=payload, timeout=180)
#         print(f"Código HTTP: {resp.status_code}")
#         try:
#             resultado = resp.json()   # aquí recibes True o False
#             print("Respuesta JSON:", resultado)
#         except ValueError:
#             print("No se pudo parsear JSON. Contenido:", resp.text)
#     except requests.RequestException as e:
#         print("Error en la petición:", e)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Test para /set_serial")
#     parser.add_argument("--cuenta", required=False, default="45187160", help="Número de cuenta")
#     parser.add_argument("--serial", required=False, default="ZTEGD880F2A1",  help="Número de serie")
#     parser.add_argument("--host",    default="192.168.51.167", help="mamalona4")
#     parser.add_argument("--port",    type=int, default=8000, help="8000")
#     args = parser.parse_args()

#     test_set_serial(args.cuenta, args.serial, args.host, args.port)
