import socket
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8989

def handle_connection(conn, addr):
    request = conn.recv(4096)
    
    # Decode and parse the request into a list 
    request_parsed = request.decode().split("\r\n")

    # Extract the request method 
    method = request_parsed[0]

    # Extract the host portion
    host = request_parsed[1]
    hostname = urlparse(host).path.strip()

    # Modify the <method> request
    proxy_request = method + "\r\n"
    proxy_request += host + "\r\n"
    proxy_request += f"Connection: Keep-Alive\r\n"
    proxy_request += f"X-Forwarded-For: {HOST}\r\n"
    proxy_request += "\r\n"

    # Forward the proxy request
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy:
        proxy.connect((hostname, 80))
        proxy.sendall(proxy_request.encode("utf-8"))
        proxy.settimeout(3)

        try:
            while True:
                data = proxy.recv(4096)
                if not data:
                    break
                conn.sendall(data)
        except socket.timeout:
            pass
    
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Starting server...")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Connection from {addr}")
            handle_connection(conn, addr)
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