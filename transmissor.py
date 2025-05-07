import json
import socket
import random
import time
import threading

BROADCAST_IP = '192.168.56.255'  # ajuste se necessário
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

causas = ["altaTensao", "variaFreq", "subTensao", "quedaEnergia"]
base_lat = -18.91
base_lon = -48.26

total_pacotes = 3000
pacotes_enviados = 0
lock = threading.Lock()

def enviar_evento(causa, codErro, lat, lon):
    global pacotes_enviados
    msg = {
        "latitude": lat,
        "longitude": lon,
        "codErro": codErro,
        "causa": causa
    }
    sock.sendto(json.dumps(msg).encode('utf-8'), (BROADCAST_IP, PORT))
    with lock:
        pacotes_enviados += 1
        print(f"Enviado: {msg}")

def simulador_de_eventos():
    global pacotes_enviados
    while pacotes_enviados < total_pacotes:
        num_eventos = random.choices([0, 1, 2], weights=[0.4, 0.4, 0.2])[0]

        causa_evento = random.choice(causas)
        codErro_evento = causas.index(causa_evento) + 1

        for _ in range(num_eventos):
            if pacotes_enviados >= total_pacotes:
                return
            lat = base_lat + random.uniform(-0.0002, 0.0002)
            lon = base_lon + random.uniform(-0.0002, 0.0002)
            threading.Thread(target=enviar_evento, args=(causa_evento, codErro_evento, lat, lon)).start()
            time.sleep(0.01)

        # Ruído normal ou distante
        if pacotes_enviados < total_pacotes:
            tipo = random.choices(["normal", "evento_distante"], weights=[0.93, 0.07])[0]
            if tipo == "normal":
                lat = base_lat + random.uniform(-0.005, 0.005)
                lon = base_lon + random.uniform(-0.005, 0.005)
                causa = None
                codErro = 0
            else:
                causa = random.choice(causas)
                codErro = causas.index(causa) + 1
                lat = base_lat + random.uniform(0.1, 0.5)
                lon = base_lon + random.uniform(0.1, 0.5)

            threading.Thread(target=enviar_evento, args=(causa, codErro, lat, lon)).start()
            time.sleep(0.01)

if __name__ == "__main__":
    print("Iniciando transmissor com threads...")
    simulador_de_eventos()
    print("Transmissão finalizada.")
