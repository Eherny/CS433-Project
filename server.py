import socket
import threading
import datetime
import json
import os

def create_message(report_request_flag=0, report_response_flag=0, join_request_flag=0, join_reject_flag=0,
                   join_accept_flag=0, new_user_flag=0, quit_request_flag=0, quit_accept_flag=0,
                   attachment_flag=0, number=0, username='', filename='', payload='',timestamp=''):
    message = {
        'REPORT_REQUEST_FLAG': report_request_flag,
        'REPORT_RESPONSE_FLAG': report_response_flag,
        'JOIN_REQUEST_FLAG': join_request_flag,
        'JOIN_REJECT_FLAG': join_reject_flag,
        'JOIN_ACCEPT_FLAG': join_accept_flag,
        'NEW_USER_FLAG': new_user_flag,
        'QUIT_REQUEST_FLAG': quit_request_flag,
        'QUIT_ACCEPT_FLAG': quit_accept_flag,
        'ATTACHMENT_FLAG': attachment_flag,
        'NUMBER': number,
        'USERNAME': username,
        'FILENAME': filename,
        'PAYLOAD_LENGTH': len(payload),
        'PAYLOAD': payload,
        'TIMESTAMP':timestamp
    }
    return message

class ChatroomServer:
    def __init__(self):
        self.host = 'localhost' # loopback address
        self.port = 18000 # default port number
        self.server_socket = None
        self.clients = {}
        self.usernames = []
        self.max_clients = 3
        self.num_clients = 0
        self.chat_history = []

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Chatroom server started on port {self.port}")
        while True:
            client_socket, client_address = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.start()

    def handle_client(self, client_socket):
        while True:
            try:
                raw_message = client_socket.recv(1024)
                if not raw_message:
                    break
                message = json.loads(raw_message.decode())
            except (ConnectionResetError, json.JSONDecodeError):
                break

            if message["JOIN_REQUEST_FLAG"] == 1:
                username = message["USERNAME"]
                if username in self.usernames or self.num_clients >= self.max_clients:
                    if username in self.usernames:
                        payload = "The server rejects the join request. Another user is using this username."
                    else:
                        payload = "The server rejects the join request. The chatroom has reached its maximum capacity."
                    reject_message = create_message(join_reject_flag=1, payload=payload)
                    client_socket.send(json.dumps(reject_message).encode())
                    client_socket.close()
                    return

                self.usernames.append(username)
                self.clients[client_socket] = username
                print(f"New connection from {username}")
                self.num_clients += 1  # Increment the number of clients here
                welcome_message_text = "Welcome to the chatroom!"
                chat_history_text = "\n".join([msg["PAYLOAD"] for msg in self.chat_history])
                welcome_message = create_message(join_accept_flag=1, username=username, payload=f"{welcome_message_text}\nChat History:\n{chat_history_text}")
                client_socket.send(json.dumps(welcome_message).encode())

                timestamp = datetime.datetime.now().strftime( '[%H:%M:%S]')
                self.broadcast(json.dumps(create_message(new_user_flag=1, payload=f"{timestamp} {username} has joined the chatroom.")).encode())


            elif message["QUIT_REQUEST_FLAG"] == 1:
                username = self.clients[client_socket]
                print(f"{username} has left the chatroom.")
                self.usernames.remove(username)
                del self.clients[client_socket]
                client_socket.close()
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.broadcast(json.dumps(create_message(quit_accept_flag=1, payload=f"{timestamp} {username} has left the chatroom.")).encode())
                self.num_clients -= 1
                break

            elif message["REPORT_REQUEST_FLAG"] == 1:
                self.send_report(client_socket)

            elif message["PAYLOAD"]:
                if message["PAYLOAD"] == "a":
                    client_socket.send(json.dumps(create_message(attachment_flag=1)).encode())
                    attachment_message = json.loads(client_socket.recv(1024).decode())
                    if attachment_message["ATTACHMENT_FLAG"] == 1:
                        filename = attachment_message["FILENAME"]
                        payload = attachment_message["PAYLOAD"]
                        with open(os.path.join("downloads", filename), "w") as f:
                            f.write(payload)
                        self.broadcast(json.dumps(create_message(payload=f"{datetime.datetime.now().strftime('[%H:%M:%S]')} {self.clients[client_socket]} uploaded an attachment: {filename}")).encode())
                        self.chat_history.append(create_message(payload=f"{datetime.datetime.now().strftime('[%H:%M:%S]')} {self.clients[client_socket]} uploaded an attachment: {filename}"))
                else:
                    username = self.clients[client_socket]
                    timestamp = message['TIMESTAMP']
                    broadcast_message = create_message(payload=f"{timestamp} {username}: {message['PAYLOAD']}")
                    self.broadcast(json.dumps(broadcast_message).encode())
                    self.chat_history.append(broadcast_message) # Store the message in the chat history



    def broadcast(self, message, prefix=""):
        for client_socket in self.clients:
            client_socket.send(prefix.encode()+message)
    def send_report(self, client_socket):
        num_users = len(self.clients)
        payload = []
        for client, username in self.clients.items():
            ip_address, port_number = client.getpeername()
            payload.append({
                'USERNAME': username,
                'IP_ADDRESS': ip_address,
                'PORT_NUMBER': port_number
            })
        message = create_message(report_response_flag=1, number=num_users, payload=json.dumps(payload))
        client_socket.send(json.dumps(message).encode())



if __name__ == "__main__":
    chatroom_server = ChatroomServer()
    chatroom_server.start()
