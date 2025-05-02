import socket

HOST = "127.0.0.1"
PORT = 8989

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Starting server...")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Connection from {addr}")
            data = conn.recv(4096)
            print(data.decode())
    except KeyboardInterrupt:
        print("Keyboard interrupt...")
    finally:
        try:
            print("Shutting down server...")
            # Socket might already be closed or disconnected 
            server.shutdown(socket.SHUT_RDWR) 
        except OSError:
            pass
        finally:
            print("Closing server")
            server.close()

if __name__ == "__main__":
    main()