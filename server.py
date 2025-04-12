from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from database import Database
import json

# Настройки
HOST = "0.0.0.0"
PORT = 8001
VERSION = "0.0.1"

# Инициализация FastAPI и базы данных
app = FastAPI()
db = Database()

# Класс игрока (без изменений)
class Player:
    def __init__(self, player_name, password):
        self.player_name = player_name
        self.id = None  # Уникальный идентификатор игрока
        self.password = password

    def __str__(self):
        return f"Player(id={self.id}, name={self.player_name}, password={self.password})"

# Хранилище игроков
players = {}

# Модель для валидации данных игрока (для REST API)
class PlayerData(BaseModel):
    player_name: str
    password: str

# REST API: Проверка версии сервера
@app.get("/version")
async def get_version():
    return {"version": VERSION}

# REST API: Регистрация игрока
@app.post("/register")
async def register_player(data: PlayerData):
    try:
        player = Player(data.player_name, data.password)
        player.id = len(players) + 1
        players[player.id] = player

        await db.init_db()
        user = await db.add_user(player.player_name, player.password, player.id)

        if user == "user added":
            print(f"Player {player} created.")
            return {"status": "success", "user_data": {"id": player.id, "player_name": player.player_name}}
        elif user == "user exists":
            print(f"exists {player}")
            #raise HTTPException(status_code=400, detail={"status": "exists", "player_name": player.player_name})
        else:
            raise HTTPException(status_code=500, detail="Unexpected database response")
    except Exception as e:
        print(f"Error registering player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket: Для обработки сообщений в реальном времени
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")

            if data == "Hello":
                response = {"type": "version", "data": VERSION}
                await websocket.send_json(response)
            elif data.startswith("register|"):
                parts = data.split("|")
                if len(parts) != 3:
                    await websocket.send_json({"type": "error", "data": "Invalid request"})
                    continue

                player_name, player_password = parts[1], parts[2]
                player = Player(player_name, player_password)
                player.id = len(players) + 1
                players[player.id] = player

                await db.init_db()
                user = await db.add_user(player.player_name, player.password, player.id)

                if user == "user added":
                    print(f"Player {player} created.")
                    response = {"type": "user_data", "id": player.id, "player_name": player.player_name}
                    await websocket.send_json(response)
                elif user == "user exists":
                    print(f"exists {player}")
                    response = {"type": "exists", "player_name": player.player_name}
                    await websocket.send_json(response)
                else:
                    await websocket.send_json({"type": "error", "data": "Unexpected database response"})
            else:
                await websocket.send_json({"type": "error", "data": "Invalid request"})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level=None)