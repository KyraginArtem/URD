import socket
import threading
from server.controllers.server_controller import handle_client

# Функция для запуска сервера
def start_server():
    # Создаем TCP-сокет
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Привязываем сокет к адресу и порту
    server.bind(('0.0.0.0', 5000))
    # Начинаем прослушивание подключений (до 5 одновременно)
    server.listen(5)
    print("Сервер запущен и ожидает подключений...")

    while True:
        # Принимаем новое подключение
        client_socket, addr = server.accept()
        print(f"Подключение от {addr}")
        # Создаем новый поток для обработки клиента
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

# Запуск серверной части
if __name__ == "__main__":
    start_server()
