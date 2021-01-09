import socket
import threading
import struct
import time

hostname = socket.gethostname()
host = socket.gethostbyname(hostname)

multicast_addr = '224.1.1.1'

multicast_server_client_port = 3000

tcp_IP = ""
tcp_PORT = ""
client = ""

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
            client.close()
            print("An error occurred!")
            timeout_counter = 0
            timeout_max = 10 

            while timeout_counter <= timeout_max:
                print("Trying to reconnect {}/{}...".format(timeout_counter, timeout_max))
                time.sleep(1)
                timeout_counter += 1
            
            client = reconnect()

            break


def write(client):
    while True:
        try:
            message = f'{nickname}: {input("")}'
            client.send(message.encode('ascii'))
        except:
            #print("reconnected")
            #time.sleep(8)
            #client = reconnect()
            #client.send(nickname.encode('ascii'))
            break


def set_connection():
    tcp_address, tcp_port = ask_host()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((tcp_address, tcp_port))
    return tcp_address, tcp_port, client


def create_threads(client):
    write_thread = threading.Thread(target=write, args=(client,))
    write_thread.start()
    receive_thread = threading.Thread(target=receive, args=(client,))
    receive_thread.start()


def reconnect():
    tcp, port, client = set_connection()
    create_threads(client)
    return client


tcp_IP, tcp_PORT, client = set_connection()
create_threads(client)