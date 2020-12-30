import socket
import threading
import struct


hostname = socket.gethostname()
host = socket.gethostbyname(hostname)
udp_port = 5566

multicast_addr = '224.0.0.1'
multicast_port = 3000

nickname = input("Wähle einen Benutzernamen: ")

def ask_host():
    multicast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_sender.sendto(f'991199,{host},{udp_port}'.encode('ascii'), (multicast_addr, multicast_port))
    multicast_sender.close()

    # broadcast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # broadcast_sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # broadcast_sender.sendto(f'991199,{host},{udp_port}'.encode('ascii'), ('255.255.255.255', 5544))
    # broadcast_sender.close()


def recv_host():
    broadcast_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_listener.bind(('', 5566))
    message = broadcast_listener.recv(1024).decode('ascii')
    broadcast_listener.close()
    new_values = message.split(",")
    address = str(new_values[0])
    port = int(new_values[1])
    return port, address


ask_host()
tcp_port, tcp_address = recv_host()

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
            break

def write():
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('ascii'))



receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()