# sender.py
import json
import socket
import random
import time
from typing import Dict

# Broadcast IP and UDP port configuration
BROADCAST_IP = '192.168.56.255'
PORT = 5005


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

for i in range(20):

    valorasomar = 0

    if(i < 3):
        valorasomar = random.uniform(10, -10)/5000
    else:
        valorasomar = random.uniform(10, -10)/50
    
    latitude = -18.919463 + valorasomar
    longitude = -48.259267 + valorasomar

    message = json.dumps({
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": time.time()
    }).encode('utf-8')

    sock.sendto(message, (BROADCAST_IP, PORT))
    print(f"Mensagem enviada: {message.decode('utf-8')}")

