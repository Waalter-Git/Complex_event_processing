import random
import json
import socket
import time

def enviar_pacotes_udp(qtd_total=300000, qtd_agrupamentos=1, dispersao=0.003, destino_ip="127.0.0.1", destino_porta=5005):
    """
    Simula o envio de pacotes UDP com eventos agrupados e ruído, em formato JSON.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    eventos = []

    # Geração dos agrupamentos (clusters)
    for _ in range(qtd_agrupamentos):
        base_lat = random.uniform(-90, 90)
        base_lon = random.uniform(-180, 180)
        for _ in range(600):
            evento = {
                "latitude": base_lat + random.uniform(-dispersao, dispersao),
                "longitude": base_lon + random.uniform(-dispersao, dispersao),
                "codErro": 2
            }
            eventos.append(evento)

    # Geração dos eventos de ruído (noise)
    resto = qtd_total - len(eventos)
    for _ in range(resto):
        ruido = {
            "latitude": random.uniform(-90, 90),
            "longitude": random.uniform(-180, 180),
            "codErro": random.randint(0, 4)
        }
        eventos.append(ruido)

    random.shuffle(eventos)

    # Envio dos pacotes
    for evento in eventos:
        pacote = json.dumps(evento).encode("utf-8")
        udp_socket.sendto(pacote, (destino_ip, destino_porta))

    udp_socket.close()
    return eventos

if __name__ == "__main__":
    enviar_pacotes_udp()