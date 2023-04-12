import socket
import threading
import tkinter as tk

class ChatroomClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.running = False # flag to indicate if the client is running

        # Create the Tkinter GUI
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

        self.menu_frame = tk.Frame(self.root)
        self.menu_frame.pack(side=tk.BOTTOM, padx=10, pady=10)

        self.report_button = tk.Button(self.menu_frame, text="Get report", command=self.get_report)
        self.report_button.pack(side=tk.LEFT)

        self.join_button = tk.Button(self.menu_frame, text="Join chatroom", command=self.join_chatroom)
        self.join_button.pack(side=tk.LEFT)

        self.quit_button = tk.Button(self.menu_frame, text="Quit", command=self.quit)
        self.quit_button.pack(side=tk.LEFT)

    def start(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("Could not connect to the chatroom server. Please try again later.")
            return
        
        # Create a prompt to enter the username
        username_label = tk.Label(self.root, text="Enter your username:")
        username_label.pack(side=tk.TOP, padx=10, pady=10)

        self.username_entry = tk.Entry(self.root, width=60)
        self.username_entry.pack(side=tk.TOP)

        username_button = tk.Button(self.root, text="Enter", command=self.set_username)
        username_button.pack(side=tk.TOP, padx=10, pady=10)

        self.root.wait_window(self.username_entry)

        # Once the username is entered, send it to the server and display the welcome message
        self.client_socket.send(self.username.encode())
        welcome_message = self.client_socket.recv(1024).decode()
        print(welcome_message)
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()
        self.running = True

        # Start the Tkinter event loop
        self.root.mainloop()

    def send_message(self):
        message = self.input_entry.get()
        if message:
            self.client_socket.send(message.encode())
            self.input_entry.delete(0, tk.END)

    def receive_messages(self):
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                self.message_listbox.insert(tk.END, message)
            except ConnectionResetError:
                print("Connection to the server has been lost.")
                self.running = False

    def get_report(self):
        self.client_socket.send("/report".encode())

    def join_chatroom(self):
        self.client_socket.send


    def quit(self):
        self.client_socket.send("/quit".encode())
        self.client_socket.close()
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    client = ChatroomClient("127.0.0.1", 18000)  # Replace with your chatroom server host and port
    client.start()
