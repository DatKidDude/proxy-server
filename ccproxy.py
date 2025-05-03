import socket
import threading
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8989
BUFSIZE = 4096

def forbidden_sites(hostname: str) -> bool:
    """Check if the hostname is in the forbidden-hosts.txt file
    
    Args:
        hostname (str): Website the user is connecting to
    
    Returns:
        bool: True if site is in the forbidden-hosts.txt else False
    """
    with open("forbidden-hosts.txt", "r") as file:
        forbidden_list = [line.strip("\n") for line in file.readlines()]
    
    if hostname in forbidden_list:
        return True
    else:
        return False


def handle_connection(conn: socket.socket, addr: tuple) -> None:
    request = conn.recv(BUFSIZE)
    
    # Decode and parse the request into a list 
    request_parsed = request.decode().split("\r\n")

    # Extract the request method 
    method = request_parsed[0]

    # Extract the host portion
    host = request_parsed[1]
    hostname = urlparse(host).path.strip()

    print(f"Request made. Target: {hostname} Client: {HOST}:{PORT}")

    if forbidden_sites(hostname):
        body = f"Website not allowed: {hostname}"
        proxy_request = "HTTP/1.1 403 Forbidden\r\n"
        proxy_request += "Content-Type: text/plain; charset=utf-8\r\n"
        proxy_request += "X-Content-Type-Options: nosniff\r\n"
        proxy_request += f"Content-Length: {len(body)}\r\n"
        proxy_request += "\r\n"
        proxy_request += body

        # Send the request back to the client
        conn.sendall(proxy_request.encode())
    else:
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
            # Add a timeout so the program doesn't get stuck on recv()
            proxy.settimeout(3)

            try:
                while True:
                    data = proxy.recv(BUFSIZE)
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
    print(f"Starting proxy server on {HOST}:{PORT}")

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