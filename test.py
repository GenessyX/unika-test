import asyncio
import argparse

PORT = 8888
HOST = "127.0.0.1"


async def tcp_echo_client(message: str):
    reader, writer = await asyncio.open_connection(HOST, PORT)
    writer.write(message.encode("utf-8"))
    await writer.drain()
    data = await reader.read(100)
    print(f"Data: {data}")
    writer.close()
    await writer.wait_closed()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--quit", action="store_true", help="Send process exit event")
    args = parser.parse_args()
    tasks = []
    if args.quit:
        await tcp_echo_client("quit\n")
    for _ in range(5):
        tasks.append(tcp_echo_client("test message\n"))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
