import socket
import threading

hostname = socket.gethostname()
host = socket.gethostbyname(hostname)
#host = '127.0.0.1'
udpport = 5566

nickname = input("Wähle einen Benutzernamen")

def ask_host():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(f'991199,{host},{udpport}'.encode('ascii'), ('255.255.255.255', 5544))
    s.close()

def rec_host():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 5566))
    m = s.recv(1024).decode('ascii')
    s.close()
    new_values = m.split(",")
    global adresse
    adresse = str(new_values[0])
    global port
    port = int(new_values[1])

ask_host()
rec_host()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((adresse, port))


def recieve():
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



recieve_thread = threading.Thread(target=recieve)
recieve_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()