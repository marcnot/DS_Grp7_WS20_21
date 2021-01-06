#rechts
import threading
import socket
import struct
import time
import json
import ipaddress

clients = []
servers = []
nicknames = []

server_dic = {}

hostname = socket.gethostname()
host_ip = socket.gethostbyname(hostname)
tcp_port = 5555
tcp_server_port = 5588

multicast_addr = '224.1.1.1'

global leader
leader = False

multicast_client_server_port = 3000
multicast_server_server_port = 4000
election_port = 4050
backup_port = 10001
test_port = 10002
heartbeat_port = 4060

buffersize = 1024

client_server_address = (host_ip, multicast_client_server_port)
server_server_address = (host_ip, multicast_server_server_port)

##Socket definition
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
heartbeat_socket.settimeout(2)

##Socketbinds
election_socket.bind((host_ip, election_port))
heartbeat_socket.bind((host_ip, heartbeat_port))

##############################RING FORMING#################################

neighbour_elect = ["192.168.178.26", "192.168.178.50"]  # eventuell in servers umbennen
election_message = {
    "mid": host_ip,
    "isLeader": False} #eingefügt von Patrick passt das so???
participant = False


def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    # print(sorted_binary_ring)
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    # print(sorted_ip_ring)
    return sorted_ip_ring


def get_neighbour(ring, current_node_ip, direction='left'):
    current_node_index = ring.index(current_node_ip) if current_node_ip in ring else -1
    if current_node_index != -1:
        if direction == 'left':
            if current_node_index + 1 == len(ring):
                return ring[0]
            else:
                return ring[current_node_index + 1]
        else:
            if current_node_index == 0:
                return ring[len(ring) - 1]
            else:
                return ring[current_node_index - 1]
    else:
        return None


ring = form_ring(servers)
neighbour = get_neighbour(ring, host_ip, 'right')

##########################LEADER ELECTION###################################
print("Election Socket is running at {}:{}".format(host_ip, election_port))

# election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))
# election_message, address = election_socket.recvfrom(buffersize)
leader_uid = ""


def leader_election(server_host_ip, participant, leader_uid):
    election_message, address = election_socket.recvfrom(buffersize)
    election_message = json.loads(election_message.decode())

    # election_IP = ipaddress.IPv4Address(election_message["mid"])
    # election_host_IP = ipaddress.IPv4Address(server_host_ip)

    neighbour = get_neighbour(form_ring(servers), host_ip, 'right')
    print("NACHBAR")
    print(neighbour)

    # election_message = json.loads(election_message)
    election_IP = ipaddress.IPv4Address(election_message["mid"])
    election_host_IP = ipaddress.IPv4Address(server_host_ip)

    #i = 0

    #while i < len(servers) + 1:

    print(election_message)
    #print(i)

    if election_message['isLeader']:
        print("if1 {}".format(neighbour))
        leader_uid = election_message["mid"]
        # forward received election message to left neighbour
        participant = False
        election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))

    if election_IP < election_host_IP and not participant:  # 192.168.178.23
        print("if2 {}".format(neighbour))
        new_election_message = {
            "mid": str(election_host_IP),
            "isLeader": False}
        participant = True
        # send received election message to left neighbour
        election_socket.sendto(json.dumps(new_election_message).encode(), (neighbour, election_port))
    elif election_IP > election_host_IP:
        print("elif1 {}".format(neighbour))
        # send received election message to left neighbour
        participant = False
        election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))
    elif election_IP == election_host_IP:
        print("elif2 {}".format(neighbour))
        leader_uid = str(election_host_IP)
        print("leaderUID")
        print(leader_uid)
        new_election_message = {
            "mid": str(election_host_IP),
            "isLeader": True}
        election_message["isLeader"] = True
        # send new election message to left neighbour
        participant = False
        global leader
        leader = True
        print(leader_uid)
        #restart()
        heartbeat_send()
        print("restart")
        election_socket.sendto(json.dumps(new_election_message).encode(), (neighbour, election_port))

        #i += 1

    return (leader_uid)


# leader_uid = leader_election (election_message, host_ip, participant, leader_uid)
print(leader_uid)


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
        multicast_server_listener.sendto(host_ip.encode('ascii'), address)

        if address[0] not in servers:
            servers.append(address[0])
            if len(servers) == 2:
                heartbeat_send()

        print("Servers in send Server: ")
        print(servers)
        time.sleep(2)
        multicast_server_listener.close()


def server_collector():
    while True:
        server_collector_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        server_collector_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        server_collector_listener.bind((host_ip, test_port))
        collect_message, address = server_collector_listener.recvfrom(1024)
        server_collector_listener.sendto(host_ip.encode('ascii'), address)
        server_collector_listener.close()


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


def handle_backups():
    while True:
        handle_backup_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        handle_backup_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        handle_backup_socket.bind((host_ip, backup_port))
        server_message, address = handle_backup_socket.recvfrom(1024)
        print(server_message)
        print(address)


def start_server():
    global leader
    leader = True

    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
    collector_thread = threading.Thread(target=server_collector)
    collector_thread.start()
    server.bind((host_ip, tcp_port))
    server.listen()
    print("Server is listening...")
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()
    print("Ready for Servers")
    receive_backup_thread = threading.Thread(target=handle_backups)
    receive_backup_thread.start()
    server_heartbeat_thread = threading.Thread(target=heartbeat_recv)
    server_heartbeat_thread.start()

    election_thread = threading.Thread(target=leader_election, args=(host_ip, participant, leader_uid,))
    election_thread.start()
    print("DONE")

def restart():
    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server.bind((host_ip, tcp_port))
    server.listen()
    print("Server is listening...")
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()
    print("Ready for Servers")
    receive_backup_thread = threading.Thread(target=handle_backups)
    receive_backup_thread.start()


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
    servers.append(host_ip)

    multicast_server_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_server_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_server_sender.sendto(host_ip.encode('ascii'), (multicast_addr, multicast_server_server_port))
    multicast_server_sender.settimeout(0.5)
    try:
        receive_server_message, address = multicast_server_sender.recvfrom(1024)
        print("Start Backup Server")
        global leader
        leader = False
        start_backup_server()
    except:
        print("Start Server")
        start_server()


def start_backup_server():
    collect_servers()
    server_collector_thread = threading.Thread(target=server_collector)
    server_collector_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
    server_heartbeat_thread = threading.Thread(target=heartbeat_recv)
    server_heartbeat_thread.start()
    election_thread = threading.Thread(target=leader_election, args=(host_ip, participant, leader_uid,))
    election_thread.start()


def heartbeat_send():
    neighbour = get_neighbour(form_ring(servers), host_ip, 'right')
    print(neighbour)
    heartbeat_socket.sendto(str(host_ip).encode(), (neighbour, heartbeat_port))


def heartbeat_recv():
    while True:
        if len(servers) > 1:
            try:
                beat, address = heartbeat_socket.recvfrom(buffersize)
                #print(beat)
                #print("Leader " + str(leader))
                heartbeat_send()
            except:
                collect_servers()
                neighbour = get_neighbour(form_ring(servers), host_ip, 'right')
                print("SERVERLISTE HEARTBEAT:")
                print(servers)
                print("LEADER:")
                print(leader)
                election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))
                print("ELECTION MESSAGE:")
                print(election_message)


def collect_servers():
    servers.clear()
    servers.append(host_ip)
    collection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    collection_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    collection_socket.sendto(host_ip.encode('ascii'), (multicast_addr, test_port))
    collection_socket.settimeout(0.5)
    try:
        while True:
            receive_collect_message, address = collection_socket.recvfrom(1024)
            if address[0] not in servers and address[0] != host_ip:
                servers.append(address[0])
    except:
        print("Servercollection:")
        print(servers)


ask_server()
