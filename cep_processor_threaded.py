import json
import numpy as np
import socket
import threading
import time
from datetime import datetime
from sklearn.cluster import DBSCAN
from receptor_threaded import ReceptorUDP

class CEPProcessor(threading.Thread):
    def __init__(self, armazenamento_compartilhado, ip_destino="127.0.0.1", porta_destino=6006):
        super().__init__(daemon=True)
        self.armazenamento = armazenamento_compartilhado  # Lista de eventos recebidos via UDP
        self.ip_destino = ip_destino                      # IP para envio dos alarmes
        self.porta_destino = porta_destino                # Porta para envio dos alarmes

    def run(self):
        print("Thread 2 (CEP Processor) iniciada.")
        while True:
            self.processar()       # Chama a função para processar eventos periodicamente
            time.sleep(10)         # Aguarda 10 segundos antes de nova verificação

    def processar(self):
        # Filtra somente eventos de queda (codErro == 95)
        eventos = [d for d in self.armazenamento if d.get("codErro") == 95]

        # Ignora processamento caso existam poucos eventos
        if len(eventos) < 3:
            return

        # Extrai latitude e longitude dos eventos
        pontos = np.array([[e["latitude"], e["longitude"]] for e in eventos])

        # Converte coordenadas para radianos para cálculo geográfico
        pontos_rad = np.radians(pontos)

        # Executa DBSCAN para encontrar aglomerações de eventos (clusters)
        db = DBSCAN(
            eps=300 / 6371000,     # Raio de 300 metros (em radianos)
            min_samples=20,        # Mínimo de 20 eventos para formar cluster
            metric='haversine'     # Usa métrica geográfica (haversine)
        )
        labels = db.fit_predict(pontos_rad)  # Identifica clusters

        clusters = {}  # Armazena clusters válidos encontrados
        for i, label in enumerate(labels):
            if label == -1:
                continue  # Ignora pontos classificados como ruído
            clusters.setdefault(label, []).append(pontos[i])

        # Caso nenhum cluster válido seja identificado, gera alarme único
        if not clusters:
            media = np.mean(pontos, axis=0)  # Localização média dos eventos
            alarme = {
                "eventoID": "cluster_unico",
                "timestamp": datetime.now().isoformat(),
                "numero_quedas": len(pontos),
                "localizacao_media": {
                    "latitude": float(media[0]),
                    "longitude": float(media[1])
                }
            }
            self.enviar_tcp(alarme)  # Envia alarme com todos os pontos
            return

        # Caso contrário, envia um alarme separado para cada cluster identificado
        for cluster_id, cluster in clusters.items():
            media = np.mean(cluster, axis=0)  # Localização média do cluster atual
            alarme = {
                "eventoID": f"cluster_{cluster_id}",
                "timestamp": datetime.now().isoformat(),
                "numero_quedas": len(cluster),
                "localizacao_media": {
                    "latitude": float(media[0]),
                    "longitude": float(media[1])
                }
            }
            self.enviar_tcp(alarme)  # Envia alarme do cluster atual

    def enviar_tcp(self, alarme):
        # Envia o alarme via conexão TCP para o destino especificado
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip_destino, self.porta_destino))      # Estabelece conexão TCP
                s.sendall(json.dumps(alarme).encode("utf-8"))         # Envia dados em JSON
                print(f"Alarme enviado: {alarme}")
        except Exception as e:
            print(f"Erro ao enviar alarme via TCP: {e}")

if __name__ == "__main__":
    armazenamento = []                     # Lista compartilhada entre threads
    receptor = ReceptorUDP(armazenamento)  # Thread que preenche 'armazenamento' com eventos UDP
    cep = CEPProcessor(armazenamento)      # Thread que processa eventos e gera alarmes

    receptor.start()  # Inicia escuta UDP
    cep.start()       # Inicia processamento CEP

    try:
        while True:
            time.sleep(1)  # Mantém script ativo até interrupção
    except KeyboardInterrupt:
        print("Encerrando threads...")
