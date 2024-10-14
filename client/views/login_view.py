from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel

class LoginWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        # Сохраняем ссылку на контроллер
        self.controller = controller
        # Устанавливаем заголовок окна
        self.setWindowTitle("Login")
        # Инициализируем пользовательский интерфейс
        self.init_ui()

    def init_ui(self):
        # Создаем вертикальный макет для размещения виджетов
        layout = QVBoxLayout()
        # Поле ввода имени пользователя
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        # Поле ввода пароля
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Кнопка для входа
        login_button = QPushButton("Login", self)
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        # Метка для вывода сообщений
        self.message_label = QLabel(self)
        layout.addWidget(self.message_label)

        # Устанавливаем макет в окне
        self.setLayout(layout)

    def handle_login(self):
        # Получаем введенные имя пользователя и пароль
        username = self.username_input.text()
        password = self.password_input.text()
        # Вызываем метод контроллера для выполнения авторизации
        self.controller.login(username, password)
