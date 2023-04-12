import json
import socket
import threading
import tkinter as tk
def create_message(report_request_flag=0, report_response_flag=0, join_request_flag=0, join_reject_flag=0,
                   join_accept_flag=0, new_user_flag=0, quit_request_flag=0, quit_accept_flag=0,
                   attachment_flag=0, number=0, username='', filename='', payload=''):
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
        'PAYLOAD': payload
    }
    return message

class ChatroomClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.running = False

        self.root = tk.Tk()
        self.root.title("Chatroom Client")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self.message_listbox = tk.Listbox(self.root, height=20, width=80)
        self.message_listbox.pack(side=tk.TOP, padx=10, pady=10)

        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.input_label = tk.Label(self.input_frame, text="Enter message:")
        self.input_label.pack(side=tk.LEFT)

        self.input_entry = tk.Entry(self.input_frame, width=60)
        self.input_entry.pack(side=tk.LEFT)

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT)

    def start(self):
        self.show_menu()
        self.root.mainloop()

    def send_message(self):
        message = self.input_entry.get()
        if message:
            if message.startswith('/report'):
                message = create_message(report_request_flag=1, username=self.username)
        else:
            message = create_message(payload=message, username=self.username)
        self.client_socket.send(json.dumps(message).encode())
        self.input_entry.delete(0, tk.END)

    def get_report(self):
        self.client_socket.send("/report".encode())

    def join_chatroom(self):
        self.client_socket.send("/join".encode())

    def show_menu(self):
        self.create_menu()

    def create_menu(self):
        self.menu_frame = tk.Frame(self.root)
        self.menu_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.option_label = tk.Label(self.menu_frame, text="Please select one of the following options:")
        self.option_label.pack(side=tk.TOP)

        self.report_button = tk.Button(self.menu_frame, text="1. Get a report of the chatroom from the server.", command=self.get_report)
        self.report_button.pack(side=tk.TOP, padx=10, pady=5, anchor='w')

        self.join_button = tk.Button(self.menu_frame, text="2. Request to join the chatroom.", command=self.join_chatroom_and_start)
        self.join_button.pack(side=tk.TOP, padx=10, pady=5, anchor='w')

        self.quit_button = tk.Button(self.menu_frame, text="3. Quit the program.", command=self.quit)
        self.quit_button.pack(side=tk.TOP, padx=10, pady=5, anchor='w')


    def join_chatroom_and_start(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Could not connect to the chatroom server. Please try again later.")
            return

        self.prompt_for_username()
        if self.username is not None:
            self.client_socket.send(self.username.encode())
            welcome_message = self.client_socket.recv(1024).decode()
            self.message_listbox.insert(tk.END, welcome_message)
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()
            self.running = True
            self.join_button.pack_forget()



    def prompt_for_username(self):
        self.username_label = tk.Label(self.root, text="Enter your username:")
        self.username_label.pack(side=tk.TOP, padx=10, pady=10)

        self.username_entry = tk.Entry(self.root, width=60)
        self.username_entry.pack(side=tk.TOP)

        self.username_button = tk.Button(self.root, text="Enter", command=self.set_username) # Changed to self.username_button
        self.username_button.pack(side=tk.TOP, padx=10, pady=10)

        self.root.wait_window(self.username_entry)


    def set_username(self):
        self.username = self.username_entry.get()
        if self.username:
            self.username_entry.delete(0, tk.END)
            self.username_label.pack_forget()
            self.username_button.pack_forget()
            self.username_entry.pack_forget()
            self.root.update()
        else:
            self.username_label.config(text="Please enter a non-empty username:")



    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                message = json.loads(message)
                payload = message['PAYLOAD']
                self.message_listbox.insert(tk.END, payload)
            except ConnectionResetError:
                print("The connection to the server was lost.")
                break


    def quit(self):
        if self.client_socket:
            self.client_socket.send("/quit".encode())
            self.client_socket.close()
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    client = ChatroomClient("127.0.0.1", 18000) # Replace with your chatroom server host and port
    client.start()
