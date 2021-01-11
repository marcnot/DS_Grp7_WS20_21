import threading
import socket
import struct
import time
import json
import ipaddress


# Setting Lists for the Server
clients = []
servers = []
nicknames = []
vectorclock = []
vectorclock_clients = []

character_encoding = "utf-8"

#Get Hostname and HostIP
hostname = socket.gethostname()
host_ip = socket.gethostbyname(hostname)

multicast_addr = '224.1.1.1'

#Portconfiguration
multicast_client_server_port = 3000
multicast_server_server_port = 4000
election_port = 4050
backup_port = 10001
collect_port = 10002
heartbeat_port = 4060
tcp_port = 5555
tcp_server_port = 5588
vectorclock_port = 5556

buffersize = 1024

#Every Server is not a Leader from the Start. The first Server will be set as True and the Backups as False.
#This will change after the Leaderelection and the new start of servers
leader = False

client_server_address = (host_ip, multicast_client_server_port)
server_server_address = (host_ip, multicast_server_server_port)

#Socket definition
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
vectorclock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
heartbeat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
heartbeat_socket.settimeout(2.5)

#Socketbinds
election_socket.bind((host_ip, election_port))
heartbeat_socket.bind((host_ip, heartbeat_port))

#Election 
election_message = {
    "mid": host_ip,
    "isLeader": leader}
participant = False


############################## RING FORMING ##################################
#The serverlist will be formated by sorting the IPs of the servers           
##############################################################################
def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

############################## GET NEIGHBOUR #################################
# Get the left or right neighbour in the serverlist.                         
##############################################################################
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

########################## LEADER ELECTION ###################################
leader_uid = ""

def leader_election(server_host_ip, leader_uid):

    #Set the variables as global the change variables outside the function
    global leader
    global participant

    #receive an election message from his left neighbour
    election_message, address = election_socket.recvfrom(buffersize)
    election_message = json.loads(election_message.decode())

    #Update of the Groupview
    servers.clear()
    collect_servers()
    neighbour = get_neighbour(form_ring(servers), host_ip, 'right')
 
    #convert the IPs to compare them 
    election_IP = ipaddress.IPv4Address(election_message["mid"])
    election_host_IP = ipaddress.IPv4Address(server_host_ip)

    if election_message['isLeader']:
        leader_uid = election_message["mid"]
        # forward received election message to left neighbour
        participant = False
        heartbeat_send()
        election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))

    if election_IP < election_host_IP and not participant:
        new_election_message = {
            "mid": str(election_host_IP),
            "isLeader": False}
        participant = True
        # send received election message to left neighbour
        election_socket.sendto(json.dumps(new_election_message).encode(), (neighbour, election_port))
    elif election_IP > election_host_IP:
        # send received election message to left neighbour
        participant = False
        election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))
    elif election_IP == election_host_IP and not leader:
        leader_uid = str(election_host_IP)
        new_election_message = {
            "mid": str(election_host_IP),
            "isLeader": True}
        election_message["isLeader"] = True
        # send new election message to left neighbour
        participant = False
        leader = True
        restart()
        heartbeat_send()
        print("New Main Server is starting on {}".format(host_ip))
        election_socket.sendto(json.dumps(new_election_message).encode(), (neighbour, election_port))
    

############################## SEND CLIENTS ########################################################################
# Create a socket for new Clients, to identify them and give them the TCP Port
# Sends TCP Port and the TCP IP of the Server to the Clients
# If the first message of the client does not include "2222" the server does respond with "Wrong client identifier"
#
# This function is running in a thread to continuously listen for new clients
#
####################################################################################################################
def send_clients():
    while True:
        multicast_client_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        multicast_client_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        multicast_client_listener.bind(client_server_address)
        client_message, address = multicast_client_listener.recvfrom(buffersize)
        new_values = client_message.decode(character_encoding).split(",")
        if new_values[0] == '2222':
            multicast_client_listener.sendto(f'1112,{host_ip},{tcp_port}'.encode(character_encoding), address)
            multicast_client_listener.close()
        else:
            print("Wrong client identifier")

############################## SEND SERVER #################################
# Dynamic discovery for the new joint server in the network
# After a second server jont the network, heartbeat will start
# The new server will be appended to the actual serverlist
#
# This function is running in a thread to continuously listen for new servers
#
############################################################################
def send_server():
    while True:
        multicast_server_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        multicast_server_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        multicast_server_listener.bind(server_server_address)
        server_message, address = multicast_server_listener.recvfrom(buffersize)
        multicast_server_listener.sendto(host_ip.encode(character_encoding), address)

        if address[0] not in servers:
            servers.append(address[0])
            if len(servers) == 2:
                heartbeat_send()

        print("List of Servers: {}".format(servers))
        #time.sleep(2)
        multicast_server_listener.close()

############################## SERVER COLLECTION #################################
# Function is running in a thread to answer groupview update requests
# 
##################################################################################
def server_collector():
    while True:
        server_collector_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        server_collector_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        server_collector_listener.bind((host_ip, collect_port))
        collect_message, address = server_collector_listener.recvfrom(buffersize)
        server_collector_listener.sendto(host_ip.encode(character_encoding), address)
        server_collector_listener.close()

############################## MULTICAST #################################
# Sends the received messages to all clients through the clientslist 
# not actutally multicast, but it works ;)
# Messages will be send with TCP and not UDP
# Reliable Messagetransmission
##########################################################################
def multicast(message):
    for client in clients:
        #print("MESSAGE TO: {}, MESSAGE: {}".format(client, message))
        client.send(message)

def vector_cast(vectorclock_send):
    vectorclock_send[0] = vectorclock_send[0]+1
    vectorclock_send = str(vectorclock_send)
    print("Vectorclock send to Clients: {}".format(vectorclock_send))
    for vectorclock_client in vectorclock_clients:
        vectorclock_client.send(vectorclock_send.encode(character_encoding))

############################## CLIENT HANDLING #################################
# Listening to Clientmessages and updates the clientlist if a client leaves
# Every Client has his own thread for handling the messages
# Calls the function to send messages to other clients
################################################################################
def handle(client):
    while True:
        try:
            message = client.recv(buffersize)
            multicast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close
            nickname = nicknames[index]
            multicast(f'{nickname} has left the chat'.encode(character_encoding))
            nicknames.remove(nickname)
            break

def vectorclock_handle(vectorclock_client):
    while True:
        try:
            vectorclock_rec = vectorclock_client.recv(buffersize)
            global vectorclock
            print("Vectorclock received from Client: {}".format(vectorclock_rec))
            vectorclock_rec = eval(vectorclock_rec)
            vector_client_index = vectorclock_clients.index(vectorclock_client)
            vectorclock_rec[0] = vectorclock[0]+1
            vectorclock = vectorclock_rec
            #print("VC REC VECTORCLOCK HANDLE {}".format(vectorclock_rec))
            #print("VECTORCLOCK AKTUELL: {}".format(vectorclock))
            vector_cast(vectorclock)
        except:

             #### At this point we dont remove any clients from the vectorclock or the vectorclock_clients list 
            #### We know that the List will get longer with every new client that connects with the server
             #### For improvments in the future we should figure out how to remove the clients from the vectorclock
            #### The problem is that the client doenst get a new index for his listindex (on the clientside)
             #### by deleting a client in the middle of the list.

            #index = vectorclock_clients.index(vectorclock_client)
            #vectorclock_clients.remove(vectorclock_client)
            #vectorclock_client.close()
            #vectorclock_place = index+1
            #del vectorclock[vectorclock_place]
            #vector_cast(vectorclock)
            break

############################## RECEIVE MESSAGES FROM CLIENTS #################################
# Listening to new TCP CLient Connections and accepting them.
# Set given Nicknames and append IPs and Nicknames to two seperated lists
# Starting a Thread for every client who connects to the server with an own handlemethod and pass the client object to that thread
# Casts a message to the other Clients for new Member in the Chatroom
##############################################################################################
def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send('NICK'.encode(character_encoding))
        nickname = client.recv(buffersize).decode(character_encoding)

        nicknames.append(nickname)
        clients.append(client)

        print(f'Username of the Client is {nickname}!')
        multicast(f'{nickname} has joined the chat'.encode(character_encoding))
        client.send('Connected to the server'.encode(character_encoding))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

def vector_receive():
    while True:
        global vectorclock
        vectorclock_client, address = vectorclock_socket.accept()
        #print("Vectorclock angefragt von {}".format(str(address)))
        #print("VECTORCLOCK_CLIENT: {}".format(vectorclock_client))
        vectorclock.append(0)
        vectorclock_clients.append(vectorclock_client)
        #print("VECTORCLOCK SERVER RECV: {}".format(vectorclock))
        vector_init = "VC_INIT"+str(vectorclock)
        vectorclock_client.send(vector_init.encode(character_encoding))
        #print("VECTORCLOCK UPDATE: {}".format(vectorclock))
        vectorclock_thread = threading.Thread(target=vectorclock_handle, args=(vectorclock_client,))
        vectorclock_thread.start()
        vector_cast(vectorclock)

############################## BACKUP SERVER HANDLING #################################
# Handling the Backup Server and listening to new Server in the network 
#######################################################################################
def handle_backups():
    while True:
        handle_backup_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        group = socket.inet_aton(multicast_addr)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        handle_backup_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        handle_backup_socket.bind((host_ip, backup_port))
        server_message, address = handle_backup_socket.recvfrom(buffersize)

############################## STARTING MAINSERVER #################################
# Only the first server will start this function to start all the importent threads and sockets
# Binds different UDP and TCP Sockets for the Serverenviroment
####################################################################################
def start_server():
    leader = True

    global vectorclock
    vectorclock = [0]

    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
    collector_thread = threading.Thread(target=server_collector)
    collector_thread.start()

    server.bind((host_ip, tcp_port))
    server.listen()
    vectorclock_socket.bind((host_ip, vectorclock_port))
    vectorclock_socket.listen()
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()
    vector_receive_thread = threading.Thread(target=vector_receive)
    vector_receive_thread.start()
    #print("Ready for Servers")
    receive_backup_thread = threading.Thread(target=handle_backups)
    receive_backup_thread.start()
    server_heartbeat_thread = threading.Thread(target=heartbeat_recv)
    server_heartbeat_thread.start()
    election_thread = threading.Thread(target=leader_election, args=(host_ip, leader_uid,))
    election_thread.start()
    #print("DONE")
    print("Server is listening...")
############################## RESTARTING AFTER LEADER ELECTION #################################
# function will be called after a server is the new leader to replace the importent sockets for the client/server connection
# and handling all other Sockets for the Serverringformation
#################################################################################################
def restart():
    leader = True
    global vectorclock
    vectorclock = [0]
    client_thread = threading.Thread(target=send_clients)
    client_thread.start()
    server.bind((host_ip, tcp_port))
    server.listen()
    vectorclock_socket.bind((host_ip, vectorclock_port))
    vectorclock_socket.listen()
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()
    vector_receive_thread = threading.Thread(target=vector_receive)
    vector_receive_thread.start()
    #print("Ready for Servers")
    receive_backup_thread = threading.Thread(target=handle_backups)
    receive_backup_thread.start()
    print("Server is listening...")
    return leader


############################## ASK FOR SERVER IN NETWORK #################################
# Asks via UDP for existing servers on the multicastport in the network
# if a server exists it will start as a backup server and the lead variable is set to False
# if there is no response from other server, the server will start as the first one
##########################################################################################
def ask_server():
    servers.append(host_ip)
    multicast_server_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_server_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_server_sender.sendto(host_ip.encode(character_encoding), (multicast_addr, multicast_server_server_port))
    multicast_server_sender.settimeout(0.5)
    try:
        receive_server_message, address = multicast_server_sender.recvfrom(buffersize)
        print("Start Backup Server at {}".format(host_ip))
        leader = False
        start_backup_server()
    except:
        print("Start Main Server at {}".format(host_ip))
        leader = True
        start_server()

    return leader
        

############################## STARTING START BACKUP SERVER #################################
# All importent sockets and threads for the backupserver system will be startet
# 
#############################################################################################
def start_backup_server():
    collect_servers()
    server_collector_thread = threading.Thread(target=server_collector)
    server_collector_thread.start()
    server_thread = threading.Thread(target=send_server)
    server_thread.start()
    server_heartbeat_thread = threading.Thread(target=heartbeat_recv)
    server_heartbeat_thread.start()
    election_thread = threading.Thread(target=leader_election, args=(host_ip, leader_uid,))
    election_thread.start()


############################## HEARTBEAT #############################################
# Heartbeat Function to discover if the neighbour is still alive
# if there is not heartbeat the server with no response will start the leader election (LE)
######################################################################################

# Every second a server will send a "heartbeat" to his right neighbour
def heartbeat_send():
    time.sleep(1.0)
    neighbour = get_neighbour(form_ring(servers), host_ip, 'right')
    heartbeat_socket.sendto(str(host_ip).encode(), (neighbour, heartbeat_port))
    print("HEARTBEAT SEND HOST IP: {}, NEIGHBOUR: {}, LEADER {}".format(host_ip, neighbour, leader))


# Receive function for the heartbeat
# if there is no heartbeat in 5 seconds the leader election will be startet
# the socket throws a timeout and starts the LE
def heartbeat_recv():

    while True:
        if len(servers) > 1:
            try:
                beat, address = heartbeat_socket.recvfrom(buffersize)
                heartbeat_send()
            except:

                election_message = {
                "mid": host_ip,
                "isLeader": leader}
                participant = False

                collect_servers()
                neighbour = get_neighbour(form_ring(servers), host_ip, 'right')
                election_socket.sendto(json.dumps(election_message).encode(), (neighbour, election_port))


############################## COLLECT SERVER IN NETWORK #################################
# Collects all server in the network and appends them to the list "servers"
##########################################################################################
def collect_servers():
    servers.clear()
    servers.append(host_ip)
    collection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    collection_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    collection_socket.sendto(host_ip.encode(character_encoding), (multicast_addr, collect_port))
    collection_socket.settimeout(0.5)
    try:
        while True:
            receive_collect_message, address = collection_socket.recvfrom(buffersize)
            if address[0] not in servers and address[0] != host_ip:
                servers.append(address[0])
    except:
        print("List of Servers: {}".format(servers))

############################## START #################################
leader = ask_server()