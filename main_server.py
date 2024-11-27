# URD/main_server.py
import socket
import threading
from server.controllers.server_controller import ServerController

def start_server():
    server_controller = ServerController()  # Создаем экземпляр контроллера
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5000))
    server.listen(5)
    print("Сервер запущен и ожидает подключений...")

    while True:
        client_socket, addr = server.accept()
        print(f"Подключение от {addr}")
        client_handler = threading.Thread(
            target=server_controller.handle_client,  # Используем метод экземпляра
            args=(client_socket,)
        )
        client_handler.start()

if __name__ == "__main__":
    start_server()
