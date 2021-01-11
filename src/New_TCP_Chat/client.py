import socket
import threading
import struct
import time
import sys

#Set all importent variables
hostname = socket.gethostname()
host = socket.gethostbyname(hostname)

multicast_addr = '224.1.1.1'

multicast_server_client_port = 3000

tcp_IP = ""
tcp_PORT = ""
client = ""
vectorclock_ip = ""
vectorclock_port = ""

character_encoding = "utf-8"
buffersize = 1024

vectorclock = []
vectorclock_start = 0


############################## ASK HOST ##################################
# Dynamic discovery of the leadserver
# Getting the TCP IP and PORT for the TCP connection of the chatroom
##########################################################################
def ask_host():
    multicast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    multicast_sender.settimeout(2)
    multicast_sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    multicast_sender.sendto("2222".encode(character_encoding), (multicast_addr, multicast_server_client_port))
    try:
        receive_server_message, address = multicast_sender.recvfrom(buffersize)
        receive_server_message_splitted = receive_server_message.decode(character_encoding).split(",")
        address_tcp = int(receive_server_message_splitted[2])
        port = str(receive_server_message_splitted[1])
    except:
        print("Currently no servers available")
        sys.exit()
    return port, address_tcp


############################## RECEIVE FROM SERVER ##################################
# Receive function for the servermessages
# calling for reconnect after the TCP connection fails
# Waits for 10 seconds after the disconnect to give the servers time for an election and restart
#####################################################################################
def receive(client):
    while True:
        try:
            message = client.recv(buffersize).decode(character_encoding)
            if message == 'NICK':
                client.send(nickname.encode(character_encoding))
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
                try:
                    reconnect()
                    return timeout_counter == 10
                except:
                    print("No Service!")
            break

def vectorclock_receive(vectorclock_client):
    while True:
        try:
            vectorclock_send = vectorclock_client.recv(buffersize).decode(character_encoding)
            global vectorclock_start
            global vectorclock

            #print("VEC RECV: {}".format(vectorclock_send))

            if vectorclock_send[:7] == "VC_INIT":
                vectorclock_shorting = vectorclock_send[7:]
                vector_transform = eval(vectorclock_shorting)
                vectorclock_start = len(vector_transform)-1
                vectorclock = vector_transform
            else:
                vectorclock_recv = eval(vectorclock_send)
                get_VC_value = vectorclock[vectorclock_start]
                vectorclock_recv[vectorclock_start] = get_VC_value+1
                vectorclock = vectorclock_recv
                #print("VECTORCLOCK: {}".format(vectorclock))
        except:
            break

############################## WRITE TO SERVER ##################################
# Handles the written messages and sends them to the server via TCP
#################################################################################
def write(client, vectorclock_client):
    while True:
        try:
            message = f'{nickname}: {input("")}'
            client.send(message.encode(character_encoding))
            vectorclock_write(vectorclock_client)
        except:
            break

def vectorclock_write (vectorclock_client):
    global vectorclock
    vector_up = vectorclock[vectorclock_start]
    vectorclock[vectorclock_start] = vector_up+1
    vectorclock_send = str(vectorclock)
    #print("VECTORCLOCL CLIENT {}".format(vectorclock_client))
    #print("VECTORCLOCK WRITE {}".format(vectorclock_send))
    vectorclock_client.send(vectorclock_send.encode(character_encoding))

############################## SET THE CONNECTION TO THE SERVER ##################################
# Setup function for the connection
# asks via UDP for a leadserver and returns all importent informations
# Connects to the TCP chatroom
##################################################################################################
def set_connection():
    tcp_address, tcp_port = ask_host()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((tcp_address, tcp_port))
    vectorclock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    vectorclock_client.connect((tcp_address, tcp_port+1))
    return tcp_address, tcp_port, client, vectorclock_client, nickname

############################## CREATING IMPORTENT THREADS ##################################
# Creates all importent threads for the writing and reveiving function of the client
############################################################################################
def create_threads(client, vectorclock_client):
    write_thread = threading.Thread(target=write, args=(client, vectorclock_client,))
    write_thread.start()
    receive_thread = threading.Thread(target=receive, args=(client,))
    receive_thread.start()

    vectorclock_receive_thread = threading.Thread(target=vectorclock_receive, args=(vectorclock_client,))
    vectorclock_receive_thread.start()
    
    #vectorclock_write_thread = threading.Thread(target=vectorclock_write, args=(vectorclock_client,))
    #vectorclock_write_thread.start()

############################## RECONNECTING AFTER LOST CONNECTION ##################################
# Reconnection function after disconnect
# asks for new TCP IP and PORT via the set_conneciton function and restarts the threads
####################################################################################################
def reconnect():
    tcp, port, client, vectorclock_client, nickname = set_connection()
    create_threads(client, vectorclock_client)
    return client, vectorclock_client

############################## START ##################################
#nickname = input("Wähle einen Benutzernamen: ")
nickname = input("Wähle einen Benutzernamen: ")
tcp_IP, tcp_PORT, client, vectorclock_client, nickname = set_connection()
create_threads(client, vectorclock_client)
