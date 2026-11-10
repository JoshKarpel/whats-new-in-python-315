import time
from datetime import datetime

def parse(line):
    when, user = line.split()
    return datetime.fromisoformat(when), user

def unique_users(events):
    seen = []
    for _, user in events:
        if user not in seen:
            seen.append(user)
    return seen

lines = [f"2026-11-09T12:{i // 60 % 60:02}:{i % 60:02} user{i}" for i in range(3_000)] * 33
start = time.perf_counter()
users = unique_users([parse(line) for line in lines])
print(f"{len(users):,} users in {time.perf_counter() - start:.2f} s")
