from sklearn.neighbors import BallTree
import numpy as np
import math

# Convert graus para radianos
def deg2rad(lat_lon):
    return np.radians(lat_lon)

# Base de casas: lista de [lat, lon]
casas = np.array([
    [-23.5505, -46.6333],
    [-23.5506, -46.6332],
    [-23.5510, -46.6330],
    # ... até 300.000
])
casas_rad = deg2rad(casas)

# Cria a árvore espacial usando a métrica Haversine
tree = BallTree(casas_rad, metric='haversine')

# Evento de queda de energia (lat, lon)
evento = [-23.55055, -46.63325]
evento_rad = np.radians([evento])

# Define o raio de interesse (ex: 500 metros)
raio_metros = 500
raio_rad = raio_metros / 6371000  # Converte para radianos

# Consulta: retorna índices das casas afetadas
indices_afetados = tree.query_radius(evento_rad, r=raio_rad)[0]

# Resultado
casas_afetadas = casas[indices_afetados]
print(f"{len(casas_afetadas)} casas afetadas:\n", casas_afetadas)
