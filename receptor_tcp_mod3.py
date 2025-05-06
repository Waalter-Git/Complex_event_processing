import socket

HOST = '0.0.0.0'
PORT = 6006

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Receptor TCP escutando em {HOST}:{PORT}...")

    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Conexão de {addr}")
            data = conn.recv(4096)
            if data:
                print("Alarme recebido:")
                print(data.decode('utf-8'))
