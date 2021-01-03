import threading
import socket
import struct


hostname = socket.gethostname()
host_ip = socket.gethostbyname(hostname)
tcp_port = 5555

multicast_addr = '224.1.1.1'

bind_addr = '0.0.0.0'

multicast_client_server_port = 3000
multicast_server_server_port = 4000

server_heartbeat_port = 4001
server_server_list_port = 4002
server_client_list_port = 4003
server_leader_election_port = 4004

client_server_address = (host_ip, multicast_client_server_port)
server_server_address = (host_ip, multicast_server_server_port)
heartbeat_address = (host_ip, server_heartbeat_port)

lead_server = True

clients = []
servers = []
nicknames = []


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
heartbeat_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
backupserver_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

membership = socket.inet_aton(multicast_addr) + socket.inet_aton(bind_addr)

def get_neighbour(ring, current_node_ip, direction):
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
            append_server(address)
            print("SERVERLISTE:")
            print(servers)
            #ring = server_ring(servers)
            neighbour = get_neighbour(servers, server_server_address, 'left')
            print(neighbour)
            multicast_server_listener.close()
        else:
            print("Wrong server identifier")


def append_server(server_ip):
    servers.append(server_ip)


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
    lead_server = True
    append_server(server_server_address)
    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
 
    heartbeat_tcp.bind((host_ip, server_heartbeat_port))
    heartbeat_tcp.listen()
    server.bind((host_ip, tcp_port))
    server.listen()

    print("Server is listening...")
    heartbeat()
    receive()


def ask_server():
    multicast_server_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_server_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_server_sender.sendto("1111".encode('ascii'), (multicast_addr, multicast_server_server_port))
    multicast_server_sender.settimeout(2.5)
    try:
        receive_server_message, address = multicast_server_sender.recvfrom(1024)
        print(receive_server_message)
        print("recv.Server")
        start_backup_server()
    except:
        print("Start Server")
        start_server()


def start_backup_server():
    print("Start Backup Server")
    backupserver_tcp.connect(heartbeat_address)

    backup_heartbeat_recv_thread = threading.Thread(target=backup_heartbeat_recv)
    backup_heartbeat_recv_thread.start()


def backup_heartbeat_recv():
    while True:
        try:
            message = backupserver_tcp.recv(1024)
            time.sleep(2)
            backupserver_tcp.send("hallo lebe :)")
        except:
            print("Connection lost to Server!")
            backupserver_tcp.close()
            break


def heartbeat():
    print("heartbeat")
    while True:
        heartbeat_server, address = heartbeat_tcp.accept()
        heartbeat_server.send('BEAT'.encode('ascii'))
        heartbeat_msg = heartbeat_tcp.recv(1024)

        heartbeat_server_thread = threading.Thread(target=handle_heartbeat, args=(heartbeat_server,))
        heartbeat_server_thread.start()


def handle_heartbeat(heartbeat_server):
    print("handle_heartbeat")
    while True:
        try:
            message = heartbeat_tcp.recv(1024)
            print(message)
        except:
            pass


def check_server():
    ask_server()


check_server()

