import json
import socket
import threading
import tkinter as tk
import datetime

def create_message(report_request_flag=0, report_response_flag=0, join_request_flag=0, join_reject_flag=0,
                   join_accept_flag=0, new_user_flag=0, quit_request_flag=0, quit_accept_flag=0,
                   attachment_flag=0, number=0, username='', filename='', payload='', timestamp=''):
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
        'TIMESTAMP': timestamp
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
            timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')
            if message.startswith('/report'):
                message = create_message(report_request_flag=1, username=self.username, timestamp=timestamp)
            else:
                message = create_message(payload=message, username=self.username, timestamp=timestamp)
            self.client_socket.send(json.dumps(message).encode())
            self.input_entry.delete(0, tk.END)


    def get_report(self):
        if self.client_socket:
            self.client_socket.send(json.dumps(create_message(report_request_flag=1, username=self.username)).encode())
            response = self.client_socket.recv(1024).decode()
            response = json.loads(response)
            if response['REPORT_RESPONSE_FLAG'] == 1:
                num_active_users = response['NUMBER']
                payload = json.loads(response['PAYLOAD'])
                message = f"There are {num_active_users} active users in the chatroom."
                self.message_listbox.insert(tk.END, message)
                if payload:
                    users_list = [f"{i+1}. {user['USERNAME']} at IP: {user['IP_ADDRESS']} and port: {user['PORT_NUMBER']}" for i, user in enumerate(payload)]
                    for user_info in users_list:
                        self.message_listbox.insert(tk.END, user_info)
                else:
                    self.message_listbox.insert(tk.END, "There are no active users.")
            else:
                self.message_listbox.insert(tk.END, "Failed to get report from server.")
        else:
                print("You need to join the chatroom before requesting a report.")




    def join_chatroom_and_start(self):
        if self.running:
            self.message_listbox.insert(tk.END, "You are already in the chatroom.")
            return

        if self.client_socket is None:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.client_socket.connect((self.host, self.port))
            except ConnectionRefusedError:
                print("Could not connect to the chatroom server. Please try again later.")
                return

        if self.username is None:
            self.prompt_for_username()

        if self.username is not None:
            join_request = create_message(join_request_flag=1, username=self.username)
            self.client_socket.send(json.dumps(join_request).encode())
            response = self.client_socket.recv(1024).decode()
            response = json.loads(response)
            if response['JOIN_ACCEPT_FLAG'] == 1:
                self.message_listbox.insert(tk.END, "Joined the chatroom!")
                self.running = True
                receive_thread = threading.Thread(target=self.receive_messages)
                receive_thread.start()
            elif response['JOIN_REJECT_FLAG'] == 1:
                self.message_listbox.insert(tk.END, response['PAYLOAD'])
                self.client_socket.close()
                self.client_socket = None
                # If the rejection message is because of the maximum capacity, don't clear the username.
                if response['PAYLOAD'] != "The server rejects the join request. The chatroom has reached its maximum capacity.":
                    self.username = None



    def prompt_for_username(self):
        username_prompt = tk.Toplevel(self.root)
        username_prompt.title("Username")
        username_prompt.protocol("WM_DELETE_WINDOW", self.quit)

        username_label = tk.Label(username_prompt, text="Please enter a username:")
        username_label.pack(padx=10, pady=10)

        username_entry = tk.Entry(username_prompt)
        username_entry.pack(padx=10, pady=10)

        def set_username():
            username = username_entry.get()
            if username:
                self.username = username
                username_prompt.destroy()

        username_button = tk.Button(username_prompt, text="OK", command=set_username)
        username_button.pack(padx=10, pady=10)
        username_prompt.grab_set()
        username_prompt.wait_window(username_prompt)

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                message = json.loads(message)
                if message["PAYLOAD"]:
                    self.message_listbox.insert(tk.END, message["PAYLOAD"])
            except ConnectionResetError:
                self.message_listbox.insert(tk.END, "Connection to the server has been lost.")
                self.running = False
                self.client_socket = None
                self.username = None

    def quit(self):
        if self.client_socket:
            quit_message = create_message(quit_request_flag=1, username=self.username)
            self.client_socket.send(json.dumps(quit_message).encode())
            self.client_socket.close()
        self.root.destroy()

    def show_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        chatroom_menu = tk.Menu(menu)
        menu.add_cascade(label="Chatroom", menu=chatroom_menu)
        chatroom_menu.add_command(label="Join Chatroom", command=self.join_chatroom_and_start)
        chatroom_menu.add_separator()
        chatroom_menu.add_command(label="Get Report", command=self.get_report)
        chatroom_menu.add_separator()
        chatroom_menu.add_command(label="Quit", command=self.quit)
if __name__ == "__main__":
    host = '127.0.0.1'
    port = 18000

    chatroom_client = ChatroomClient(host, port)
    chatroom_client.start()
