from datetime import datetime

def parse(line):
    when, user = line.split()
    return datetime.fromisoformat(when), user

def unique_users(events):
    seen = set()
    for _, user in events:
        if user not in seen:
            seen.add(user)
    return seen

lines = [f"2026-11-09T12:00:{i % 60:02} user{i % 3_000}" for i in range(99_000)]
print(f"{len(unique_users(map(parse, lines))):,} users")
