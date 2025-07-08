import pytz
import requests
from datetime import datetime
import time
from requests.exceptions import ConnectionError, RequestException, HTTPError
s= requests.Session()

def send_msg(msg):
    IST = pytz.timezone('America/Mexico_City')
    raw_TS = datetime.now(IST)
    curr_time = raw_TS.strftime("%H-%M-%S")
    msg = f"Extracciones Mariana: {msg}"
    telegram_api = f"https://api.telegram.org/bot6819354375:AAFb2UuBWfbOkT83YDyt2IH_lHSUgOpnkuU/sendMessage?chat_id=-4539225320&text={msg}"
    
    for attempt in range(5):  # Reintentar hasta 5 veces
        try:
            tel_resp = s.get(telegram_api)
            if tel_resp.status_code == 200:
                print(f"Mensaje Enviado a Telegram")
                break
            else:
                error_msg = tel_resp.text
                print(f"ERROR: Mensaje no Enviado: {error_msg}")
                time.sleep(5)
        except (ConnectionError, HTTPError) as e:
            print(f"Attempt {attempt+1}: Connection error occurred: {e}")
            if attempt < 4:  # No es el último intento
                time.sleep(5)  # Esperar 5 segundos antes de reintentar
            else:
                print("All retry attempts failed. Could not send message to Telegram.")
                break
        except RequestException as e:
            print(f"Attempt {attempt+1}: General error occurred: {e}")
            break  # No reintentar en caso de otros tipos de errores


# send_msg("buenoa dias")

