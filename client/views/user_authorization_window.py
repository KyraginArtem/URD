#URD\client\views\user_authorization_window.py
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel

class LoginWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.username_input = None
        self.password_input = None
        self.message_label = None
        self.controller = controller # Ссылка на контроллер
        self.setWindowTitle("Login")
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("Login", self)
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        self.message_label = QLabel(self)
        layout.addWidget(self.message_label)
        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        self.controller.get_user_name_in_db(username, password)
