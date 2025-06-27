package server

import (
	"bufio"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
	"log"
	"net"
	"strings"
	"sync"
)

// Encryption key 16 bytes
var key = []byte("1234567890123456")
var clients = make([]net.Conn, 0)
var sessions = make(map[net.Conn]string)
var mutex sync.Mutex

// Initialize the server (listen 8080) and accept the client net.accept append them on clients[] and call handle function (for session store and broadcast the client messages)
func StartServer() {
	listener, err := net.Listen("tcp", "127.0.0.1:8080")

	if err != nil {
		log.Fatal("error in server conn:", err)
	}
	defer listener.Close()
	fmt.Println("Server listening on 127.0.0.1:8080")
	
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println("Error accepting connection:", err)
			continue
		}
		mutex.Lock()
		clients = append(clients, conn)
		mutex.Unlock()
		go handleConnection(conn)
	}
}

// HandleConnection manages client connection
func handleConnection(conn net.Conn) {
	defer func() {
		mutex.Lock()
		delete(sessions, conn)
		removeClient(conn)
		conn.Close()
		mutex.Unlock()
	}()

	reader := bufio.NewReader(conn)
	
	// Session management
	conn.Write([]byte("Enter your username: "))
	username, err := reader.ReadString('\n')
	if err != nil {
		fmt.Println("Error reading username:", err)
		return
	}
	username = strings.TrimSpace(username)

	mutex.Lock()
	sessions[conn] = username
	mutex.Unlock()
	fmt.Printf("User %s connected\n", username)

	// Manage incoming messages from clients
	for {
		message, err := reader.ReadString('\n')
		if err != nil {
			fmt.Printf("User %s disconnected\n", username)
			break
		}
		
		message = strings.TrimSpace(message)
		decryptedMessage, err := decryptMessage([]byte(message))
		if err != nil {
			fmt.Println("Error decrypting message:", err)
			continue
		}
		
		fullMessage := fmt.Sprintf("%s: %s", username, decryptedMessage)
		fmt.Println(fullMessage)
		
		// Broadcast to other clients
		broadcastMessage(conn, fullMessage)
	}
}

func broadcastMessage(sender net.Conn, message string) {
	mutex.Lock()
	defer mutex.Unlock()
	for _, client := range clients {
		if client != sender {
			encryptedMessage, err := encryptMessage([]byte(message))
			if err != nil {
				fmt.Println("Error encrypting message:", err)
				continue
			}
			client.Write(encryptedMessage)
		}
	}
}

func removeClient(conn net.Conn) {
	mutex.Lock()
	defer mutex.Unlock()
	for i, client := range clients {
		if client == conn {
			clients = append(clients[:i], clients[i+1:]...)
			break
		}
	}
}

func encryptMessage(plainText []byte) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	cipherText := make([]byte, aes.BlockSize+len(plainText))
	iv := cipherText[:aes.BlockSize]
	if _, err := rand.Read(iv); err != nil {
		return nil, err
	}
	stream := cipher.NewCFBEncrypter(block, iv)
	stream.XORKeyStream(cipherText[aes.BlockSize:], plainText)
	return cipherText, nil
}

func decryptMessage(cipherText []byte) (string, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}
	if len(cipherText) < aes.BlockSize {
		return "", fmt.Errorf("ciphertext too short")
	}
	iv := cipherText[:aes.BlockSize]
	cipherText = cipherText[aes.BlockSize:]
	stream := cipher.NewCFBDecrypter(block, iv)
	stream.XORKeyStream(cipherText, cipherText)
	return string(cipherText), nil
}
