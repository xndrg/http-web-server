#!/usr/bin/python3

import asyncio
import socket
import logging
import sys

MAX_CLIENTS = 4
ENCODING = "ISO-8859-1"

logging.basicConfig(
    level = logging.INFO,
    format = "%(levelname)s: %(message)s"
)

def main() -> None:
    if len(sys.argv) != 2:
        print_usage()
        exit(64)

    try:
        port = int(sys.argv[1])
        asyncio.run(serve(port))
    except ValueError:
        logging.error("Port number should be an integer!")
        exit(64)

def print_usage():
    print("Usage: http-server.py [PORT]")
    print("Simple http server written from scratch using python sockets API")

async def serve(port: int) -> None:
    logging.info(f"Starting http server on port {port}")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, None)
    server.bind(("localhost", port))
    server.listen(MAX_CLIENTS);
    server.setblocking(False);

    loop = asyncio.get_event_loop()

    while True:
        client, _ = await loop.sock_accept(server)
        loop.create_task(handle_client(client))

async def handle_client(client: socket.socket):
    client_ip, client_port = client.getpeername()
    logging.info(f"Got connection {client_ip}:{client_port}")

    loop = asyncio.get_event_loop()

    request = (await loop.sock_recv(client, 1024)).decode(ENCODING)
    response = make_response(request)

    await loop.sock_sendall(client, response)

    client.close()

def make_response(request: str) -> bytes:
    try:
        request_method, file_path = parse_request(request)
        response = response_file(file_path)
        return response.encode(ENCODING)
    except AssertionError:
        response = "HTTP/1.1 400 Bad Request\r\n\r\n"
        logging.error("Bad request: unsupported request method or file format")
        return response.encode(ENCODING)
    except IndexError:
        response = "HTTP/1.1 400 Bad Request\r\n\r\n"
        logging.error("Bad request: could not parse request")
        return response.encode(ENCODING)

def parse_request(request: str) -> (str, str):
    # Ignoring all the payload
    headers_index = request.find("\r\n\r\n")
    # Split by each individual header
    headers = request[:headers_index].split("\r\n")

    start_line = headers[0]
    separator = start_line.find("/")
    request_method = start_line[:separator].strip()
    file_path = "." + start_line[separator:].split()[0]
    
    # Raise exception if method isn't `GET` 
    assert request_method == "GET"
    
    return request_method, file_path

def response_file(file_path: str) -> str:
    file_path = "./index.html" if file_path == "./" else file_path
    file_type = file_path.split(".")[2]
        
    assert file_type == "html" or file_type == "txt"
    
    content_type = "text/html" if file_type == "html" else "text/plain"

    try:
        file = open(file_path, "r")
        chars = file.read()
        length = len(chars)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {length}\r\nConnection: close\r\n\r\n{chars}"
        file.close()
        return response
    except FileNotFoundError:
        logging.warning(f"File not found: `{file_path}`")
        file = open("not_found.html", "r")
        chars = file.read()
        length = len(chars)
        response = f"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nContent-Length: {length}\r\nConnection: close\r\n\r\n{chars}"
        file.close()
        return response

if __name__ == "__main__": main()
