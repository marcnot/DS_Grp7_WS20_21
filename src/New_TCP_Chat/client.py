import socket
import threading
import struct
import time

#Set all importent variables
hostname = socket.gethostname()
host = socket.gethostbyname(hostname)

multicast_addr = '224.1.1.1'

multicast_server_client_port = 3000

tcp_IP = ""
tcp_PORT = ""
client = ""

############################## ASK HOST ##################################
# Dynamic discovery of the leadserver
# Getting the TCP IP and PORT for the TCP connection of the chatroom
##########################################################################
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

############################## RECEIVE FROM SERVER ##################################
# Receive function for the servermessages
# calling for reconnect after the TCP connection fails
# Waits for 10 seconds after the disconnect to give the servers time for an election and restart
#####################################################################################
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

############################## WRITE TO SERVER ##################################
# Handles the written messages and sends them to the server via TCP
#################################################################################
def write(client):
    while True:
        try:
            message = f'{nickname}: {input("")}'
            client.send(message.encode('ascii'))
        except:
            break

############################## SET THE CONNECTION TO THE SERVER ##################################
# Setup function for the connection
# asks via UDP for a leadserver and returns all importent informations
# Connects to the TCP chatroom
##################################################################################################
def set_connection():
    tcp_address, tcp_port = ask_host()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((tcp_address, tcp_port))
    return tcp_address, tcp_port, client

############################## CREATING IMPORTENT THREADS ##################################
# Creates all importent threads for the writing and reveiving function of the client
############################################################################################
def create_threads(client):
    write_thread = threading.Thread(target=write, args=(client,))
    write_thread.start()
    receive_thread = threading.Thread(target=receive, args=(client,))
    receive_thread.start()

############################## RECONNECTING AFTER LOST CONNECTION ##################################
# Reconnection function after disconnect
# asks for new TCP IP and PORT via the set_conneciton function and restarts the threads
####################################################################################################
def reconnect():
    tcp, port, client = set_connection()
    create_threads(client)
    return client

############################## START ##################################
tcp_IP, tcp_PORT, client = set_connection()
create_threads(client)