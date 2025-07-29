# network.py
import socket
import threading
import json

class P2PNode:
    def __init__(self, name, is_host, host_ip="localhost", port=5000):
        self.name = name
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        self.peers = []
        self.conn = None
        self.lock = threading.Lock()
        self.messages = []

    def start(self):
        if self.is_host:
            threading.Thread(target=self._accept_connections).start()
        else:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.host_ip, self.port))
            threading.Thread(target=self._receive, args=(self.conn,)).start()

    def _accept_connections(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host_ip, self.port))
        server.listen(3)
        print("Esperando jugadores...")
        while len(self.peers) < 3:
            conn, addr = server.accept()
            print(f"Jugador conectado desde {addr}")
            self.peers.append(conn)
            threading.Thread(target=self._receive, args=(conn,)).start()

    def send_to_all(self, data):
        message = json.dumps(data).encode()
        if self.is_host:
            for conn in self.peers:
                conn.send(message)
        else:
            self.conn.send(message)

    def _receive(self, conn):
        while True:
            try:
                data = conn.recv(2048)
                if data:
                    with self.lock:
                        self.messages.append(json.loads(data.decode()))
            except:
                break

    def get_messages(self):
        with self.lock:
            msgs = self.messages[:]
            self.messages = []
        return msgs
