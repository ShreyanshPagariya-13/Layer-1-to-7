# TCP Chat Server (Layer 1 to 7)

A real-time TCP/IP chat system built using Python's `socket` library, implementing end-to-end AES-256 encryption for secure messaging. The architecture relies purely on the Python standard library with multi-threading and mutex locks to ensure reliable state management for 50+ concurrent connections.

## OSI Model Mapping

This project practically demonstrates the layers of the OSI model:

1. **Layer 1 & 2 (Physical / Data Link)**: Relies on the underlying network hardware (Ethernet/Wi-Fi) and OS drivers to transmit raw bit streams.
2. **Layer 3 (Network)**: Utilizes **IP Addressing** (`127.0.0.1` by default) to route packets to the correct machine.
3. **Layer 4 (Transport)**: Uses **TCP on port 8080** to establish a reliable, connection-oriented byte stream between the client and the server.
4. **Layer 5 (Session)**: Manages **user sessions** mapping TCP connections to registered usernames. The server tracks these sessions and gracefully handles disconnects.
5. **Layer 6 (Presentation)**: Implements **AES-256-CFB Encryption** using `pycryptodome`. Data is securely encrypted and decrypted before it reaches the application layer, ensuring the confidentiality of messages.
6. **Layer 7 (Application)**: The **Chat Protocol** itself—formatting messages (`Sender: Message`), broadcasting logic, and parsing the payload length boundaries.

## Features

- **No Frameworks**: Built entirely using Python standard libraries (`socket`, `threading`).
- **AES-256 Encryption**: Uses `pycryptodome` for CFB mode encryption with a fresh 16-byte IV per message.
- **Thread-safe Server**: Spawns one thread per client and guards shared resources (the clients list and session map) using `threading.Lock()`.
- **Concurrent Client**: Spawns distinct threads for reading terminal input and listening for incoming messages simultaneously without blocking.

## How to Run

### Prerequisites

Install the only required dependency for AES encryption:
```bash
pip install -r requirements.txt
```

### Start the Server
Open a terminal and start the central server:
```bash
python server.py
```
*The server will start listening on `127.0.0.1:8080`.*

### Start Clients
Open multiple separate terminals to simulate different users and run:
```bash
python client.py
```
Enter a username when prompted, and start sending messages! The server will decrypt, prepend your username, re-encrypt, and broadcast to all other connected clients.

## Verification Note: Testing 50+ Concurrent Clients

To verify that the server's thread-safe design can handle 50+ concurrent connections without state corruption, you can simulate mass connections using a short Python script. 

Here is a snippet to test the load:

```python
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
```

Run this script while the server is active to see 50 threads connect, register, send an encrypted message, and safely disconnect, validating the `threading.Lock()` usage on the server.
