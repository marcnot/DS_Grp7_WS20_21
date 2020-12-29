import threading
import socket

hostname = socket.gethostname()
tcp_host = socket.gethostbyname(hostname)
tcp_port = 5555

def send_adress():
    while True:
        broadcast_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_listener.bind(('', 5544))
        broadcast_message = broadcast_listener.recv(1024).decode('ascii')
        new_values = broadcast_message.split(",")
        if new_values[0] == '991199':
            udp_address = str(new_values[1])
            udp_port = int(new_values[2])
            broadcast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_sender.sendto(f'{tcp_host},{tcp_port}'.encode('ascii'), (udp_address, udp_port))
            broadcast_sender.close()
        else:
            print("Wrong identifier")


thread = threading.Thread(target=send_adress)
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

def recieve():
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
recieve()