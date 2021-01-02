import socket
import threading
import struct


hostname = socket.gethostname()
host = socket.gethostbyname(hostname)
# udp_port = 5566

multicast_addr = '224.0.0.1'

multicast_server_client_port = 3000


def ask_host():
    multicast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_sender.sendto("2222".encode('ascii'), (multicast_addr, multicast_server_client_port))
    receive_server_message, address = multicast_sender.recvfrom(1024)
    receive_server_message_splitted = receive_server_message.decode('ascii').split(",")
    address_tcp = int(receive_server_message_splitted[2])
    port = str(receive_server_message_splitted[1])
    return port, address_tcp


tcp_address, tcp_port = ask_host()

print(tcp_address, tcp_port)
nickname = input("Wähle einen Benutzernamen: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((tcp_address, tcp_port))


def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
            else:
                print(message)
        except:
            print("An error occurred!")
            client.close()
            ask_host()
            break

def write():
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('ascii'))



receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()