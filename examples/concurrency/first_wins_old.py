import asyncio

DELAYS = {"us": 0.3, "eu": 0.1, "ap": 0.5}

async def fetch(mirror):
    await asyncio.sleep(DELAYS[mirror])
    return f"payload from {mirror}"

class Done(Exception):
    pass

async def first_wins(mirrors):
    winner = None

    async def attempt(mirror):
        nonlocal winner
        winner = (mirror, await fetch(mirror))
        raise Done

    try:
        async with asyncio.TaskGroup() as tg:
            for mirror in mirrors:
                tg.create_task(attempt(mirror))
    except* Done:
        pass
    return winner

print(asyncio.run(first_wins(["us", "eu", "ap"])))
