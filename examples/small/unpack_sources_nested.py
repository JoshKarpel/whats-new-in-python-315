import asyncio

async def numbers(n):
    for i in range(n):
        yield i

async def sources():
    yield numbers(2)
    yield numbers(3)

async def main():
    print([n async for source in sources() async for n in source])

asyncio.run(main())
