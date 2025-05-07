import socket
import threading
import json

class ReceptorUDP(threading.Thread):
    def __init__(self, armazenamento_compartilhado, ip_escuta="0.0.0.0", porta=5005):
        super().__init__(daemon=True)
        self.armazenamento = armazenamento_compartilhado
        self.ip_escuta = ip_escuta
        self.porta = porta
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip_escuta, self.porta))

    def run(self):
        print("Thread 1 (Receptor UDP) iniciada.")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                mensagem = json.loads(data.decode("utf-8"))

                cod = mensagem.get("codErro")
                if cod in self.armazenamento:
                    self.armazenamento[cod].append(mensagem)
                    print(f"Recebido de {addr}: {mensagem}")
                else:
                    print(f"CodErro inválido ou fora do esperado: {cod}")

            except Exception as e:
                print(f"Erro no recebimento UDP: {e}")
