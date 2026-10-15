import asyncio
import os
import signal

async def worker(n):
    try:
        while True:
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        print(f"worker {n} cleaning up")
        raise

async def main():
    loop = asyncio.get_running_loop()
    async with asyncio.TaskGroup() as tg:
        loop.add_signal_handler(signal.SIGTERM, tg.cancel)
        for n in range(3):
            tg.create_task(worker(n))
        loop.call_later(0.2, os.kill, os.getpid(), signal.SIGTERM)
    print("shut down cleanly")

asyncio.run(main())
