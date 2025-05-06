
import socket
import json
import time
import random

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(100):  # Envia 100 pacotes simulados
    mensagem = {
        "Lat": -18.91 + random.uniform(-0.01, 0.01),
        "Long": -48.26 + random.uniform(-0.01, 0.01),
        "codErro": 95 if random.random() < 0.7 else 12
    }
    sock.sendto(json.dumps(mensagem).encode("utf-8"), (UDP_IP, UDP_PORT))
    print(f"Enviado: {mensagem}")
    time.sleep(0.1)
