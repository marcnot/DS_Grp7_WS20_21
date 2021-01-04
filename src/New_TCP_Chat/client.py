import socket
import threading
import struct
import time

hostname = socket.gethostname()
host = socket.gethostbyname(hostname)

multicast_addr = '224.1.1.1'

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


nickname = input("Wähle einen Benutzernamen: ")


def receive(client):
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
            time.sleep(5)
            reconnect()
            break


def write(client):
    while True:
        try:
            message = f'{nickname}: {input("")}'
            client.send(message.encode('ascii'))
        except:
            print("reconnected")


def connect():
    tcp_address, tcp_port = ask_host()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((tcp_address, tcp_port))
    print("TEst")
    write_thread = threading.Thread(target=write, args=(client,))
    write_thread.start()
    print("TEst 2")
    receive_thread = threading.Thread(target=receive, args=(client,))
    receive_thread.start()
    print("TEst 3")

def reconnect():

    connect()


connect()