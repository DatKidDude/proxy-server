import socket
import threading
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8989
BUFSIZE = 4096

class ProxyStatusCodes:

    @staticmethod
    def build_403_response(hostname: str) -> str:
        """Return the forbidden 403 response
        
        Args:
            hostname (str): Website the user is connecting to
        
        Returns:
            str: HTTP header + body
        """
        body = f"Website not allowed: {hostname}"
        headers = (
            "HTTP/1.1 403 Forbidden\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "X-Content-Type-Options: nosniff\r\n"
            f"Content-Length: {len(body)}\r\n"
            "\r\n"
        )

        return headers + body
    
    @staticmethod
    def build_proxy_request(method: str, host: str) -> str:
        """Return the 200 response request
        
        Args:
            hostname (str): Website the user is connecting to
        
        Returns:
            str: HTTP header + body
        """
        headers = (
            f"{method}\r\n"
            f"{host}\r\n"
            "Connection: Keep-Alive\r\n"
            f"X-Forwarded-For: {HOST}\r\n"
            "\r\n"
        )
        
        return headers


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


def handle_connection(client_conn: socket.socket, addr: tuple) -> None:
    request = client_conn.recv(BUFSIZE)
    
    # Decode and parse the request into a list 
    request_parsed = request.decode().split("\r\n")

    # Extract the request method 
    method = request_parsed[0]

    # Extract the host portion
    host = request_parsed[1]
    hostname = urlparse(host).path.strip()

    print(f"Request made. Target: {hostname} Client: {HOST}:{PORT}")

    if forbidden_sites(hostname):
        proxy_request = ProxyStatusCodes.build_403_response(hostname)
        # Send the request back to the client
        client_conn.sendall(proxy_request.encode())
    else:
        proxy_request = ProxyStatusCodes.build_proxy_request(method, host)

        # Forward the proxy request
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_conn:
            remote_conn.connect((hostname, 80))
            remote_conn.sendall(proxy_request.encode("utf-8"))
            # Add a timeout so the program doesn't get stuck on recv()
            remote_conn.settimeout(3)

            try:
                while True:
                    data = remote_conn.recv(BUFSIZE)
                    if not data:
                        break
                    client_conn.sendall(data)
            except socket.timeout:
                pass

    client_conn.shutdown(socket.SHUT_RDWR)
    client_conn.close()


def main():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((HOST, PORT))
    proxy.listen()
    print(f"Starting proxy server on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = proxy.accept()
            print(f"Connection from {addr}")
            handle_connection(conn, addr)
    except KeyboardInterrupt:
        print("Keyboard interrupt...")
    finally:
        try:
            print("Shutting down proxy...")
            # Socket might already be closed or disconnected 
            proxy.shutdown(socket.SHUT_RDWR) 
        except OSError:
            pass
        finally:
            print("Closing proxy")
            proxy.close()

if __name__ == "__main__":
    main()