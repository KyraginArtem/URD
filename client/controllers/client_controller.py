# client/controllers/client_controller.py
import socket
from PySide6.QtWidgets import QApplication, QMessageBox
from client.views.login_view import LoginWindow
from client.views.template_constructor_view import TemplateConstructorWindow
from client.views.template_settings_window_view import TemplateSettingsWindow

class ClientController:
    # Объявляем переменную для окна настроек, но не инициализируем его сразу
    settings_window = None

    def __init__(self):
        self.app = QApplication([])
        self.controller = self
        self.view = LoginWindow(self)
        self.view.show()
        self.app.exec_()
        self.template_constructor_view = None

    def open_template_constructor(self, username):
        template_names = self.get_template_names()  # Получение списка шаблонов из БД
        print(f"Шаблоны для конструктора: {template_names}")  # Отладка
        self.template_constructor_view = (
            TemplateConstructorWindow(admin_name=username, template_names=template_names, parent_view=self))
        self.template_constructor_view.template_selected.connect(self.request_template_data)
        self.template_constructor_view.settings_requested.connect(self.open_settings_window)
        self.template_constructor_view.template_saved.connect(
            self.save_template)  # Подключаем сохранение к методу контроллера
        self.template_constructor_view.show()

    def open_settings_window(self):
        # Окно настроек для изменения количества ячеек в таблице
        if not hasattr(self, 'template_constructor_view') or self.template_constructor_view is None:
            print("Ошибка: Конструктор шаблонов еще не инициализирован.")
            return
        if not self.settings_window:
            # Создаем окно настроек и подключаем сигналы
            self.settings_window = TemplateSettingsWindow(self.template_constructor_view)
            self.settings_window.settings_applied.connect(self.template_constructor_view.apply_settings_to_table)
        self.settings_window.show()

    def send_request_to_server(self, request_data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 5000))
                s.sendall(request_data.encode('utf-8'))
                response = s.recv(4096).decode('utf-8')
                return response
        except ConnectionRefusedError as e:
            print(f"Error connecting to server: {e}")
            return None

    def login(self, username, password):
        login_data = f"LOGIN {username} {password}"
        response = self.send_request_to_server(login_data)

        if response:
            if response.startswith('Login successful'):
                print('Login successful')
                _, role, admin_name = response.split('|')
                if role == 'admin':
                    self.view.close()
                    self.open_template_constructor(admin_name)
                else:
                    print('Access denied: User is not an admin')
            else:
                print('Invalid credentials')

    def get_template_names(self):
        request = "GET_TEMPLATE_NAMES"
        response = self.send_request_to_server(request)
        if response:
            template_names = response.split(',')
            return template_names
        else:
            return []

    def request_template_data(self, template_name):
        request = f"GET_TEMPLATE_DATA {template_name}"
        response = self.send_request_to_server(request)
        if response:
            self.update_template(response)

    def update_template(self, template_data):
        try:
            # Парсим данные шаблона
            parts = template_data.split("|")
            if len(parts) < 4:
                raise ValueError("Invalid data format received from server.")

            row_count = int(parts[0].strip())
            col_count = int(parts[1].strip())
            background_color = parts[2].strip()
            cell_data = parts[3]
            cell_data_line = cell_data.splitlines()
            print(f"Данные из ячейки: {cell_data_line}")

            # Обновляем данные таблицы и фон в представлении
            if hasattr(self, 'template_constructor_view'):
                self.template_constructor_view.update_table_structure(row_count, col_count)
                self.template_constructor_view.update_background_color(background_color)
                self.template_constructor_view.update_table_data(cell_data_line)
        except ValueError as e:
            print(f"Error parsing template data: {e}")

    def save_template(self, template_name, row_count, col_count, cell_data):
        # Сначала проверяем, существует ли уже шаблон с таким именем
        if self.check_template_exists(template_name):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Ошибка")
            msg_box.setText(f"Шаблон с именем '{template_name}' уже существует.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
        else:
            request = f"SAVE_TEMPLATE|{template_name}|{row_count}|{col_count}|{cell_data}"
            response = self.send_request_to_server(request)
            if "Template saved successfully" in response:
                self.update_template_combo_box(template_name)
                self.template_constructor_view.set_current_template_in_combo(template_name)
            else:
                print("Не удалось сохранить шаблон.")

    def check_template_exists(self, template_name):
        request = f"CHECK_TEMPLATE_EXISTS {template_name}"
        response = self.send_request_to_server(request)
        if "Template exists" in response:
            return True
        else:
            return False

    def update_template_combo_box(self, new_template_name):
        if hasattr(self, 'template_constructor_view') and self.template_constructor_view:
            self.template_constructor_view.add_template_name_to_combo(new_template_name)
        else:
            print("Ошибка: объект template_constructor_view не инициализирован.")

    def delete_template(self, template_name):
        request = f"DELETE_TEMPLATE|{template_name}"
        response = self.send_request_to_server(request)
        if "Delete successful" in response:
            QMessageBox.information(self.template_constructor_view, "Удаление шаблона",
                                    f"Шаблон '{template_name}' успешно удален.")
            self.template_constructor_view.remove_template_name_from_combo(template_name)
        else:
            QMessageBox.warning(self.template_constructor_view, "Ошибка удаления", "Не удалось удалить шаблон.")