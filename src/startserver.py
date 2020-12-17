import socket
import threading
import os
import sys
import time

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Server application IP address and port
server_address = '127.0.0.1'
server_port = 10001

# Buffer size
buffer_size = 1024

# Bind socket to port
server_socket.bind((server_address, server_port))
print('Server up and running at {}:{}'.format(server_address, server_port))

clients = []

def clientthread(conn, addr):
    conn.send("Welcome to this chatroom!")  
    while True:  
            try:  
                message = conn.recv(buffer_size)  
                if message:  
                    print ("<" + addr[0] + "> " + message)  
  
                    # Calls broadcast function to send message to all  
                    message_to_send = "<" + addr[0] + "> " + message  
                    broadcast(message_to_send, conn)  
  
                else:
                    remove(conn)  
  
            except:  
                continue

def broadcast(message, connection):  
    for clients in clients:  
        if clients!=connection:  
            try:  
                clients.send(message)  
            except:  
                clients.close()  
  
                # if the link is broken, we remove the client  
                remove(clients)  

def remove(connection):  
    if connection in clients:  
        clients.remove(connection)  

while True:

    # get the data sent to us
    #data, ip = server_socket.recvfrom(1024)
    conn, addr = server_socket.accept()

    clients.append(conn)

    print(addr[0] + "connected!")
    threading.Thread(clientthread(conn,addr))

    # display
    #print("{}: {}".format(ip, data.decode(encoding="utf-8").strip()))

    # echo back
    #server_socket.sendto(data, ip)

conn.close()
server_socket.close()