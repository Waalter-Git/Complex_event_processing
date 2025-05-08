# Importação de bibliotecas necessárias
import tkinter as tk
import customtkinter as ctk  # Biblioteca de UI customizada
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import socket
import threading
import json
import time
import numpy as np
from datetime import datetime
from sklearn.cluster import DBSCAN
import subprocess
import sys

# Configuração do socket para envio de alarmes via UDP
ALARMES_DEST_IP = "10.14.100.224"
ALARMES_DEST_PORT = 12345
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Configurações do receptor UDP
PORT = 5005
HOST = "0.0.0.0"

# Variáveis globais para armazenamento de dados e controle
armazenamento_compartilhado = []           # Armazena os dados recebidos via UDP
logs = []                                  # Registra logs de eventos e alarmes
ultimos_alarmes = []                       # Armazena os últimos alarmes exibidos
alarme_enviado_por_cluster = {}            # Impede reenvio de alarmes duplicados no mesmo minuto

# Códigos e cores associadas aos tipos de erro
causas = ["altaTensao", "variaFreq", "subTensao", "quedaEnergia"]
tipo_cores = {
    "altaTensao": "red",
    "variaFreq": "blue",
    "subTensao": "gold",
    "quedaEnergia": "green"
}

# ========================
# Função receptora de dados via UDP
# ========================
def receptor_udp(interface):
    sock.bind((HOST, PORT))  # Liga o socket à porta
    interface.udp_ativo.set(True)
    while interface.monitorando:
        try:
            data, _ = sock.recvfrom(1024)  # Recebe pacote UDP
            msg = json.loads(data.decode('utf-8'))  # Decodifica JSON
            armazenamento_compartilhado.append(msg)  # Armazena o evento recebido
        except:
            continue
    interface.udp_ativo.set(False)

# ========================
# Thread responsável por processar os dados recebidos
# ========================
class CEPProcessor(threading.Thread):
    def __init__(self, interface):
        super().__init__(daemon=True)
        self.interface = interface

    def run(self):
        self.interface.cep_ativo.set(True)
        while self.interface.monitorando:
            self.processar()
            time.sleep(5)  # Processamento a cada 5 segundos
        self.interface.cep_ativo.set(False)

    # Processamento dos dados para identificar clusters e gerar alarmes
    def processar(self):
        eventos = [d for d in armazenamento_compartilhado if d.get("codErro") in [2]]
        if len(eventos) < 2:
            return

        # Cria os agrupamentos com DBSCAN
        coords = np.array([[e["latitude"], e["longitude"]] for e in eventos])
        clustering = DBSCAN(eps=0.1, min_samples=15).fit(coords)
        labels = clustering.labels_

        # Processa cada cluster detectado
        for i in set(labels):
            if i == -1:
                continue  # Ignora ruídos

            cluster_indices = np.where(labels == i)[0]
            cluster_eventos = [eventos[idx] for idx in cluster_indices]
            tipo_erro = cluster_eventos[0].get("codErro")
            causa = causas[tipo_erro - 1]
            horario = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Garante que o alarme seja enviado apenas uma vez por minuto por cluster
            chave_cluster = f"{i}_{horario}"
            if chave_cluster in alarme_enviado_por_cluster:
                continue

            # Atualiza lista de alarmes e log
            texto = f"Cluster_{i} – {len(cluster_eventos)} eventos\n{horario}"
            ultimos_alarmes.insert(0, texto)
            logs.append(f"[{horario}] Alarme gerado ({causa}): Cluster_{i}")
            if len(ultimos_alarmes) > 1:
                ultimos_alarmes.pop()

            # Prepara os dados do alarme
            alarme_data = {
                "URI": "102",
                "alarme": True,
                "codErro": tipo_erro,
                "causa": causa,
                "cluster": i,
                "quantidadeEventos": len(cluster_eventos),
                "timestamp": horario
            }

            print(f"[DEBUG] Preparando envio do alarme do Cluster {i}")

            # Marca que esse cluster já foi enviado neste minuto e dispara envio
            alarme_enviado_por_cluster[chave_cluster] = True
            self.enviar_alarme_em_thread(alarme_data)

        # Atualiza interface com alarmes, log e gráfico
        self.interface.update_alarmes()
        self.interface.update_log()
        self.interface.update_grafico()

    # Envia o alarme em uma thread separada
    def enviar_alarme_em_thread(self, dados):
        def envio():
            try:
                print(f"[ENVIANDO ALARME UDP] Cluster {dados['cluster']} - {dados['causa']}")
                dados_serializaveis = {k: int(v) if isinstance(v, np.integer) else v for k, v in dados.items()}
                sock.sendto(json.dumps(dados_serializaveis).encode("utf-8"), (ALARMES_DEST_IP, ALARMES_DEST_PORT))
                print("[ALARME ENVIADO COM SUCESSO]")
            except Exception as e:
                print(f"[ERRO NO ENVIO DE ALARME] {e}")
        threading.Thread(target=envio, daemon=True).start()

# ========================
# Classe da interface gráfica principal
# ========================
class InterfaceMonitoramento(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monitoramento de Quedas - Módulo 5b")
        self.geometry("1050x650")
        self.monitorando = False
        ctk.set_appearance_mode("light")

        self.udp_ativo = tk.BooleanVar(value=False)
        self.cep_ativo = tk.BooleanVar(value=False)

        self.init_ui()

    # Monta todos os elementos da interface
    def init_ui(self):
        # Título da janela
        titulo = ctk.CTkLabel(self, text="Monitoramento de Quedas", font=("Arial", 24, "bold"))
        titulo.pack(pady=(10, 5))

        # Painel de status (UDP/CEP)
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(pady=5)

        self.udp_check = ctk.CTkCheckBox(status_frame, text="UDP Ativo", variable=self.udp_ativo, state="disabled")
        self.udp_check.grid(row=0, column=0, padx=10)

        self.cep_check = ctk.CTkCheckBox(status_frame, text="CEP Ativo", variable=self.cep_ativo, state="disabled")
        self.cep_check.grid(row=0, column=1, padx=10)

        self.contador_label = ctk.CTkLabel(status_frame, text="Eventos Recebidos: 0", font=("Arial", 14))
        self.contador_label.grid(row=0, column=2, padx=20)

        # Container principal
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # Painel esquerdo (alarmes e log)
        painel_esquerdo = ctk.CTkFrame(container, width=300)
        painel_esquerdo.pack(side="left", fill="y", padx=10, pady=10)

        self.alarmes_label = ctk.CTkLabel(painel_esquerdo, text="Últimos Alarmes", font=("Arial", 16))
        self.alarmes_label.pack(pady=5)

        self.texto_alarme = ctk.CTkTextbox(painel_esquerdo, width=280, height=100)
        self.texto_alarme.pack(pady=5)

        self.log_label = ctk.CTkLabel(painel_esquerdo, text="Log", font=("Arial", 16))
        self.log_label.pack(pady=5)

        self.texto_log = ctk.CTkTextbox(painel_esquerdo, width=280, height=200)
        self.texto_log.pack(pady=5)

        # Painel direito (gráfico)
        painel_direito = ctk.CTkFrame(container)
        painel_direito.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Gráfico de Quedas")
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")

        self.canvas = FigureCanvasTkAgg(self.fig, master=painel_direito)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Botão de encerrar
        self.botao_finalizar = ctk.CTkButton(self, text="Encerrar Monitoramento", command=self.encerrar_monitoramento)
        self.botao_finalizar.pack(pady=10)

        self.iniciar_monitoramento()

    # Inicia os threads de monitoramento e CEP
    def iniciar_monitoramento(self):
        self.monitorando = True
        threading.Thread(target=receptor_udp, args=(self,), daemon=True).start()
        threading.Thread(target=self.rodar_transmissor, daemon=True).start()
        CEPProcessor(interface=self).start()
        threading.Thread(target=self.atualizar_contador, daemon=True).start()

    # Encerra o monitoramento e fecha a janela
    def encerrar_monitoramento(self):
        self.monitorando = False
        self.destroy()

    # Inicia o processo que gera os eventos (novoMuckup.py)
    def rodar_transmissor(self):
        subprocess.Popen([sys.executable, "novoMuckup.py"])

    # Atualiza o contador de eventos recebidos
    def atualizar_contador(self):
        while self.monitorando:
            self.contador_label.configure(text=f"Eventos Recebidos: {len(armazenamento_compartilhado)}")
            time.sleep(0.001)

    # Atualiza a área de alarmes
    def update_alarmes(self):
        self.texto_alarme.configure(state="normal")
        self.texto_alarme.delete("1.0", "end")
        for item in ultimos_alarmes:
            self.texto_alarme.insert("end", item + "\n")
        self.texto_alarme.configure(state="disabled")

    # Atualiza a área de log
    def update_log(self):
        self.texto_log.configure(state="normal")
        self.texto_log.delete("1.0", "end")
        for item in logs[-20:]:
            self.texto_log.insert("end", item + "\n")
        self.texto_log.configure(state="disabled")

    # Atualiza o gráfico com base nos eventos atuais
    def update_grafico(self):
        self.ax.clear()
        self.ax.set_title("Gráfico de Quedas")
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")

        eventos_por_tipo = {tipo: [] for tipo in tipo_cores}

        for d in armazenamento_compartilhado:
            cod = d.get("codErro")
            if cod in [1, 2, 3, 4]:
                causa = causas[cod - 1]
                eventos_por_tipo[causa].append((d["longitude"], d["latitude"]))

        for tipo, pontos in eventos_por_tipo.items():
            if pontos:
                x, y = zip(*pontos)
                self.ax.scatter(x, y, color=tipo_cores[tipo], label=tipo)

        self.ax.legend(title="Legenda")
        self.canvas.draw()

# Execução principal
if __name__ == "__main__":
    app = InterfaceMonitoramento()
    app.mainloop()
