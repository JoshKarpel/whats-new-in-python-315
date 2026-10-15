def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)


def sieve(n):
    is_prime = [True] * (n + 1)
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    return sum(is_prime)


for _ in range(10):
    fib(22)
    sieve(200_000)
