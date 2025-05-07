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
        self.armazenamento = armazenamento_compartilhado
        self.ip_destino = ip_destino
        self.porta_destino = porta_destino

    def run(self):
        print("Thread 2 (CEP Processor) iniciada.")
        while True:
            self.processar()
            time.sleep(10)

    def processar(self):
        # Filtra somente eventos de queda (codErro == 95)
        eventos = [d for d in self.armazenamento if d.get("codErro") == 95]

        # Ignora processamento caso existam poucos eventos
        if len(eventos) < 3:
            return

        # Extrai latitude e longitude dos eventos
        pontos = np.array([[e["latitude"], e["longitude"]] for e in eventos])
        pontos_rad = np.radians(pontos)

        # Executa DBSCAN para encontrar aglomerações de eventos (clusters)
        db = DBSCAN(
            eps=300 / 6371000,
            min_samples=20,
            metric='haversine'
        )
        labels = db.fit_predict(pontos_rad)

        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:
                continue  # Ignora pontos classificados como ruído
            clusters.setdefault(label, []).append(pontos[i])

        # Se nenhum cluster válido for formado, não faz nada
        if not clusters:
            return

        # Envia um alarme para cada cluster formado
        for cluster_id, cluster in clusters.items():
            media = np.mean(cluster, axis=0)
            alarme = {
                "eventoID": f"cluster_{cluster_id}",
                "timestamp": datetime.now().isoformat(),
                "numero_quedas": len(cluster),
                "localizacao_media": {
                    "latitude": float(media[0]),
                    "longitude": float(media[1])
                }
            }
            self.enviar_tcp(alarme)

    def enviar_tcp(self, alarme):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip_destino, self.porta_destino))
                s.sendall(json.dumps(alarme).encode("utf-8"))
                print(f"Alarme enviado: {alarme}")
        except Exception as e:
            print(f"Erro ao enviar alarme via TCP: {e}")

if __name__ == "__main__":
    armazenamento = []
    receptor = ReceptorUDP(armazenamento)
    cep = CEPProcessor(armazenamento)

    receptor.start()
    cep.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando threads...")
