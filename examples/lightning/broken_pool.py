import os
from concurrent.futures import ProcessPoolExecutor


def crash():
    os._exit(3)


if __name__ == "__main__":
    with ProcessPoolExecutor(1) as pool:
        try:
            pool.submit(crash).result()
        except Exception as error:
            print(type(error).__name__)
            print("caused by:", repr(error.__cause__))
