received = bytearray(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nhi")

status_line = received.take_bytes(received.index(b"\r\n") + 2)

print(status_line)
print(received)
