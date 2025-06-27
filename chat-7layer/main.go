package main

import (
	"flag"
	"fmt"
	"hello/client"
	"hello/server"
	"os"
)

func main() {
	mode := flag.String("mode", "server", "Mode to run: 'server' or 'client'")
	flag.Parse()

	switch *mode {
	case "server":
		fmt.Println("Starting server...")
		server.StartServer()
	case "client":
		fmt.Println("Starting client...")
		client.StartClient()
	default:
		fmt.Println("Invalid mode. Use 'server' or 'client'.")
		os.Exit(1)
	}
}
