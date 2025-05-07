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
        for cod in [1, 2, 3, 4]:  # codErro válidos
            eventos_cod = [d for d in self.armazenamento if d.get("codErro") == cod]
            if len(eventos_cod) < 3:
                continue

            pontos = np.array([[e["latitude"], e["longitude"]] for e in eventos_cod])
            pontos_rad = np.radians(pontos)

            db = DBSCAN(
                eps=300 / 6371000,
                min_samples=20,
                metric='haversine'
            )
            labels = db.fit_predict(pontos_rad)

            clusters = {}
            for i, label in enumerate(labels):
                if label == -1:
                    continue
                clusters.setdefault(label, []).append(pontos[i])

            for cluster_id, cluster in clusters.items():
                media = np.mean(cluster, axis=0)
                alarme = {
                    "eventoID": f"cluster_{cod}_{cluster_id}",
                    "codErro": cod,
                    "causa": eventos_cod[0].get("causa", "descohecida"),
                    "timestamp": datetime.now().isoformat(),
                    "numero_eventos": len(cluster),
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
