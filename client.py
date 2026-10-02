import socket
import threading
import sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# Configuration
HOST = '127.0.0.1'
PORT = 8080

# 32-byte key for AES-256 (Must match server)
SECRET_KEY = b'this_is_a_32_byte_secret_key_123'

def encrypt_message(plaintext: str) -> bytes:
    """Encrypt a string message using AES-256-CFB."""
    # Generate a fresh 16-byte IV for every message
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(SECRET_KEY, AES.MODE_CFB, iv=iv)
    ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
    # Prepend IV to ciphertext
    return iv + ciphertext

def decrypt_message(encrypted_data: bytes) -> str:
    """Decrypt incoming bytes using AES-256-CFB."""
    # Extract the 16-byte IV from the beginning
    iv = encrypted_data[:AES.block_size]
    ciphertext = encrypted_data[AES.block_size:]
    cipher = AES.new(SECRET_KEY, AES.MODE_CFB, iv=iv)
    plaintext = cipher.decrypt(ciphertext).decode('utf-8')
    return plaintext

def send_message(client_socket: socket.socket, msg: str):
    """Encrypts and sends a message with a 4-byte length header."""
    encrypted_msg = encrypt_message(msg)
    msg_length = len(encrypted_msg).to_bytes(4, byteorder='big')
    client_socket.sendall(msg_length + encrypted_msg)

def receive_messages(client_socket: socket.socket):
    """Thread function to continuously receive and decrypt messages."""
    try:
        while True:
            # Read 4-byte length header
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                print("\n[DISCONNECTED] Server closed the connection.")
                break
            
            msg_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read the full message based on the length
            encrypted_data = b""
            while len(encrypted_data) < msg_length:
                chunk = client_socket.recv(msg_length - len(encrypted_data))
                if not chunk:
                    break
                encrypted_data += chunk
                
            if not encrypted_data:
                break

            # Decrypt the incoming message
            message = decrypt_message(encrypted_data)
            
            # Print the received message and prompt again
            print(f"\r{message}\n> ", end="")
            sys.stdout.flush()
            
    except Exception as e:
        print(f"\n[ERROR] An error occurred while receiving: {e}")
    finally:
        client_socket.close()
        # Exit the program abruptly since the server disconnected
        import os
        os._exit(0)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Failed to connect to server at {HOST}:{PORT}. Is it running?")
        return

    # Registration
    username = input("Enter your username: ")
    # Send encrypted username as the first message
    send_message(client_socket, username)
    print("Connected to the chat room! Type your message and press Enter.")

    # Start the receive thread
    # This thread blocks on recv(), decrypts incoming messages, and prints them
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.daemon = True
    receive_thread.start()

    # Main thread handles sending messages
    # It reads terminal input, encrypts, and sends
    try:
        while True:
            msg = input("> ")
            if msg.lower() in ('/quit', '/exit'):
                break
            if msg:
                send_message(client_socket, msg)
    except KeyboardInterrupt:
        pass
    finally:
        print("Disconnecting...")
        client_socket.close()

if __name__ == "__main__":
    main()
