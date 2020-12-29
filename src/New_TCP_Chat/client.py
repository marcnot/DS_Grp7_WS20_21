import socket
import threading

hostname = socket.gethostname()
host = socket.gethostbyname(hostname)
udp_port = 5566

nickname = input("Wähle einen Benutzernamen: ")

def ask_host():
    broadcast_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_sender.sendto(f'991199,{host},{udp_port}'.encode('ascii'), ('255.255.255.255', 5544))
    broadcast_sender.close()


def rec_host():
    broadcast_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_listener.bind(('', 5566))
    message = broadcast_listener.recv(1024).decode('ascii')
    broadcast_listener.close()
    new_values = message.split(",")
    address = str(new_values[0])
    port = int(new_values[1])
    return port, address


ask_host()
tcp_port, tcp_address = rec_host()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((tcp_address, tcp_port))


def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
            else:
                print(message)
        except:
            print("An error occurred!")
            client.close()
            break

def write():
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('ascii'))



receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()