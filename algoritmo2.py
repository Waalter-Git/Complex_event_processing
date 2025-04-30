from sklearn.cluster import DBSCAN
import numpy as np

# Suponha que você tenha os pontos de queda de energia (lat/lon)
quedas = np.array([
    [-23.5505, -46.6333],
    [-23.5506, -46.6332],
    [-23.5510, -46.6330],
    [-23.5800, -46.6400],  # Queda isolada
    [-23.5801, -46.6402],
    # ... pode ser milhares
])

# Converte graus para radianos (requisito da métrica haversine)
quedas_rad = np.radians(quedas)

# Raio máximo entre pontos vizinhos (em radianos)
# Exemplo: 300 metros = 300 / 6371000
eps = 300 / 6371000

# Aplica DBSCAN
db = DBSCAN(eps=eps, min_samples=3, metric='haversine')
labels = db.fit_predict(quedas_rad)

# Resultado:
for i, label in enumerate(labels):
    print(f"Ponto {quedas[i]} pertence ao cluster {label}")
