# client/controllers/client_controller.py
import socket
from PySide6.QtWidgets import QApplication
from client.views.login_view import LoginWindow
from client.views.template_constructor_view import TemplateConstructorWindow
from client.views.template_settings_window_view import TemplateSettingsWindow

class ClientController:
    def __init__(self):
        # Создаем экземпляр приложения Qt
        self.app = QApplication([])
        # Создаем окно авторизации и передаем контроллер
        self.view = LoginWindow(self)
        # Показываем окно авторизации
        self.view.show()
        # Запускаем основной цикл обработки событий приложения
        self.app.exec_()

        # Объявляем переменную для окна настроек, но не инициализируем его сразу
        self.settings_window = None

    def login(self, username, password):
        try:
            # Создаем TCP-сокет
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Подключаемся к серверу на localhost и порту 5000
                s.connect(('localhost', 5000))
                # Формируем данные для авторизации
                login_data = f"LOGIN {username} {password}"
                # Отправляем данные на сервер
                s.sendall(login_data.encode())
                # Получаем ответ от сервера
                response = s.recv(1024).decode()
                # Проверяем ответ сервера и выводим результат
                if response == 'Login successful':
                    print('Login successful')
                    # Проверяем роль пользователя (например, если это администратор)
                    if username == 'admin':
                        # Закрываем окно авторизации и открываем конструктор шаблонов
                        self.view.close()
                        self.open_template_constructor(username)
                else:
                    print('Invalid credentials')
        except ConnectionRefusedError as e:
            # Обработка ошибки, если сервер недоступен
            print(f"Error connecting to server: {e}")

    def get_template_names(self):
        # В данном методе должно быть подключение к базе данных для получения списка шаблонов
        try:
            # Создаем TCP-сокет
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Подключаемся к серверу на localhost и порту 5000
                s.connect(('localhost', 5000))
                # Отправляем запрос на получение списка шаблонов
                s.sendall("GET_TEMPLATE_NAMES".encode())
                # Получаем ответ от сервера
                response = s.recv(4096).decode()
                # Предполагается, что ответ сервера - это строка с названиями шаблонов, разделенная запятыми
                template_names = response.split(',')
                return template_names
        except ConnectionRefusedError as e:
            print(f"Error connecting to server: {e}")
            return []

    def open_template_constructor(self, username):
        template_names = self.get_template_names()  # Получение списка шаблонов из БД
        self.template_constructor_view = TemplateConstructorWindow(admin_name=username, template_names=template_names)
        self.template_constructor_view.settings_requested.connect(self.open_settings_window)  # Подключаем сигнал к методу контроллера
        self.template_constructor_view.show()

    def open_settings_window(self):
        # Окно настроек для изменения количества ячеек в таблице
        self.settings_window = TemplateSettingsWindow()
        # Подключаем сигнал, чтобы применить настройки к таблице
        self.settings_window.settings_applied.connect(self.apply_settings_to_table)
        self.settings_window.show()

    def apply_settings_to_table(self, rows, cols):
        # Применение настроек таблицы в окне конструктора шаблонов
        if hasattr(self, 'template_constructor_view'):
            self.template_constructor_view.table.setRowCount(rows)
            self.template_constructor_view.table.setColumnCount(cols)

            # Генерация заголовков столбцов
            column_labels = [self.generate_column_labels(i + 1) for i in range(cols)]

            self.template_constructor_view.table.setHorizontalHeaderLabels(column_labels)
            self.template_constructor_view.table.setVerticalHeaderLabels([str(i + 1) for i in range(rows)])

    def generate_column_labels(self, num_columns):
        """Генерирует заголовки столбцов аналогично Excel (A, B, ..., Z, AA, AB, ..., AZ, BA и т.д.)"""
        labels = []
        while num_columns > 0:
            num_columns -= 1
            labels.append(chr(65 + (num_columns % 26)))
            num_columns //= 26
        return ''.join(reversed(labels))
