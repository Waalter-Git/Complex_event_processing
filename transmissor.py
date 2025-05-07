import json
import socket
import random
import time
import threading

BROADCAST_IP = '127.0.0.1'
PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

causas = ["altaTensao", "variaFreq", "subTensao", "quedaEnergia"]
base_lat = random.uniform(30, 40)
base_lon = random.uniform(30, 40)

total_pacotes = 300000
enviados = 0

variaF = 0
sobT = 0
queda = 0
altaT = 0
quantidadeR = 0

lock = threading.Lock()

def enviar_dados():
    global enviados, altaT, variaF, sobT, queda, quantidadeR

    while enviados < total_pacotes:
        num_eventos = random.choices([0, 1, 2], weights=[0.4, 0.4, 0.2])[0]
        causa_evento = random.choice(causas)
        codErro_evento = causas.index(causa_evento) + 1

        for _ in range(num_eventos):
            if enviados >= total_pacotes:
                break
            lat = base_lat + random.uniform(-0.0002, 0.0002)
            lon = base_lon + random.uniform(-0.0002, 0.0002)

            if causa_evento == "altaTensao":
                altaT += 1
            elif causa_evento == "variaFreq":
                variaF += 1
            elif causa_evento == "subTensao":
                sobT += 1
            elif causa_evento == "quedaEnergia":
                queda += 1

            msg = {
                "latitude": lat,
                "longitude": lon,
                "codErro": codErro_evento,
                "causa": causa_evento
            }

            with lock:
                sock.sendto(json.dumps(msg).encode('utf-8'), (BROADCAST_IP, PORT))
                print(f"Enviado (evento): {msg}")
                enviados += 1

        if enviados < total_pacotes:
            ruido_tipo = random.choices(["normal", "evento_distante"], weights=[0.93, 0.07])[0]
            if ruido_tipo == "normal":
                lat = base_lat + random.uniform(-0.005, 0.005)
                lon = base_lon + random.uniform(-0.005, 0.005)
                msg = {
                    "latitude": lat,
                    "longitude": lon,
                    "codErro": 0,
                    "causa": None
                }
                print(f"Enviado (ruído normal): {msg}")
            else:
                causa_ruido = random.choice(causas)
                codErro_ruido = causas.index(causa_ruido) + 1
                lat = base_lat + random.uniform(0.1, 0.5)
                lon = base_lon + random.uniform(0.1, 0.5)
                msg = {
                    "latitude": lat,
                    "longitude": lon,
                    "codErro": codErro_ruido,
                    "causa": causa_ruido                }
                print(f"Enviado (ruído evento distante): {msg}")
                quantidadeR += 1

            with lock:
                sock.sendto(json.dumps(msg).encode('utf-8'), (BROADCAST_IP, PORT))
                enviados += 1

    print("Transmissão concluída.")
    print(f"Alta Tensão: {altaT}, Variação de Frequência: {variaF}, Subtensão: {sobT}, Queda: {queda}")
    print("Total de pacotes enviados:", enviados)
    print("Ruído evento distante:", quantidadeR)

if __name__ == "__main__":
    transmissor_thread = threading.Thread(target=enviar_dados)
    transmissor_thread.start()
