package client

import (
	"bufio"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"fmt"
	"net"
	"os"
)

var key = []byte("1234567890123456")

// StartClient initializes the chat client
func StartClient() {
	conn, err := net.Dial("tcp", "localhost:8080")
	if err != nil {
		fmt.Println("Error connecting to server:", err)
		return
	}
	defer conn.Close()

	go receiveMessages(conn)

	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Enter your username: ")
	username, _ := reader.ReadString('\n')
	conn.Write([]byte(username))

	// Send messages
	for {
		fmt.Print("Enter message: ")
		message, _ := reader.ReadString('\n')
		encryptedMessage, err := encryptMessage([]byte(message))
		if err != nil {
			fmt.Println("Error encrypting message:", err)
			continue
		}
		conn.Write(encryptedMessage)
	}
}

func receiveMessages(conn net.Conn) {
	for {
		buffer := make([]byte, 1024)
		n, err := conn.Read(buffer)
		if err != nil {
			fmt.Println("Disconnected from server")
			break
		}

		decryptedMessage, err := decryptMessage(buffer[:n])
		if err != nil {
			fmt.Println("Error decrypting message:", err)
			continue
		}

		fmt.Println("Message from server:", decryptedMessage)
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
