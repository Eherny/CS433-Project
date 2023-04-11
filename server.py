import socket
import threading

class ChatroomServer:
    def __init__(self):
        self.host = '127.0.0.1' # loopback address
        self.port = 18000 # default port number
        self.server_socket = None
        self.clients = {}
        self.usernames = []
        self.max_clients=3

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Chatroom server started on port {self.port}")
        while True:
            if len(self.clients) < self.max_clients:
                client_socket, client_address = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                thread.start()
            else:
                print("Maximum number of clients reached. Rejecting connection request.")
                client_socket, client_address = self.server_socket.accept()
                client_socket.send("Maximum number of clients reached. Please try again later.".encode())
                client_socket.close()
    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                print(message)
            except ConnectionResetError:
                print("Connection to the server has been lost.")
                self.running = False            
    def handle_client(self, client_socket):
        username = client_socket.recv(1024).decode()
        if username in self.usernames:
            client_socket.send("This username is already taken. Please choose another one.".encode())
            client_socket.close()
            return
        self.usernames.append(username)
        self.clients[client_socket] = username
        print(f"New connection from {username}")
        client_socket.send("Welcome to the chatroom!".encode())
        self.broadcast(f"{username} has joined the chatroom.".encode())
        while True:
            message = client_socket.recv(1024)
            if not message:
                break
            self.broadcast(message, username+": ")
        print(f"{username} has left the chatroom.")
        self.usernames.remove(username)
        del self.clients[client_socket]
        client_socket.close()
        self.broadcast(f"{username} has left the chatroom.".encode())

    def broadcast(self, message, prefix=""):
        for client_socket in self.clients:
            client_socket.send(prefix.encode()+message)

if __name__ == "__main__":
    chatroom_server = ChatroomServer()
    chatroom_server.start()
