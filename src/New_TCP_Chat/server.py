import threading
import socket
import struct

hostname = socket.gethostname()
tcp_host = socket.gethostbyname(hostname)
tcp_port = 5555

multicast_addr = '224.0.0.1'
bind_addr = '0.0.0.0'

multicast_client_server_port = 3000
multicast_server_server_port = 4000


def send_address():
    while True:
        multicast_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        membership = socket.inet_aton(multicast_addr) + socket.inet_aton(bind_addr)
        multicast_listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        multicast_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_listener.bind((bind_addr, multicast_client_server_port))
        broadcast_message = multicast_listener.recv(1024).decode('ascii')
        new_values = broadcast_message.split(",")
        if new_values[0] == '991199':
            udp_client_address = str(new_values[1])
            udp_client_port = int(new_values[2])
            broadcast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_sender.sendto(f'{tcp_host},{tcp_port}'.encode('ascii'), (udp_client_address, udp_client_port))
            broadcast_sender.close()
        else:
            print("Wrong identifier")


thread = threading.Thread(target=send_address)
thread.start()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((tcp_host, tcp_port))

server.listen()

clients = []
nicknames = []


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

print("Server is listening...")
receive()