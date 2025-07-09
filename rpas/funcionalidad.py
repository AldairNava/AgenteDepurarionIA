from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.keys import Keys
from datetime import datetime, date, timedelta
from selenium.webdriver.common.by import By
from os import environ, path, remove, listdir
from shutil import rmtree
from selenium import webdriver
from time import sleep
from rutas import *
import  pyautogui  as pg
import autoit as it

def buscar_orden(driver, numero_orden: str):
    print("🔍 Iniciando búsqueda de orden...")

    try:
        print("📄 Verificando página inicial")
        intentos, elemento = validar_elemento_presentes(driver, pagina_inicial)
        if intentos >= 5 or not elemento:
            print("❌ No cargó la página inicial")
            return False
        elemento.click()
        print("✅ Click en 'órdenes de servicio'")

        print("🔎 Esperando lupa de búsqueda")
        intentos, elemento = validar_elemento_presentes(driver, lupa_ordenes)
        if intentos >= 5 or not elemento:
            print("❌ No apareció la lupa")
            return False
        elemento.click()
        print("✅ Click en lupa")

        print("⌨️ Buscando campo para ingresar número")
        intentos, campo = validar_elemento_presentes(driver, input_orden)
        if intentos >= 5 or not campo:
            print("❌ Campo de orden no visible")
            return False
        campo.send_keys(numero_orden)
        print(f"✅ Número de orden '{numero_orden}' ingresado")

        print("➡️ Buscando orden")
        intentos, boton_buscar = validar_elemento_presentes(driver, buscar)
        if intentos >= 5 or not boton_buscar:
            print("❌ Botón buscar no disponible")
            return False
        boton_buscar.click()
        print("✅ Click en 'Buscar'")

        print("📄 Seleccionando orden")
        intentos, orden = validar_elemento_presentes(driver, oden)
        if intentos >= 5 or not orden:
            print("❌ La orden no aparece en la lista")
            return False
        orden.click()
        print("✅ Orden seleccionada")

        print("📅 Abriendo selector de fecha")
        intentos, boton_fecha = validar_elemento_presentes(driver, fecha_atencion)
        if intentos >= 5 or not boton_fecha:
            print("❌ Botón de fecha no encontrado")
            return False
        boton_fecha.click()
        print("✅ Click en fecha de atención")
        WebDriverWait(driver, 10).until(EC.alert_is_present()).accept()
        print("☑️ Alerta aceptada")

        print("📆 Buscando calendario")
        intentos, calendario_elemento = validar_elemento_presentes(driver, calendario)
        if intentos >= 5 or not calendario_elemento:
            print("❌ Calendario no disponible")
            return False
        calendario_elemento.click()
        print("✅ Click en calendario")

        print("📤 Obteniendo fechas disponibles...")
        return obtener_fechas_disponibles(driver)

    except Exception as e:
        print(f"⚠️ Error en buscar_orden: {e}")
        return False


def seleccionar_fecha_horario(driver, fecha_obj: date, turno: str) -> bool:
    # Formato que aparece en el <td> (solo día/mes/año)
    buscado = fecha_obj.strftime("%d/%m/%Y")
    # Lower para comparar sin case
    turno = turno.lower()

    # Recorremos todas las filas del cuerpo de la tabla
    filas = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for fila in filas:
        # 1) Sacamos el texto de la celda Fecha de atención y truncamos hora
        celda_fecha = fila.find_element(
            By.XPATH,
            ".//td[contains(@id,'_Fecha_de_atencion')]"
        ).text.split()[0]  # '03/07/2025 00:00:00' → ['03/07/2025', '00:00:00']

        if celda_fecha != buscado:
            continue

        # 2) Vemos su horario
        celda_horario = fila.find_element(
            By.XPATH,
            ".//td[contains(@id,'_Horario_de_atencion')]"
        ).text.lower()

        if turno == "matutino" and "matutino" in celda_horario:
            pass
        elif turno == "vespertino" and "vespertino" in celda_horario:
            pass
        else:
            # la fecha coincide, pero no el turno
            continue

        # 3) Marcamos el checkbox de esa fila
        try:
            check = fila.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            if not check.is_selected():
                check.click()
            return True
        except:
            # si la celda no tiene <input>, quizá hay que clicar la propia celda:
            celda_check = fila.find_element(By.XPATH, ".//td[2]")
            celda_check.click()
            return True

    # si llegamos aquí, no encontramos combinación fecha+turno
    return False


def obtener_fechas_disponibles(driver, dias_a_ver=5):
    """
    Recorre desde mañana hasta `dias_a_ver` días posteriores
    y devuelve una lista de objetos date que estén disponibles
    en el datepicker.
    """
    hoy = date.today()
    disponibles = []

    for offset in range(1, dias_a_ver + 1):
        fecha = hoy + timedelta(days=offset)
        dia = fecha.day
        mes = fecha.month - 1  # jQuery UI datepicker usa mes 0-based
        year = fecha.year

        xpath = (
            f"//td[@data-handler='selectDay' "
            f"and normalize-space(text())='{dia}' "
            f"and @data-year='{year}' "
            f"and @data-month='{mes}']"
        )

        if driver.find_elements(By.XPATH, xpath):
            disponibles.append(fecha)

    return disponibles

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

def validar_elemento_presentes(driver, x_path):
    intentos = 0
    MAX_INTENTOS = 6
    elemento = None

    while intentos < MAX_INTENTOS:
        try:
            elemento = driver.find_element(By.XPATH, x_path)
            print(f"✅ Elemento encontrado en intento {intentos + 1}")
            break
        except Exception as e:
            intentos += 1
            print(f"⏳ Cargando ventana... intento {intentos} fallido. Error: elemento no encontrado")
            sleep(3)  # Puedes reducir el tiempo si es para debug rápido

    return intentos


def cargandoElemento(driver, elemento, atributo, valorAtributo, path = False):

    cargando = True
    contador = 0

    while cargando:

        sleep(1)
        try: 
            print('Esperando a que el elemento cargue')
            if path == False: 
                driver.find_element(By.XPATH, f"//{elemento}[@{atributo}='{valorAtributo}']").click()
                return True, ''
            else:
                driver.find_element(By.XPATH, path).click()
                return True, ''
        
        except:

            try:
                print('Validando posible warning')
                contador += 1
                sleep(1)
                alert = Alert(driver)
                alert_txt = alert.text
                print(f'♦ {alert_txt} ♦')
                if 'Cuenta en cobertura FTTH' in alert_txt: 
                    alert.accept()
                    print('aqui')
                    return True, ''
                else: return False, f'Inconsistencia Siebel: {alert_txt}'
            except:
                print('Pantalla Cargando')
                if contador == 10: return False, 'elemento no carga'

def home(driver): driver.find_element(By.XPATH, "//a[@title='Pantalla Única de Consulta']").click()


# Función de apertura para generar validaciones
def inicio(driver, cuenta,tipoCN,motivoCN):

    try:

        pathEstadoCN = '/html/body/div[1]/div/div[5]/div/div[8]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div/div/form/div/span/div[3]/div/div/table/tbody/tr[4]/td[5]'
        pathPickListEstadoCN = '/html/body/div[1]/div/div[5]/div/div[8]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div/div/form/div/span/div[3]/div/div/table/tbody/tr[4]/td[5]/div/span'
        pathOpcCerradoCN = '/html/body/div[1]/div/div[5]/div/div[8]/ul[16]/li[7]/div'

        
        print('→ Buscando Cuenta')

        # Pantalla Consulta (Click)
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'a', 'title', 'Pantalla Única de Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        # Buscando Elemento
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'button', 'title', 'Pantalla Única de Consulta Applet de formulario:Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        lupa_busqueda_cn, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Numero Cuenta')
        if lupa_busqueda_cn == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        # Ingreso Cuenta
        input_busqueda_cuenta = driver.find_element(By.XPATH, "//input[@aria-label='Numero Cuenta']")
        input_busqueda_cuenta.send_keys(cuenta)
        input_busqueda_cuenta.send_keys(Keys.RETURN)
        print('♦ Cuenta Ingresada ♦')

        # Cargando Cuenta
        cargaPantalla, resultado = cargandoElemento(driver, '', '', '', path= "//*[contains(@aria-label,'SALDO VENCIDO')]")
        if cargaPantalla == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        print('♥ Cuenta OK! ♥')

        # Inicio de Generacion CN
        # Buscando Creacion CN
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'button', 'title', 'Casos de Negocio Applet de lista:Nuevo')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        sleep(5)

        if tipoCN == 1:
            Categoria = 'Outbound'
            Motivo= 'Seguimientos especiales'
            SubMotivo = 'Limpieza de pool'
            Solucion = 'Cancelación TC'  
            Comentario = 'SE CONTACTA A TT COMENTA QUE SU SERVICIO SE ENCUENTRA FUNCIONANDO CORRECTAMENTE SE CIERRA OS Y CANCELA VT' 
            MoCierre = 'B.O. confirma y soluciona' 
        else:
            Categoria = 'Outbound'
            Motivo= 'Seguimientos especiales'
            SubMotivo = 'Limpieza de pool'
            Solucion = 'Confirmacion TC'  
            Comentario = 'SE CONTACTA A TT COMENTA QUE SU SERVICIO SE ENCUENTRA FUNCIONANDO CORRECTAMENTE SE CIERRA OS Y CANCELA VT' 
            MoCierre = 'RAC informa y soluciona' 
            MoCliente = 'CONTINUA FALLA'

        # Llenado de CN
        # Buscando Categoria
        elementoActivo, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Categoria')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        categoria = driver.find_element(By.XPATH, "//input[@aria-label='Categoria']")
        categoria.send_keys(Categoria)
        categoria.send_keys(Keys.RETURN)

        # Buscando Motivo
        elementoActivo, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Motivo')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        motivo = driver.find_element(By.XPATH, "//input[@aria-label='Motivo']")
        motivo.send_keys(Motivo)
        motivo.send_keys(Keys.RETURN)

        # Buscando Sub Motivo
        elementoActivo, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Submotivo')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        subMotivo = driver.find_element(By.XPATH, "//input[@aria-label='Submotivo']")
        subMotivo.send_keys(SubMotivo)
        subMotivo.send_keys(Keys.RETURN)

        # Buscando Solucion
        elementoActivo, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Solución')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        solucion = driver.find_element(By.XPATH, "//input[@aria-label='Solución']")
        solucion.send_keys(Solucion)
        solucion.send_keys(Keys.RETURN)

        # PAGO CON PROMOCION
        # PAGO COMPLETO

        # Buscando Comentario
        elementoActivo, resultado = cargandoElemento(driver, 'textarea', 'aria-label', 'Comentarios')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        comentarios = driver.find_element(By.XPATH, "//textarea[@aria-label='Comentarios']")
        comentarios.send_keys(Comentario)

        # Buscando Motivo Cierre
        elementoActivo, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Motivo del Cierre')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        motivoCierre = driver.find_element(By.XPATH, "//input[@aria-label='Motivo del Cierre']")
        motivoCierre.send_keys(MoCierre)
        motivoCierre.send_keys(Keys.RETURN)

        # Obtencion de CN Generado
        cnGenerado = driver.find_element(By.XPATH, "//a[@name='SRNumber']")
        cnGenerado = driver.execute_script("return arguments[0].textContent;", cnGenerado)
        print(f'→ CN Generado: {cnGenerado}')

        # Buscando Estado CN

        # motivoCliente = driver.find_element(By.XPATH, "//input[@aria-label='Motivo Cliente']")
        # motivoCliente.send_keys(MoCliente)
        # motivoCliente.send_keys(Keys.RETURN)

        try:

            driver.find_element(By.XPATH, pathEstadoCN).click()
            sleep(2)
            driver.find_element(By.XPATH, pathPickListEstadoCN).click()
            sleep(5)
            driver.find_element(By.XPATH, pathOpcCerradoCN).click()
            sleep(5)
        
        except Exception as e: 
            lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'a', 'title', 'Pantalla Única de Consulta')
            if lupa_busqueda_cuenta == False: 
                if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
    

        # Guardar CN
        elementoActivo, resultado = cargandoElemento(driver, 'button', 'aria-label', 'Casos de negocio Applet de formulario:Guardar')
        if elementoActivo == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        print('→ Fin Creacion CN')
        sleep(10)
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'a', 'title', 'Pantalla Única de Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
    
        return True, 'Completado', cnGenerado

    except Exception as e: 
        print(e)
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'a', 'title', 'Pantalla Única de Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
    
        
           


def manejar_serial(driver, cuenta,serial):

    try:

        pathEstadoCN = '/html/body/div[1]/div/div[5]/div/div[8]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div/div/form/div/span/div[3]/div/div/table/tbody/tr[4]/td[5]'
        pathPickListEstadoCN = '/html/body/div[1]/div/div[5]/div/div[8]/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div/div/form/div/span/div[3]/div/div/table/tbody/tr[4]/td[5]/div/span'
        pathOpcCerradoCN = '/html/body/div[1]/div/div[5]/div/div[8]/ul[16]/li[7]/div'

        
        print('→ Buscando Cuenta')

        # Pantalla Consulta (Click)
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'a', 'title', 'Pantalla Única de Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        # Buscando Elemento
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'button', 'title', 'Pantalla Única de Consulta Applet de formulario:Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        
        lupa_busqueda_cn, resultado = cargandoElemento(driver, 'input', 'aria-label', 'Numero Cuenta')
        if lupa_busqueda_cn == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        # Ingreso Cuenta
        input_busqueda_cuenta = driver.find_element(By.XPATH, "//input[@aria-label='Numero Cuenta']")
        input_busqueda_cuenta.send_keys(cuenta)
        input_busqueda_cuenta.send_keys(Keys.RETURN)
        print('♦ Cuenta Ingresada ♦')

        # Cargando Cuenta
        cargaPantalla, resultado = cargandoElemento(driver, '', '', '', path= "//*[contains(@aria-label,'SALDO VENCIDO')]")
        if cargaPantalla == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'
        print('♥ Cuenta OK! ♥')

        # Inicio de Generacion CN
        # Buscando Creacion CN
        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'button', 'title', 'Ítems de Servicio Applet de lista:Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        acciones = ActionChains(driver)

        for _ in range(2):
            acciones.send_keys(Keys.TAB)
        acciones.perform()

        acciones.send_keys(serial)
        sleep(2)
        acciones.send_keys(Keys.ENTER)
        sleep(2)
        acciones.perform()

        serie_elem = driver.find_element(By.XPATH, "//*[@id='1_Serial_Number']")
        serie = serie_elem.get_attribute("value")
        print(f'→ Serie: {serie}')

        if not serie:
            print("→ Serie: El numero de serie es incorrecto")
            return False ,'Numero de Serie Incorrecto' , 'Numero de Serie Incorrecto' 



        sleep(2)

        for _ in range(2):
            acciones.key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT)
        sleep(2)

        #acciones.send_keys(Keys.SPACE)
        sleep(2)
        acciones.perform()

        sleep(3)

        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'button', 'title', 'Ítems de Servicio Applet de lista:Comando')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, 'Error al enviar comando'
        
        # try:
        #     sleep(5)
        #     #Alerta por prueba
        #     alert = driver.switch_to.alert
        #     # 5a. Para ACEPTAR la alerta (equivale a hacer clic en “Aceptar”)
        #     alert.accept()
        # except Exception as e:
        #     print("alerta no disponible")

        intentos = validar_elemento_presentes(driver,"/html/body/div[22]/div[2]/div/div/div/form/div/div[1]/div/div/div[3]/div[2]/div/table/thead/tr/th[2]/div")
        if intentos< 5:
            print("bucando reiniciar")
            try:
                wait = WebDriverWait(driver, 10)
                celda_reiniciar = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[22]/div[2]/div/div/div/form/div/div[1]/div/div/div[3]/div[3]/div/div[2]/table/tbody/tr[5]/td[2]")
                ))
                
                celda_reiniciar.click()
                sleep(3)
            except Exception as e:
                print(f"error al buscar comando {e}")
                return False, resultado, '-'
        else:
            return False, resultado, '-'

        try:
            print("bucando aceptar")
            wait = WebDriverWait(driver, 10)
            botno_Aceptar = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[22]/div[2]/div/div/div/form/div/div[2]/span[1]/button")))
            botno_Aceptar.click()
            sleep(3)
        except Exception as e:
            print(f"error en aceptar {e}")
            return False, resultado, '-'

        lupa_busqueda_cuenta, resultado = cargandoElemento(driver, 'a', 'title', 'Pantalla Única de Consulta')
        if lupa_busqueda_cuenta == False: 
            if resultado == 'elemento no carga': resultado = 'Registro Pendiente'
            return False, resultado, '-'

        sleep(10)

        


        return True, 'Completado', 'Refres Modem Enviado'

    except Exception as e: print(e); return False, 'Error Generar Reset', '-'