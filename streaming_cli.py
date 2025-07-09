import asyncio
from selenium.webdriver.common.by import By
import os
import requests
from time import sleep
import json
import pyaudio
from openai_realtime_client import RealtimeClient, AudioHandler, InputHandler, TurnDetectionMode
from dotenv import load_dotenv
from llama_index.core.tools import FunctionTool
from instrucciones import get_instructions, update_client_context_from_db, client_context
from tools import *

def load_config(self, config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
# Cargar variables de entorno
load_dotenv()

# === VARIABLES GLOBALES ===
_client = None
_main_loop = None
aio_thread = None
aio_should_shutdown = False
agent_started = False
agent_start_lock = asyncio.Lock()

# Rutas de archivos
salida_file   = r"C:\AgentedeVozPython\salir.txt"
shutdown_file = r"C:\AgentedeVozPython\shutdown.txt"
hangup_file   = r"C:\AgentedeVozPython\hangup.txt"
err_file = r"C:\AgentedeVozPython\errorcliente.txt"

def register_client(client):
    global _client
    _client = client

def set_main_loop(loop):
    global _main_loop
    _main_loop = loop

# === HERRAMIENTAS PARA VICIDIAL ASINCRONAS ===
def send_serial() -> dict:
    client = _client

    async def serial_task():
        try:
            response = await asyncio.to_thread(
                requests.post,
                "http://localhost:8000/set_serial",
                json={
                    "cuenta": client_context["CUENTA"],
                    "serial": client_context["NumeroSerieInternet"],
                },
            )
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}")
            resultado = response.json()
            print("Respuesta del servidor:", resultado)
            if resultado is True:
                print("✅ Reset exitoso")
                await client.send_text(
                    "di la siguiente frese sin agregar nada a esta(el reset se realizó correctamente, podiras esperar a que las luceses del módem se estabilicen y luego continuar con la llamada) se estabilicen y revisar su cneccion"
                )
            else:
                print("❌ Reset fallido (el endpoint devolvió False)")
                await client.send_text(
                    "Ocurrió un error al realizar el reset de tu módem; "
                    "procederemos a agendar la visita técnica (paso 1D)."
                )
        except Exception as e:
            print(f"Excepción durante el reset: {e}")
            await client.send_text(
                "Hubo un problema al conectar con el servicio de reset; "
                "procederemos con la visita técnica programada (paso 1D)."
            )

    if _main_loop is None:
        return {"result": "false", "error": "Main event loop no registrado"}

    asyncio.run_coroutine_threadsafe(serial_task(), _main_loop)
    return {"result": "ok (tarea en background con loop principal)"}

tools = [
    FunctionTool.from_defaults(fn=send_serial),
    FunctionTool.from_defaults(fn=external_pause_and_flag_exit),
    FunctionTool.from_defaults(fn=transfer_conference),
]

async def bandera_loop(navegador, client, check_interval: float = 1.0):
    """
    Loop asíncrono que:
     • Detecta ON  → actualiza client_context, envía update_session e inicia conversación.
     • Detecta DEAD→ envía despedida y marca el fin de la llamada.
    """
    llamada_activa = False
    ip = navegador.config['ip']
    XPATH_BANDERA = '//*[@id="Tabs"]/table/tbody/tr/td[5]/img'
    XPATH_CUENTA  = '//*[@id="last_name"]'
    
    while True:
        try:
            img = navegador.driver.find_element(By.XPATH, XPATH_BANDERA)
            src = img.get_attribute('src')
            
            # if os.path.exists(shutdown_file):

            
            # -----------------------------
            # Cuando la llamada entra (ON)
            # -----------------------------
            if src == f'http://{ip}/agc/images/agc_live_call_ON.gif' and not llamada_activa:
                llamada_activa = True
                # 1) Extraer cuenta y actualizar contexto
                cuenta = navegador.driver.find_element(By.XPATH, XPATH_CUENTA).get_attribute('value')
                cliente = update_client_context_from_db("cuenta")
                if cliente is None:
                    # Manejo de cuenta no encontrada
                    actualizar_actividad("En Error")
                    external_hangup()
                    sleep(1)
                    external_status_SCCCUE()
                    
                else:
                    actualizar_actividad("En llamada")
                    # 2) Regenerar instrucciones y enviar update_session
                    nuevas_instr = get_instructions()
                    await client.update_session({"instructions": nuevas_instr})
                    client.instructions = nuevas_instr
                    await client.send_text("!Hola¡")
            
            # --------------------------------
            # Cuando la llamada cuelga (DEAD)
            # --------------------------------
            elif src == f'http://{ip}/agc/images/agc_live_call_DEAD.gif' and llamada_activa:
                llamada_activa = False
                print('📴 Llamada colgada')
                with open(hangup_file, 'w') as f:
                    f.write('hangup')
            
            
        except Exception as e:
            print(f"⚠️ Error leyendo bandera: {e}")
        
        await asyncio.sleep(check_interval)
        
# === LÓGICA DE INICIO DEL AGENTE ===
async def start_agent(navegador):
    actualizar_actividad("En espera")
    global _client, agent_started

    if os.path.exists(salida_file):
        os.remove(salida_file)
    if os.path.exists(hangup_file):
        os.remove(hangup_file)

    config_file='config.json'

    set_main_loop(asyncio.get_running_loop())

    pa = pyaudio.PyAudio()
    default_in  = pa.get_default_input_device_info()["index"]
    default_out = pa.get_default_output_device_info()["index"]
    print(f"Usando entrada  → {default_in}")
    print(f"Usando salida   → {default_out}")
    navegador.config = navegador.load_config(config_file)

    audio_handler = AudioHandler(input_index=default_in, output_index=default_out)
    input_handler = InputHandler()
    input_handler.loop = asyncio.get_running_loop()

    inactivity_counter = 0
    inactivity_task = None
    session_active = True

    def reset_inactivity_timer():
        nonlocal inactivity_task, inactivity_counter, session_active
        if not session_active:
            return  # no volvemos a programar nada si ya estamos fuera de sesión
        if inactivity_task:
            inactivity_task.cancel()
        inactivity_counter = 0
        inactivity_task = asyncio.create_task(inactivity_check())

    async def inactivity_check():
        nonlocal inactivity_task, inactivity_counter, session_active
        try:
            if not session_active:
                return  # abandonamos inmediatamente
            print("⏱ Esperando silencio…")
            await asyncio.sleep(40)
            if not session_active:
                return

            inactivity_counter += 1
            if inactivity_counter in (1, 2):
                print(f"Pregunta de seguimiento {inactivity_counter}")
                await client.send_text(
                        "si Ejecutaste la herramienta send_serial di la siguiente frase sin agregar nada a esta"
                        "(Continuo con usted señor/señorita + [apellido o nombre del cliente] ...) "
                        "si no ejecutaste el tool di la siguiente frase sin agregar nada más ..."
                    )
                # reprogramamos otra ronda
                inactivity_task = asyncio.create_task(inactivity_check())
            elif inactivity_counter == 3:
                print("Colgando la llamada")
                await client.send_text(
                        "Ejecuta la herramienta *external_pause_and_flag_exit* para finalizar sin decir nada mas"
                    )
        except asyncio.CancelledError:
            print("🛑 inactivity_check cancelado")

    client = RealtimeClient(
        api_key=os.getenv('OPENAI_API_KEY'),
        on_text_delta=lambda text: print(f"Assistant: {text}", end="", flush=True),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        voice="coral",
        on_interrupt=lambda: audio_handler.stop_playback_immediately(),
        turn_detection_mode=TurnDetectionMode.SERVER_VAD,
        on_client_silence=reset_inactivity_timer,
        tools=tools,
        instructions=get_instructions(),
    )

    register_client(client)

    await client.connect()
    asyncio.create_task(client.handle_messages())
    asyncio.create_task(audio_handler.start_streaming(client))
    bandera_task = asyncio.create_task(bandera_loop(navegador, client, check_interval=1.0))

    try:
        while True:
            if os.path.exists(salida_file):
                session_active = False
                if inactivity_task:
                    inactivity_task.cancel()
                bandera_task.cancel()
                break

            # 3) Colgado real de llamada
            if os.path.exists(hangup_file):
                await client.send_text("Ejecuta la herramienta *external_pause_and_flag_exit* con los parametros segun la llamada sin decir nada mas")

            await asyncio.sleep(0.1)

    finally:
        audio_handler.stop_streaming()
        audio_handler.cleanup()
        await client.close()
        agent_started = False
        print("✅ Sesión cerrada correctamente")


# if __name__ == "__main__":
#     update_client_context_from_db('80135614')
#     asyncio.run(start_agent())