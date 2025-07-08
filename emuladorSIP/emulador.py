import asyncio
import aiosip
import json

# Cargar configuración SIP desde config.json
with open('config.json') as f:
    config = json.load(f)

USERNAME = config["extension"]
PASSWORD = config["password"]
SERVER_IP = config["ip"]
SERVER_PORT = 5060
LOCAL_IP = '0.0.0.0'
LOCAL_PORT = 5062  # puerto local donde escucha este cliente

async def on_invite(request, message):
    print(f"📞 Llamada entrante de: {message.headers['From']}")
    dialog = await request.prepare(status_code=180)  # Ringing
    await asyncio.sleep(1)
    await dialog.reply(200)  # Contestar con 200 OK
    print("✅ Llamada contestada (200 OK)")
    # Aquí puedes agregar lógica de audio más adelante

async def main():
    loop = asyncio.get_event_loop()

    app = await aiosip.Application(loop=loop).run(
        local_addr=(LOCAL_IP, LOCAL_PORT)
    )

    # Registrar el INVITE listener
    invite_server = await app.listen(
        protocol=aiosip.Protocol.UDP,
        from_uri=f'sip:{USERNAME}@{SERVER_IP}',
        password=PASSWORD,
        callback=on_invite
    )

    print("📡 Registrando con el servidor SIP...")

    contact_uri = f'sip:{USERNAME}@{LOCAL_IP}:{LOCAL_PORT}'
    async with app.connect(
        protocol=aiosip.Protocol.UDP,
        remote_addr=(SERVER_IP, SERVER_PORT),
        from_uri=f'sip:{USERNAME}@{SERVER_IP}',
        to_uri=f'sip:{SERVER_IP}',
        contact_uri=contact_uri,
        password=PASSWORD
    ) as dialog:
        print("✅ Registrado correctamente en el servidor SIP.")
        while True:
            await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Finalizando cliente SIP...")
