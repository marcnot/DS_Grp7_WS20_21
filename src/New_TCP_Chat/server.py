import threading
import socket
import struct

clients = []
servers = []
nicknames = []

hostname = socket.gethostname()
tcp_host = socket.gethostbyname(hostname)
tcp_port = 5555

multicast_addr = '224.0.0.1'
bind_addr = '0.0.0.0'

multicast_client_server_port = 3000
multicast_server_server_port = 4000
multicast_server_server_recv_port = 4040
multicast_client_server_recv_port = 3030

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
membership = socket.inet_aton(multicast_addr) + socket.inet_aton(bind_addr)


def send_clients():
    while True:
        multicast_client_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        multicast_client_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        multicast_client_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_client_listener.bind((bind_addr, multicast_client_server_port))
        client_message = multicast_client_listener.recv(1024).decode('ascii')
        new_values = client_message.split(",")
        if new_values[0] == '2222':
            print(client_message)
            multicast_client_listener.sendto(f'1112,{tcp_host},{tcp_port}'.encode('ascii'), (multicast_addr, multicast_client_server_recv_port))
            multicast_client_listener.close()
        else:
            print("Wrong client identifier")


def send_server():
    while True:
        multicast_server_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        multicast_server_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        multicast_server_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_server_listener.bind((bind_addr, multicast_server_server_port))
        server_message = multicast_server_listener.recv(1024).decode('ascii')
        if server_message == '1111':
            print(server_message)
            multicast_server_listener.sendto("1112".encode('ascii'), (multicast_addr, multicast_server_server_recv_port))
            multicast_server_listener.close()
        else:
            print("Wrong server identifier")


def multicast(message):
    for client in clients:
        client.send(message)


def handle(client):
    while True:
        try:
            message = client.recv(1024)
            multicast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close
            nickname = nicknames[index]
            multicast(f'{nickname} has left the chat'.encode('ascii'))
            nicknames.remove(nickname)
            break


def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')

        nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname of the CLient is {nickname}!')
        multicast(f'Username {nickname} has joined the chat'.encode('ascii'))
        client.send('Connected to the server'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


def start_server():
    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
    server.bind((tcp_host, tcp_port))
    server.listen()
    print("Server is listening...")
    receive()

def start_backup_server():
    while True:
        backup_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        backup_server.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        backup_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        backup_server.bind((bind_addr, multicast_server_server_port+1))
        print("Start-backup_server")
        server_message = backup_server.recv(1024).decode('ascii')


def ask_server():
    multicast_server_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_server_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_server_sender.sendto("1111".encode('ascii'), (multicast_addr, multicast_server_server_port))
    multicast_server_sender.close()

def recv_server():
    multicast_reciever = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    multicast_reciever.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    multicast_reciever.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicast_reciever.settimeout(2.5)
    multicast_reciever.bind((bind_addr, multicast_server_server_recv_port))
    try:
        receive_server_message = multicast_reciever.recv(1024).decode('ascii')
        print(receive_server_message)
        print("recv.Server")
        start_backup_server()
    except:
        print("Test")
        multicast_reciever.close
        start_server()

#def heartbeat():

def check_server():
    ask_server()
    recv_thread = threading.Thread(target=recv_server())
    recv_thread.start()


check_server()

