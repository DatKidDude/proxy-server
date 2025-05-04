import socket
import threading
import logging
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8989
BUFSIZE = 4096

# Logging config settings
logging.basicConfig(
    filename="ccproxy.log",
    encoding="utf-8",
    filemode="w",
    format="{asctime} {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO,
)

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
            f"Host: {host}\r\n"
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


def pipe(src: socket.socket, dst: socket.socket) -> None:
    """Read data from the src socket and write data back to the destination socket
    
    Args:
        src (socket.socket): Socket being read from
        dst (socket.socket): Socket being written to
    
    Returns:
        None
    """
    try:
        while True:
            data = src.recv(BUFSIZE)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        src.close()
        dst.close()    


def handle_connection(client_conn: socket.socket, addr: tuple) -> None:
    request = client_conn.recv(BUFSIZE)
    
    # Decode and parse the request into a list 
    request_parsed = request.decode().split("\r\n")

    # Get the full request line
    request_line = request_parsed[0]

    # Extract the request method and the host
    method, target, _ = request_parsed[0].split()

    if method == "CONNECT":
        host, port = target.split(":")
        port = int(port)
    else:
        port = 80
        # Extract the host portion
        _, host = request_parsed[1].split()    
   
    print(f"Request made. Target: {host} Client: {HOST}:{PORT}")
    logging.info(f"Client: {HOST}:{PORT} Request URL: {request_line}")

    if forbidden_sites(host):
        proxy_request = ProxyStatusCodes.build_403_response(host)
        # Send the request back to the client
        client_conn.sendall(proxy_request.encode())
        logging.info(f"{HOST}:{PORT} 403 Forbidden")
        client_conn.close()
        return
    
    # Creates threads if a HTTPS tunnel needs to be made
    if method == "CONNECT": 
        try:
            remote_conn = socket.create_connection((host, port))
        except Exception as e:
            client_conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            client_conn.close()
            return

        # Tell the client the tunnel is ready
        client_conn.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        logging.info(f"{HOST}:{PORT} 200 OK")

        # Start piping in both directions
        threading.Thread(target=pipe, args=(client_conn, remote_conn)).start()
        threading.Thread(target=pipe, args=(remote_conn, client_conn)).start()
    else:
        proxy_request = ProxyStatusCodes.build_proxy_request(request_line, host)
        
        # Forward the proxy request
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_conn:
            remote_conn.connect((host, port))
            remote_conn.sendall(proxy_request.encode("utf-8"))
            # Add a timeout so the program doesn't get stuck on recv()
            remote_conn.settimeout(3)
            pipe(remote_conn, client_conn)


def main():
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind((HOST, PORT))
    proxy.listen()
    print(f"Starting proxy server on {HOST}:{PORT}")
    logging.info(f"Starting proxy server on {HOST}:{PORT}")

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