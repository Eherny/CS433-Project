import socket
import threading

class ChatroomClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.running = False # flag to indicate if the client is running
    def start(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Could not connect to the chatroom server. Please try again later.")
            return
        self.username = input("Enter your username: ")
        self.client_socket.send(self.username.encode())
        welcome_message = self.client_socket.recv(1024).decode()
        print(welcome_message)
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()
        self.running = True
        while self.running:
            message = input()
            if message.lower() == "/quit":
                self.client_socket.close()
                self.running = False
                break
            self.client_socket.send(message.encode())

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                print(message)
            except ConnectionResetError:
                print("Connection to the server has been lost.")
                self.running = False

if __name__ == "__main__":
    chatroom_client = ChatroomClient('127.0.0.1', 18000)
    chatroom_client.start()
