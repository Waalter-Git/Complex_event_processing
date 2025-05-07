import customtkinter as ctk
import socket
import threading
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

eventos_recebidos = 0
coordenadas = []
fila_alarmes = []

def receber_tcp():
    global eventos_recebidos

    HOST = "0.0.0.0"
    PORT = 6006

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Interface TCP escutando em {HOST}:{PORT}...")

    while True:
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(4096)
            if data:
                try:
                    alarme = json.loads(data.decode("utf-8"))
                    eventos_recebidos += alarme.get("numero_eventos", 0)
                    lat = alarme["localizacao_media"]["latitude"]
                    lon = alarme["localizacao_media"]["longitude"]
                    coordenadas.append((lat, lon))
                    fila_alarmes.append(alarme)
                    atualizar_interface()
                except Exception as e:
                    print(f"Erro ao processar alarme recebido: {e}")

def atualizar_interface():
    status_udp.configure(text="✅ Thread UDP Ativa")
    status_cep.configure(text="✅ Thread CEP Ativa")
    contador_label.configure(text=f"Eventos Recebidos: {eventos_recebidos}")

    if fila_alarmes:
        alarme = fila_alarmes[-1]
        texto = f"🔔 {alarme['eventoID']} – {alarme['numero_eventos']} eventos\n" \
                f"{alarme['timestamp']}\n" \
                f"{alarme['localizacao_media']['latitude']}, {alarme['localizacao_media']['longitude']}\n" \
                f"Causa: {alarme.get('causa', 'N/A')} (cod {alarme.get('codErro', '-')})"
        area_alarme.configure(state="normal")
        area_alarme.delete("0.0", "end")
        area_alarme.insert("0.0", texto)
        area_alarme.configure(state="disabled")

        log.insert("end", f"[{alarme['timestamp']}] Alarme gerado: {alarme['eventoID']} - {alarme.get('causa')}\n")
        log.see("end")

    atualizar_grafico()

def atualizar_grafico():
    grafico.clear()
    if coordenadas:
        lats, longs = zip(*coordenadas)
        grafico.scatter(longs, lats, c='red', marker='x')
        grafico.set_title("Gráfico de Eventos Agrupados")
        grafico.set_xlabel("Longitude")
        grafico.set_ylabel("Latitude")
    canvas.draw()

# GUI
root = ctk.CTk()
root.title("Monitoramento de Quedas - Módulo 5b")
root.geometry("1100x750")
root.grid_columnconfigure((0, 1), weight=1)

titulo = ctk.CTkLabel(root, text="Monitoramento de Quedas", font=("Arial", 24, "bold"))
titulo.pack(pady=10)

# STATUS
frame_status = ctk.CTkFrame(root, fg_color="#f0f0f0")
frame_status.pack(pady=5)

status_udp = ctk.CTkLabel(frame_status, text="⚪ UDP", width=150, font=("Arial", 14))
status_udp.grid(row=0, column=0, padx=10, pady=10)

status_cep = ctk.CTkLabel(frame_status, text="⚪ CEP", width=150, font=("Arial", 14))
status_cep.grid(row=0, column=1, padx=10, pady=10)

contador_label = ctk.CTkLabel(frame_status, text="Eventos Recebidos: 0", font=("Arial", 14))
contador_label.grid(row=0, column=2, padx=10, pady=10)

# CONTEÚDO
frame_conteudo = ctk.CTkFrame(root, fg_color="transparent")
frame_conteudo.pack(pady=5, fill="both", expand=True)

frame_conteudo.grid_columnconfigure(0, weight=1)
frame_conteudo.grid_columnconfigure(1, weight=2)

# ALARMES E LOG
frame_esquerda = ctk.CTkFrame(frame_conteudo, fg_color="#e5e5e5", corner_radius=10)
frame_esquerda.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

ctk.CTkLabel(frame_esquerda, text="Últimos Alarmes", font=("Arial", 16, "bold")).pack(pady=5)
area_alarme = ctk.CTkTextbox(frame_esquerda, height=120, width=330, font=("Consolas", 13), corner_radius=10)
area_alarme.configure(state="disabled")
area_alarme.pack(padx=10, pady=(0, 10))

ctk.CTkLabel(frame_esquerda, text="Log", font=("Arial", 14, "bold")).pack()
log = ctk.CTkTextbox(frame_esquerda, height=170, width=330, font=("Consolas", 11), corner_radius=10)
log.pack(padx=10, pady=5)

# GRÁFICO
frame_direita = ctk.CTkFrame(frame_conteudo, fg_color="#e5e5e5", corner_radius=10)
frame_direita.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

ctk.CTkLabel(frame_direita, text="Gráfico", font=("Arial", 16, "bold")).pack(pady=5)

fig, grafico = plt.subplots(figsize=(7, 5.5))
canvas = FigureCanvasTkAgg(fig, master=frame_direita)
canvas.get_tk_widget().pack(expand=True, fill="both")

# BOTÃO
botao_sair = ctk.CTkButton(root, text="Encerrar Monitoramento", fg_color="gray", command=root.destroy)
botao_sair.pack(pady=15)

# Inicia a thread de escuta TCP
threading.Thread(target=receber_tcp, daemon=True).start()

root.mainloop()
