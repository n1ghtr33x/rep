import asyncio
import socket
from database import Database

HOST = '138.2.134.211'
PORT = 8001

version = "0.0.1"

db = Database()

# Класс игрока
class Player:
    def __init__(self, player_name, password):
        self.player_name = player_name
        self.id = None  # Уникальный идентификатор игрока
        self.password = password

    def __str__(self):
        return f"Player(id={self.id}, name={self.player_name}, password={self.password})"


# Список для хранения игроков
players = {}

async def handle_client(client_socket):
    try:
        # Принимаем запрос от клиента
        message = client_socket.recv(1024).decode()
        print(f"Received message: {message}")

        if message == "Hello":
            response = f"version|{version}"
            client_socket.send(response.encode())

        if message.startswith("register|"):
            player_name = message.split("|")[1]
            player_password = message.split("|")[2]

            player = Player(player_name, player_password)
            player.id = len(players) + 1
            players[player.id] = player
            await db.init_db()
            user = await db.add_user(player.player_name, player.password, player.id)
            if user == "user added":
                print(f"Player {player} created.")
                print(player)
                response = f"user_data|{player.id}|{player.player_name}"
                client_socket.send(response.encode())
            elif user == "user exists":
                print(f"exists {player}")
                response = f"exists|{player.player_name}"
                client_socket.send(response.encode())
        else:
            # Для других сообщений
            client_socket.send("Invalid request".encode())

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()


async def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established.")
        await handle_client(client_socket)
        #client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        #client_handler.start()


if __name__ == "__main__":
    asyncio.run(start_server())
