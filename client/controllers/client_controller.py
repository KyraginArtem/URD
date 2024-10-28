# client/controllers/client_controller.py
import socket
from PySide6.QtWidgets import QApplication, QMessageBox
from client.views.login_view import LoginWindow
from client.views.template_constructor_view import TemplateConstructorWindow
from client.views.template_settings_window_view import TemplateSettingsWindow

class ClientController:
    settings_window = None

    def __init__(self):
        self.app = QApplication([])
        self.controller = self
        self.login_pass_view = LoginWindow(self)
        self.login_pass_view.show()
        self.app.exec_()
        self.template_constructor_view = None

    @staticmethod
    def show_message_box(self, title, message, icon=QMessageBox.Information, button=QMessageBox.Ok):
        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(button)
        msg_box.exec()

    @staticmethod
    def send_request_to_server(request_data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 5000))
                s.sendall(request_data.encode('utf-8'))
                response = s.recv(4096).decode('utf-8')
                return response
        except ConnectionRefusedError as e:
            print(f"Error connecting to server: {e}")
            return None

    def open_template_constructor_window(self, username):
        template_names = self.get_template_names_in_db()  # Получение списка шаблонов из БД
        print(f"Шаблоны для конструктора: {template_names}")  # Отладка
        self.template_constructor_view = (TemplateConstructorWindow(admin_name=username, template_names=template_names, parent_view=self))
        self.template_constructor_view.template_selected.connect(self.request_template_data_in_db)
        self.template_constructor_view.settings_requested.connect(self.open_settings_window)
        self.template_constructor_view.template_saved.connect(
            self.save_template_in_db)  # Подключаем сохранение к методу контроллера
        self.template_constructor_view.template_update.connect(self.update_template_data_in_db)
        self.template_constructor_view.delete_template_signal.connect(self.delete_template_in_db)
        self.template_constructor_view.show()

    def open_settings_window(self):
        if not hasattr(self, 'template_constructor_view') or self.template_constructor_view is None:
            print("Ошибка: Конструктор шаблонов еще не инициализирован.")
            return
        if not self.settings_window:
            # Создаем окно настроек и подключаем сигналы
            self.settings_window = TemplateSettingsWindow(self.template_constructor_view)
            self.settings_window.settings_applied.connect(self.template_constructor_view.apply_settings_to_table)
        self.settings_window.show()

    def refresh_template_in_window(self, template_data):
        try:
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

    def refresh_template_combo_box_in_window(self, new_template_name):
        if hasattr(self, 'template_constructor_view') and self.template_constructor_view:
            self.template_constructor_view.add_template_name_to_combo(new_template_name)
        else:
            print("Ошибка: объект template_constructor_view не инициализирован.")

    def check_template_exists_in_db(self, template_name):
        response = ClientController.send_request_to_server(f"CHECK_TEMPLATE_EXISTS {template_name}")
        if "Template exists" in response:
            return True
        else:
            return False

    def get_template_names_in_db(self):
        response = ClientController.send_request_to_server("GET_TEMPLATE_NAMES")
        if response:
            template_names = response.split(',')
            return template_names
        else:
            return []

    def get_user_name_in_db(self, username, password):
        login_data = f"LOGIN {username} {password}"
        response = ClientController.send_request_to_server(login_data)
        if response:
            if response.startswith('Login successful'):
                print('Login successful')
                _, role, admin_name = response.split('|')
                if role == 'admin':
                    self.login_pass_view.close()
                    self.open_template_constructor_window(admin_name)
                else:
                    print('Access denied: User is not an admin')
            else:
                print('Invalid credentials')

    def request_template_data_in_db(self, template_name):
        response = ClientController.send_request_to_server(f"GET_TEMPLATE_DATA {template_name}")
        if response:
            self.refresh_template_in_window(response)

    def update_template_data_in_db(self, template_name, row_count, col_count, cell_data):
        request = f"UPDATE_TEMPLATE|{template_name}|{row_count}|{col_count}|{cell_data}"
        response = ClientController.send_request_to_server(request)
        if "Template update successfully" in response:
            (ClientController.show_message_box
            (self, "Обновление шаблона", f"Шаблон '{template_name}' успешно обнавлен."))
        else:
            print("Не удалось сохранить шаблон.")

    def save_template_in_db(self, template_name, row_count, col_count, cell_data):
        # Сначала проверяем, существует ли уже шаблон с таким именем
        if self.check_template_exists_in_db(template_name):
            ClientController.show_message_box(self,
                "Ошибка", "Шаблон с именем '{template_name}' уже существует.", QMessageBox.Warning)
            return
        else:
            request = f"SAVE_TEMPLATE|{template_name}|{row_count}|{col_count}|{cell_data}"
            response = ClientController.send_request_to_server(request)
            if "Template saved successfully" in response:
                self.refresh_template_combo_box_in_window(template_name)
                self.template_constructor_view.set_current_template_in_combo(template_name)
            else:
                print("Не удалось сохранить шаблон.")

    def delete_template_in_db(self, template_name):
        if self.check_template_exists_in_db(template_name):
            response = ClientController.send_request_to_server(f"DELETE_TEMPLATE|{template_name}")
            if "Delete successful" in response:
                self.template_constructor_view.remove_template_name_from_combo(template_name)
                (ClientController.
                 show_message_box(self,"Удаление шаблона", f"Шаблон '{template_name}' успешно удален."))
            else:
                (ClientController.
                 show_message_box(self,"Ошибка удаления", "Не удалось удалить шаблон.", QMessageBox.Warning))