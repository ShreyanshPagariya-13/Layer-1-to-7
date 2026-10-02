import socket
import threading
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# Configuration
HOST = '127.0.0.1'
PORT = 8080

# 32-byte key for AES-256
# In a real-world scenario, this should be securely exchanged or derived.
SECRET_KEY = b'this_is_a_32_byte_secret_key_123'

# Shared State
clients = []  # List of active client socket objects
sessions = {} # Dictionary mapping socket -> username
state_lock = threading.Lock() # Mutex lock for thread-safe access to shared state

def encrypt_message(plaintext: str) -> bytes:
    """Encrypt a string message using AES-256-CFB."""
    # Generate a fresh 16-byte IV for every message
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(SECRET_KEY, AES.MODE_CFB, iv=iv)
    ciphertext = cipher.encrypt(plaintext.encode('utf-8'))
    # Prepend IV to ciphertext so the receiver can decrypt
    return iv + ciphertext

def decrypt_message(encrypted_data: bytes) -> str:
    """Decrypt incoming bytes using AES-256-CFB."""
    # Extract the 16-byte IV from the beginning
    iv = encrypted_data[:AES.block_size]
    ciphertext = encrypted_data[AES.block_size:]
    cipher = AES.new(SECRET_KEY, AES.MODE_CFB, iv=iv)
    plaintext = cipher.decrypt(ciphertext).decode('utf-8')
    return plaintext

def broadcast(message: str, sender_conn: socket.socket):
    """Encrypt and broadcast a message to all clients except the sender."""
    encrypted_msg = encrypt_message(message)
    
    with state_lock:
        for client in clients:
            if client != sender_conn:
                try:
                    # Prefix the message length could be needed in a robust protocol,
                    # but for this simple demonstration we'll just send it.
                    # We send a fixed-size header first to ensure complete reads, 
                    # or assume the buffer is large enough for chat messages.
                    # To keep it minimal, we send the encrypted message directly.
                    # Wait, TCP is a stream. We should frame the messages to avoid
                    # sticking. Let's prepend a 4-byte length header.
                    msg_length = len(encrypted_msg).to_bytes(4, byteorder='big')
                    client.sendall(msg_length + encrypted_msg)
                except Exception as e:
                    print(f"Error broadcasting to a client: {e}")

def handle_client(conn: socket.socket, addr):
    """Thread function to handle a single client's connection."""
    print(f"[NEW CONNECTION] {addr} connected.")
    
    # 1. First message from client must be their username (encrypted)
    try:
        # Read the 4-byte length header
        length_bytes = conn.recv(4)
        if not length_bytes:
            raise ConnectionError("Connection closed before sending username.")
        msg_length = int.from_bytes(length_bytes, byteorder='big')
        
        encrypted_username = conn.recv(msg_length)
        username = decrypt_message(encrypted_username)
        
        # Register the session
        with state_lock:
            clients.append(conn)
            sessions[conn] = username
        
        print(f"[{addr}] Registered as username: {username}")
        broadcast(f"System: {username} has joined the chat.", conn)
        
    except Exception as e:
        print(f"[{addr}] Failed to register: {e}")
        conn.close()
        return

    # 2. Main loop: receive encrypted messages and broadcast
    try:
        while True:
            # Read 4-byte length header
            length_bytes = conn.recv(4)
            if not length_bytes:
                break # Client disconnected nicely
            
            msg_length = int.from_bytes(length_bytes, byteorder='big')
            
            # Read the full message based on the length
            encrypted_data = b""
            while len(encrypted_data) < msg_length:
                chunk = conn.recv(msg_length - len(encrypted_data))
                if not chunk:
                    break
                encrypted_data += chunk
                
            if not encrypted_data:
                break

            # Decrypt the incoming message
            message = decrypt_message(encrypted_data)
            
            # Identify sender safely using the lock
            with state_lock:
                sender_name = sessions.get(conn, "Unknown")
            
            # Prefix with sender's username
            formatted_msg = f"{sender_name}: {message}"
            print(f"[RECV] {formatted_msg}")
            
            # Broadcast to all OTHER clients
            broadcast(formatted_msg, conn)
            
    except Exception as e:
        print(f"[{addr}] Error: {e}")
    finally:
        # 3. Disconnect and cleanup under the lock
        with state_lock:
            if conn in clients:
                clients.remove(conn)
            username = sessions.pop(conn, "Unknown")
            
        print(f"[DISCONNECT] {addr} ({username}) disconnected.")
        broadcast(f"System: {username} has left the chat.", conn)
        conn.close()

def start_server():
    """Start the TCP server and listen for incoming connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow address reuse to avoid "Address already in use" errors during testing
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen()
    print(f"[STARTING] Server is listening on {HOST}:{PORT}")
    
    # Infinite loop to accept incoming connections
    while True:
        conn, addr = server.accept()
        # Spawn one thread per client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True # Allow server to exit even if threads are running
        thread.start()
        
        # Note: Active connection count doesn't subtract the main thread or the initial ones
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()
