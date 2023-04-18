import socket
import threading
import datetime
import json
import os
import base64

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
          BUFFER_SIZE=1024
          while True:
            try:
                raw_message = client_socket.recv(1024)
                if not raw_message:
                    break
                message = json.loads(raw_message.decode())
                #print("Decoded message:", message)
                if not isinstance(message, dict):
                    raise ValueError("Invalid message format")
            except (ConnectionResetError, json.JSONDecodeError, ValueError):
                continue

            if message["JOIN_REQUEST_FLAG"] == 1:
                username = message["USERNAME"]
                if username in self.usernames or self.num_clients >= self.max_clients:
                    if username in self.usernames:
                        payload = "The server rejects the join request. Another user is using this username."
                        
                    else:
                        payload = "The server rejects the join request. The chatroom has reached its maximum capacity."
                    reject_message = create_message(join_reject_flag=1, payload=payload)
                    print(f"Reject message sent to {username}: {payload}")
                    client_socket.send(json.dumps(reject_message).encode())
                    client_socket.close()
                    return

                self.usernames.append(username)
                self.clients[client_socket] = username
                print(f"New connection from {username}")
                self.num_clients += 1  # Increment the number of clients here
                welcome_message_text = "Welcome to the chatroom!\nType lowercase ‘q’ and press enter at any time to quit the chatroom.\nType lowercase ‘a’ and press enter at any time to upload an attachment to the chatroom."
                chat_history_text = "\n".join([msg["PAYLOAD"] for msg in self.chat_history])
                welcome_message = create_message(join_accept_flag=1, username=username, payload=f"{welcome_message_text}\nHere is the History of the Chatroom:\n{chat_history_text}")
                client_socket.send(json.dumps(welcome_message).encode())

                timestamp = datetime.datetime.now().strftime( '[%H:%M:%S]')
                new_user_message = json.dumps(create_message(new_user_flag=1, payload=f"{timestamp}Server: {username} has joined the chatroom.")).encode()
                self.broadcast(new_user_message)
        
                # Store the message in the chat history
                self.chat_history.append(json.loads(new_user_message.decode()))


            elif message["QUIT_REQUEST_FLAG"] == 1:
                username = self.clients[client_socket]
                print(f"Server:{username} has left the chatroom.")
                self.usernames.remove(username)
                del self.clients[client_socket]
                client_socket.close()
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                quit_message = create_message(quit_accept_flag=1, payload=f"{timestamp} Server: {username} has left the chatroom.")
                self.broadcast(json.dumps(quit_message).encode())
                self.chat_history.append(quit_message)  # Store the quit message in the chat history
                self.num_clients -= 1
                break

            elif message["REPORT_REQUEST_FLAG"] == 1:
                ip_address, port_number = client_socket.getpeername()
                print(f"Server: Client ({ip_address}, {port_number}) has requested a report.")
                self.send_report(client_socket)
            elif message["ATTACHMENT_FLAG"] == 1:
                filename = message["FILENAME"]
                payload = message["PAYLOAD"]
                content = base64.b64decode(payload.encode())
                with open(os.path.join("downloads", filename), "wb") as f:
                    f.write(content)

                with open(os.path.join("downloads", filename), "r") as f:
                    file_content = f.read()
                timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')
                broadcast_message = create_message(
                attachment_flag=1,
                username=message["USERNAME"],
                filename=filename,
                payload=file_content,
                timestamp=timestamp
            )
                
                broadcast_payload = f"{timestamp} {self.clients[client_socket]} uploaded an attachment: {filename}"
                broadcast_message_formatted = create_message(payload=broadcast_payload)
                self.chat_history.append(broadcast_message_formatted)

                self.broadcast(json.dumps(broadcast_message_formatted).encode())
                file_contents_payload = f"{timestamp} {self.clients[client_socket]} shared the contents of {filename}:\n{file_content}"
                file_contents_message = create_message(payload=file_contents_payload)
                self.broadcast(json.dumps(file_contents_message).encode())
                self.chat_history.append(file_contents_message)
                print(f"Server: {username} has sent a file: {filename}")
            elif message["PAYLOAD"]:
                if message["PAYLOAD"] == "a":
                    client_socket.send(json.dumps(create_message(attachment_flag=1)).encode())
                    attachment_message = json.loads(client_socket.recv(1024).decode())
                    if attachment_message["ATTACHMENT_FLAG"] == 1:
                        filename = attachment_message["FILENAME"]
                        payload = attachment_message["PAYLOAD"]
                        with open(os.path.join("downloads", filename), "wb") as f:
                            f.write(payload)
                        self.broadcast(json.dumps(create_message(payload=f"{datetime.datetime.now().strftime('[%H:%M:%S]')} {self.clients[client_socket]} uploaded an attachment: {filename}")).encode())
                        self.chat_history.append(create_message(payload=f"{datetime.datetime.now().strftime('[%H:%M:%S]')} {self.clients[client_socket]} uploaded an attachment: {filename}"))

                else:
                    username = self.clients[client_socket]
                    timestamp = message['TIMESTAMP']
                    text_message= f"{timestamp} {username}: {message['PAYLOAD']}"
                    print(f"Server: {username} has written a message: {message['PAYLOAD']}")
                    broadcast_message = create_message(payload=text_message)
                    self.broadcast(json.dumps(broadcast_message).encode())
                    self.chat_history.append(broadcast_message) # Store the message in the chat history
        

    def broadcast(self, message, prefix=b""):
        for client_socket in self.clients:
            client_socket.send(prefix+message)
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
