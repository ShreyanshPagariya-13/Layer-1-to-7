import socket
import threading
import time
from client import encrypt_message

def simulate_client(client_id):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 8080))
        
        # Send username
        username_payload = encrypt_message(f"Bot_{client_id}")
        s.sendall(len(username_payload).to_bytes(4, 'big') + username_payload)
        
        time.sleep(1) # wait for registration
        
        # Send a message
        msg_payload = encrypt_message(f"Hello from bot {client_id}!")
        s.sendall(len(msg_payload).to_bytes(4, 'big') + msg_payload)
        
        time.sleep(2) # stay connected briefly
        s.close()
    except Exception as e:
        print(f"Bot {client_id} failed: {e}")

# Spawn 50 threads concurrently
threads = []
for i in range(50):
    t = threading.Thread(target=simulate_client, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Test complete.")
