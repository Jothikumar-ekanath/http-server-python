import asyncio


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
            print(f"received command: {payload}")
            writer.write(b"HTTP/1.1 200 OK\r\n\r\n")
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
