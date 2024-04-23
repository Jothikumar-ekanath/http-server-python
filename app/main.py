import asyncio

CRLF = "\r\n"
async def parse_http_request(payload: bytes) -> tuple:
    lines = payload.decode().split(CRLF)
    method, path, _ = lines[0].split(" ")
    headers = {}
    for line in lines[1:]:
        if line:
            key, value = line.split(": ")
            headers[key] = value
    return (method, path, headers)



async def produce_response(request: tuple) -> bytes:
    method, path, headers = request
    http_status = "200 OK"
    response_content = ""
  
    if method == "GET":
        if path == "/":
            pass
        elif  "/echo/" in path:
            path_parts = path.split("/echo/")
            response_content = path_parts[1]
        elif "/user-agent" in path:
            response_content = headers["User-Agent"]
        else:
            http_status = "404 Not Found"
        headers = (
            f"HTTP/1.1 {http_status}{CRLF}"
            f"Content-Type: text/plain{CRLF}Content-Length: {len(response_content)}{CRLF}")
        response_template = f"{headers}{CRLF}{response_content}(CRLF)"
        return response_template.encode()
       
async def main():
    server = await asyncio.start_server(connection_handler, "localhost", 4221)
    print(f"Server running on {server.sockets[0].getsockname()}")
    async with server:
        await server.serve_forever()

async def connection_handler(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter):    
    try:
        addr = writer.get_extra_info("peername")
        while True:
            payload = await reader.read(1024)
            print(f"received request: {payload}")
            if not payload:
                break
            request = await parse_http_request(payload)
            response = await produce_response(request)
            writer.write(response)
            await writer.drain()
    except Exception as e:
        print(f"An error occurred for {addr}: {e}")
    finally:
        writer.close()
   
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
