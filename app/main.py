import asyncio
import argparse
import os

CRLF = "\r\n"
args = None


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
                directory = args.directory
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
        headers = (
            f"HTTP/1.1 {http_status}{CRLF}"
            f"Content-Type: text/plain{CRLF}Content-Length: {len(response_content)}{CRLF}{CRLF}")
        response_template = f"{headers}{response_content}"
        return response_template.encode()  # "utf-8" default encoding


async def main():
    server = await asyncio.start_server(connection_handler, "localhost", 4221)
    print(f"Server running on {server.sockets[0].getsockname()}")
    async with server:
        await server.serve_forever()


async def connection_handler(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        addr = writer.get_extra_info("peername")
        while not reader.at_eof():
            payload = await reader.read(1024)
            print(f"received payload: {payload}")
            if not payload:
                break
            header_lines, body = payload.decode().split("\r\n\r\n")
            header_lines = header_lines.split("\r\n")
            method, path, _ = header_lines[0].split(" ")
            headers = {}
            for line in header_lines[1:]:
                if line:
                    key, value = line.split(": ")
                    headers[key] = value
            if method == "POST":
                print(f"reading post {body}")
                pathArray = path.split("/")
                if len(pathArray) == 3:
                    directory = args.directory
                    fileName = pathArray[2]
                    path = directory + fileName
                    with open(path, "w") as file:
                        file.write(body)
                    response = f"HTTP/1.1 201 OK{CRLF}Content-Type: text/plain{
                        CRLF}Content-Length: 0{CRLF}{CRLF}"
                    writer.write(response.encode())
                    await writer.drain()
            if method == "GET":
                response = await produce_response((method, path, headers))
                writer.write(response)
                await writer.drain()
    except asyncio.IncompleteReadError as e:
        print(f"Connection with {addr} was closed")
    except Exception as e:
        print(f"An error occurred for {addr}: {e}")
    finally:
        writer.close()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", help="serving files dir")
    args = parser.parse_args()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
