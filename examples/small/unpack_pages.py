import asyncio

async def pages():
    for page in ([1, 2, 3], [4, 5], [6]):
        await asyncio.sleep(0.1)  # fetch the next page
        yield page

async def main():
    print([*page async for page in pages()])

asyncio.run(main())
