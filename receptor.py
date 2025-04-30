import socket
import json

# Configuração do IP e porta para escutar
BROADCAST_IP = '192.168.56.255'
PORT = 5005

# Criação do socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Vincula o socket ao IP e porta
sock.bind(('', PORT))

print(f"Escutando mensagens no IP {BROADCAST_IP} e porta {PORT}...")

# Dicionário para armazenar os dados recebidos
quedas = {}
contador = 0

while True:
    # Recebe dados (tamanho máximo de 1024 bytes)
    data, addr = sock.recvfrom(1024)
    
    try:
        # Decodifica a mensagem JSON
        message = json.loads(data.decode('utf-8'))
        latitude = message.get("latitude")
        longitude = message.get("longitude")
        timestamp = message.get("timestamp")
        
        # Armazena os dados no dicionário
        quedas[contador] = {
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp
        }
        contador += 1
        
        # Exibe os dados recebidos
        print(f"Mensagem recebida de {addr}:")
        print(f"  Latitude: {latitude}")
        print(f"  Longitude: {longitude}")
        print(f"  Timestamp: {timestamp}")
        print(f"Dados armazenados no dicionário: {quedas[contador - 1]}")
    except json.JSONDecodeError:
        print("Erro ao decodificar a mensagem JSON.")
