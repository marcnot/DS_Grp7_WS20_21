import threading
import socket
import struct
import time
import json
import pickle

clients = []
servers = []
nicknames = []

server_dic = {}


hostname = socket.gethostname()
host_ip = socket.gethostbyname(hostname)
tcp_port = 5555
tcp_server_port = 5588

multicast_addr = '224.1.1.1'

bind_addr = '0.0.0.0'

multicast_client_server_port = 3000
multicast_server_server_port = 4000

client_server_address = (host_ip, multicast_client_server_port)
server_server_address = (host_ip, multicast_server_server_port)

lead_server = True


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
membership = socket.inet_aton(multicast_addr) + socket.inet_aton(bind_addr)

###############################################################################

election_port = 10001
buffersize = 1024
neighbour_elect = "192.168.178.105"

election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
election_socket.bind((host_ip, election_port))

print("Election Socket is running at {}.{}".format(host_ip, election_port))


while True:
    data, address = election_socket.recvfrom(buffersize)
    print((data).decode("utf-8"))
    election_socket.sendto(("Hi zweiter PC").encode("utf-8"), (neighbour_elect, election_port))
    time.sleep(5)

###############################################################################

def send_clients():
    while True:
        multicast_client_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        multicast_client_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        multicast_client_listener.bind(client_server_address)
        client_message, address = multicast_client_listener.recvfrom(1024)
        new_values = client_message.decode('ascii').split(",")
        if new_values[0] == '2222':
            multicast_client_listener.sendto(f'1112,{host_ip},{tcp_port}'.encode('ascii'), address)
            multicast_client_listener.close()
        else:
            print("Wrong client identifier")


def send_server():
    while True:
        multicast_server_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        multicast_server_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        multicast_server_listener.bind(server_server_address)
        server_message, address = multicast_server_listener.recvfrom(1024)
        server_message_decode = server_message.decode("ascii")
        if server_message_decode == '1111':
            multicast_server_listener.sendto("1112".encode('ascii'), address)
            #servers.append(address)
            #print("SERVERLISTE:")
            #print(servers)
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


def handle_backup_server(backup_server):
    while True:
        try:
            backup_server.send("Your Data".encode("ascii"))
            time.sleep(5)
        except:
            #servers.remove(backup_server.getpeername())
            backup_server_name = backup_server.getpeername()
            server_dic.pop(backup_server_name[1])
            print("Serverlist nach Backupserver disconnect")
            print(server_dic)
            backup_server.close
            print("Server " + str(backup_server.getpeername()) + " disconnected")
            break


def receive_backup_server():
    while True:
        backup_server, address = server_server.accept()
        #servers.append(address)
        server_dic[address[1]] = {"server_ip" : address[0], "is_leader" : False}
        print("SERVERLISTE:")
        print(server_dic)
        backup_server.send('Connected to the server cluster'.encode('ascii'))
        backup_thread = threading.Thread(target=handle_backup_server, args=(backup_server,))
        backup_thread.start()


def start_server():
    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
    server.bind((host_ip, tcp_port))
    server.listen()
    server_server.bind((host_ip, tcp_server_port))
    server_server.listen()
    print("Server is listening...")
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()
    print("Ready for Servers")
    receive_backup_thread = threading.Thread(target=receive_backup_server)
    receive_backup_thread.start()
    print("DONE")


def receive_server(backup_server):
    while True:
        try:
            backup_server.send("BEAT".encode('ascii'))
            message = backup_server.recv(1024).decode('ascii')
            print(message)
        except:
            print("An error occurred!")
            backup_server.close()
            break

def ask_server():
    multicast_server_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_server_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_server_sender.sendto("1111".encode('ascii'), (multicast_addr, multicast_server_server_port))
    multicast_server_sender.settimeout(0.5)
    try:
        receive_server_message, address = multicast_server_sender.recvfrom(1024)
        tcp_server_ip = str(address[0])
        print("recv.Server")
        print(tcp_server_ip)
        start_backup_server(tcp_server_ip)
    except:
        print("Start Server")
        start_server()


def start_backup_server(tcp_server_ip):
    backup_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backup_server.connect((tcp_server_ip, tcp_server_port))
    while True:
        try:
            data = backup_server.recv(1024).decode('utf-8')
            print(data)
        except:
            print("An error occurred!")
            backup_server.close()
            ask_server()
            break


ask_server()


