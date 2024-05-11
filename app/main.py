import asyncio
import argparse
import os
import gzip

CRLF = "\r\n"
directory = "/files/"

# TODO - refactor

async def produce_response(request: tuple) -> bytes:
    method, path, headers = request
    http_status = "200 OK"
    response_content = ""
    if method == "GET":
        if path == "/":
            pass
        elif "/echo/" in path:
            path_parts = path.split("/echo/")
            response_content = path_parts[1]
        elif "/user-agent" in path:
            response_content = headers["User-Agent"]
        elif "/files/" in path:
            pathArray = path.split("/")
            if len(pathArray) == 3:
                fileName = pathArray[2]
                path = directory + fileName
                if os.path.isfile(path):
                    with open(path, "rb") as file:
                        response_content = file.read()
                        contentLength = len(response_content)
                        response_content = (
                            f"HTTP/1.1 200 OK{CRLF}Content-Type: application/octet-stream{
                                CRLF}Content-Length: {contentLength}{CRLF}{CRLF}{response_content.decode()}"
                        )
                        print(f"----file content-----: {response_content}")
                        return response_content.encode("utf-8")
                else:
                    http_status = "404 Not Found"
            else:
                http_status = "404 Not Found"
        else:
            http_status = "404 Not Found"
        if "Accept-Encoding" in headers and "gzip" in headers["Accept-Encoding"]:
            response_content = gzip.compress(response_content.encode())
        response_headers = prepare_response_headers(http_status, len(response_content), headers)
        response_template = response_headers.encode()+response_content
        return response_template


def prepare_response_headers(http_status, response_content_len, req_headers) -> str:
    res_headers = f"HTTP/1.1 {http_status}{CRLF}Content-Type: text/plain{CRLF}Content-Length: {response_content_len}"
    if 'Accept-Encoding' in req_headers:
        encoding = req_headers['Accept-Encoding']
        if ',' in encoding:
            encoding = encoding.split(',')
        if 'gzip' in encoding:
            res_headers += f"{CRLF}Content-Encoding: gzip"
    res_headers += f"{CRLF}{CRLF}"
    return res_headers

async def connection_handler(   
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        addr = writer.get_extra_info('peername')
        while not reader.at_eof():
            payload = await reader.read(1024)
            print(f'received payload: {payload}')
            if not payload:
                break
            header_lines, body = payload.decode().split('\r\n\r\n')
            header_lines = header_lines.split(CRLF)
            method, path, _ = header_lines[0].split(' ')
            headers = {}
            for line in header_lines[1:]:
                if line:
                    key, value = line.split(': ')
                    headers[key] = value
            response = b''
            if method == 'POST':
                print(f'reading post {body}')
                pathArray = path.split('/')
                if len(pathArray) == 3:
                    fileName = pathArray[2]
                    path = directory + fileName
                    with open(path, 'w') as file:
                        file.write(body)
                    response = f'HTTP/1.1 201 Created{CRLF}Content-Type: text/plain{
                        CRLF}Content-Length: 0{CRLF}{CRLF}'
                    response = response.encode()
            if method == 'GET':
                response = await produce_response((method, path, headers))
            print(f'sending response: {response}')
            writer.write(response)
            await writer.drain()
            
            
            
            
    except asyncio.IncompleteReadError as e:
        print(f'Connection with {addr} was closed')
    except Exception as e:
        print(f'An error occurred for {addr}: {e}')
    finally:
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(connection_handler, 'localhost', 4221)
    print(f'Server running on {server.sockets[0].getsockname()}')
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory',type=str)
    args = parser.parse_args()
    if args.directory:
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
        directory = args.directory
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server stopped by ctrl-c')
