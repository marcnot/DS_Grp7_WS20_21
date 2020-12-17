import socket

# Create a UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server application IP address and port
server_address = '127.0.0.1'
server_port = 10001

# Buffer size
buffer_size = 1024

while True:

    message = input(">> ")
    message = message.encode()

    client_socket.sendto(message, (server_address, server_port))

    data, ip = client_socket.recvfrom(buffer_size)

    print("{}: {}".format(ip, data.decode()))
