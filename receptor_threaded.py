
import threading
import socket
import json

class ReceptorUDP(threading.Thread):
    def __init__(self, armazenamento_compartilhado, porta=5005):
        super().__init__(daemon=True)
        self.armazenamento = armazenamento_compartilhado
        self.porta = porta

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.porta))
        print(f"Thread 1 (UDP) escutando na porta {self.porta}...")

        contador = 0
        while True:
            data, _ = sock.recvfrom(1024)
            try:
                mensagem = json.loads(data.decode('utf-8'))
                if 'Lat' in mensagem and 'Long' in mensagem:
                    self.armazenamento.append({
                        "id": contador,
                        "latitude": mensagem["Lat"],
                        "longitude": mensagem["Long"],
                        "codErro": mensagem.get("codErro", None)
                    })
                    contador += 1
            except json.JSONDecodeError:
                continue
