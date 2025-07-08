from json.decoder import JSONDecodeError
import requests
import json
from time import sleep
import socket

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)


url = 'https://rpabackizzi.azurewebsites.net/AgenciasExternas/getCuentaCreacionCNs'
urlUpdate = 'https://rpabackizzi.azurewebsites.net/AgenciasExternas/ActualizaCreacionCNs'
urlPassUser = f'https://rpabackizzi.azurewebsites.net/Bots/getProcess?ip={str(ip)}'

def get_orden_servicio():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            responseApi = json.loads(response.text)
            print('API CORRECTA')
            print(responseApi)
            return responseApi
        elif response.status_code == 401: return print("Anauthorized")
        elif response.status_code == 404: return print("Not Found")
        elif response.status_code == 500: return print("Internal Server Error")
        
    except JSONDecodeError: return response.body_not_json

def get_orden_servicio2():
    try:
        response = requests.get(urlPassUser)
        if response.status_code == 200:
            responseApi = json.loads(response.text)
            print('API CORRECTA')
            print(responseApi)
            return responseApi
        elif response.status_code == 401: return print("Anauthorized")
        elif response.status_code == 404: return print("Not Found")
        elif response.status_code == 500: return print("Internal Server Error")
        
    except JSONDecodeError: return response.body_not_json

def update(datos, parametros):

    try:
        response = requests.put(urlUpdate, params=parametros, json=datos)
        if response.status_code == 200:
            responseApi = json.loads(response.text)
            print('ACTUALIZADO')
            return responseApi
        
        elif response.status_code == 401: return print("Anauthorized")
        elif response.status_code == 404: return print("Not Found")
        elif response.status_code == 500: return print("Internal Server Error")

    except JSONDecodeError: return response.body_not_json


def ajusteCerrado(id, cnGenerado, fechaCaptura, fechaCompletado, status, cve_usuario, ip, cuenta, fechaSubida, categoria, mootivo, subMotivo, solucion, saldoIncobrable, promocion, ajuste, fechaGestion, tipo):
    datos = {
        'id' : id,
        'cnGenerado' : cnGenerado,
        'fechaCaptura' : fechaCaptura,
        'fechaCompletado' : fechaCompletado,
        'status' : status,
        'cve_usuario' : cve_usuario,
        'ip' : ip,
        'cuenta' : cuenta,
        'fechaSubida' : fechaSubida,
        'categoria' : categoria,
        'mootivo' : mootivo,
        'subMotivo' : subMotivo,
        'solucion' : solucion,
        'saldoIncobrable' : saldoIncobrable,
        'promocion' : promocion,
        'ajuste' : ajuste,
        'fechaGestion' : fechaGestion,
        'tipo' : tipo
    }

    parametros = { 'id' : id }
    return update(datos, parametros)

# p = get_orden_servicio()
# print(p)