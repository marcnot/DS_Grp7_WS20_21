import threading
import socket

hostname = socket.gethostname()
host = socket.gethostbyname(hostname)
#host = '127.0.0.1'
port = 5555

def send_adress():
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', 5544))
        m = s.recv(1024).decode('ascii')
        new_values = m.split(",")
        if new_values[0] == '991199':
            print(new_values)
            adress = str(new_values[1])
            porta = int(new_values[2])
            r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            r.sendto(f'{host},{port}'.encode('ascii'), (adress, porta))
            r.close()
        else:
            print("Wrong identifier")


thread = threading.Thread(target=send_adress)
thread.start()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))

server.listen()

clients = []
nicknames = []


def broadcast(message):
    for client in clients:
        client.send(message)


def handle(client):
    while True:
        try:
            message = client.recv(1024)
            broadcast(message)
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close
            nickname = nicknames[index]
            broadcast(f'{nickname} hat den chat verlassen'.encode('ascii'))
            nicknames.remove(nickname)
            break

def recieve():
    while True:
        client, address = server.accept()
        print(f"Verbunden mit {str(address)}")

        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')

        nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname of the CLient is {nickname}!')
        broadcast(f'Benutzer {nickname} hat den Chat betreten'.encode('ascii'))
        client.send('Verbunden mit dem Server'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Server is listening...")
recieve()