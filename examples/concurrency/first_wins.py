import asyncio

DELAYS = {"us": 0.3, "eu": 0.1, "ap": 0.5}

async def fetch(mirror):
    await asyncio.sleep(DELAYS[mirror])
    return f"payload from {mirror}"

async def first_wins(mirrors):
    winner = None

    async def attempt(tg, mirror):
        nonlocal winner
        winner = (mirror, await fetch(mirror))
        tg.cancel()

    async with asyncio.TaskGroup() as tg:
        for mirror in mirrors:
            tg.create_task(attempt(tg, mirror))
    return winner

print(asyncio.run(first_wins(["us", "eu", "ap"])))
