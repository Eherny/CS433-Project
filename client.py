import json
import socket
import threading
import datetime
import os

def create_message(report_request_flag=0, report_response_flag=0, join_request_flag=0, join_reject_flag=0,
                   join_accept_flag=0, new_user_flag=0, quit_request_flag=0, quit_accept_flag=0,
                   attachment_flag=0, number=0, username='', filename='', payload='', timestamp='', filepath=''):
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
        'TIMESTAMP': timestamp,
        'FILEPATH': filepath
    }
    return message

class ChatroomClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.running = False

    def start(self):
        self.client_socket.connect((self.host, self.port))

        self.show_menu()


    def send_message(self):
        message = input()
        if message:
            timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')
            if message.startswith('/report'):
                message = create_message(report_request_flag=1, username=self.username, timestamp=timestamp)
            elif message == 'q':
                quit_message = create_message(quit_request_flag=1, username=self.username, timestamp=timestamp)
                self.client_socket.send(json.dumps(quit_message).encode())
                self.running = False  # Set running to False before closing the socket
                self.client_socket.close()
                self.client_socket = None
                self.username = None
                return
            else:
                message = create_message(payload=message, username=self.username, timestamp=timestamp)
            self.client_socket.send(json.dumps(message).encode())

    def upload_file(self):
        print("Please enter the file path and name:")
        filepath = input("> ")
        try:
            with open(filepath, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print("File not found.")
            return

        filename = os.path.basename(filepath)
        message = create_message(attachment_flag=1, username=self.username, filename=filename,
                                 payload=content, filepath=filepath)
        self.client_socket.send(json.dumps(message).encode())
    def join_chatroom_and_start(self):
        if self.username is None:
            self.prompt_for_username()

        if self.client_socket is None:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.client_socket.connect((self.host, self.port))
            except ConnectionRefusedError:
                print("Unable to connect to the server. Please try again later.")
                self.client_socket = None
                return

        join_request = create_message(join_request_flag=1, username=self.username)
        self.client_socket.send(json.dumps(join_request).encode())

        response = json.loads(self.client_socket.recv(1024).decode())

        if response["JOIN_ACCEPT_FLAG"] == 1:
            print(response["PAYLOAD"])
            self.running = True
            thread = threading.Thread(target=self.receive_messages)
            thread.start()
            while self.running:
                self.send_message()
            self.show_menu()
        elif response["JOIN_REJECT_FLAG"] == 1:
            print(response["PAYLOAD"])
            self.client_socket.close()
            self.client_socket = None
            self.username = None

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(1024)
                if not data:  # Check if data is empty, which means the connection is closed
                    break
                decoded_message = json.loads(data)

                if decoded_message["NEW_USER_FLAG"] == 1 or decoded_message["QUIT_ACCEPT_FLAG"] == 1 or decoded_message["PAYLOAD"]:
                    print(decoded_message["PAYLOAD"])
                elif decoded_message["ATTACHMENT_FLAG"] == 1:
                    print("You can now upload an attachment.")
                else:
                    print("Error: Invalid message received.")

            except ConnectionResetError:
                print("Connection to the server has been lost.")
                self.running = False
                break
            except json.JSONDecodeError:
                print("An error occurred while decoding the message.")
                break



    def prompt_for_username(self):
        self.username = input("Please enter a username: ")

    def quit(self):
        if self.client_socket and self.running:
            quit_message = create_message(quit_request_flag=1, username=self.username)
            self.client_socket.send(json.dumps(quit_message).encode())
            self.client_socket.close()
        exit()
    def get_report(self):
        report_request = create_message(report_request_flag=1, username=self.username)
        self.client_socket.send(json.dumps(report_request).encode())
        received_data = self.client_socket.recv(1024).decode()

        if received_data:  # Check if the received data is not empty
            try:
                report_response = json.loads(received_data)
            except json.decoder.JSONDecodeError:
                print("There are no active users in the chatroom currently")
                self.show_menu()
                return

            if report_response["REPORT_RESPONSE_FLAG"] == 1:
                number_of_users = report_response["NUMBER"]
                print(f"There are {number_of_users} active users in the chatroom.")

                if report_response["PAYLOAD"]:
                    payload = json.loads(report_response["PAYLOAD"])  # You need to parse the payload as it is a JSON string
                    for index, user in enumerate(payload, start=1):
                        print(f"{index}. {user['USERNAME']} at IP: {user['IP_ADDRESS']} and port: {user['PORT_NUMBER']}.")
                else:
                    print("No active users in the chatroom.")
            else:
                print("Error: Invalid response from the server.")
        else:
            print("Error: No data received from the server.")

        self.show_menu()








    def show_menu(self):
        print("Please select one of the following options:")
        print("1. Get a report of the chatroom from the server.")
        print("2. Request to join the chatroom.")
        print("3. Quit the program.")
        choice = input("Enter your choice: ")

        if choice == '1':
            self.get_report()
        elif choice == '2':
            self.join_chatroom_and_start()
        elif choice == '3':
            self.quit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    host = 'localhost'
    port = 18000

    chatroom_client = ChatroomClient(host, port)
    chatroom_client.start()
