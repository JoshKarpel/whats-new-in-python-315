import os
from concurrent.futures import ProcessPoolExecutor


def crash():
    os._exit(3)


if __name__ == "__main__":
    with ProcessPoolExecutor(1) as pool:
        try:
            pool.submit(crash).result()
        except Exception as error:
            print(f"{type(error).__name__=}")
            print(f"{error.__cause__=}")
