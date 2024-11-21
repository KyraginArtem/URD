# client/controllers/client_controller.py
import json
import socket
import zlib

from PySide6.QtWidgets import QApplication, QMessageBox
from client.views.user_authorization_window import LoginWindow
from client.views.template_constructor_window import TemplateConstructorWindow
from client.views.window_creating_new_template import WindowCreatingNewTemplate
from client.services.template_table_service import TemplateTableService

class ClientController:
    creating_window = None

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
                json_request = json.dumps(request_data)
                print(f"Отправляемый запрос: {json_request}")  # Логирование перед отправкой
                compressed_data = zlib.compress(json.dumps(request_data).encode('utf-8'))
                s.sendall(compressed_data)

                compressed_response = s.recv(8192)  # Получаем сжатый ответ
                response = zlib.decompress(compressed_response).decode('utf-8')
                return json.loads(response)
        except ConnectionResetError as e:
            print(f"Connection error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def open_template_constructor_window(self, username):
        template_names = self.get_template_names_in_db()  # Получение списка шаблонов из БД
        print(f"Шаблоны для конструктора: {template_names}")  # Отладка
        self.template_constructor_view = (TemplateConstructorWindow(admin_name=username, template_names=template_names, controller=self))
        self.template_constructor_view.template_selected.connect(self.request_template_data_in_db)
        self.template_constructor_view.create_requested.connect(self.open_create_window)
        self.template_constructor_view.template_save_requested.connect(self.handle_save_template)
        self.template_constructor_view.template_update.connect(self.update_template_data_in_db)
        self.template_constructor_view.delete_template_signal.connect(self.delete_template_in_db)
        self.template_constructor_view.show()

    #Создаем окно для создания нового шаблона.
    def open_create_window(self):
        if not hasattr(self, 'template_constructor_view') or self.template_constructor_view is None:
            print("Ошибка: Конструктор шаблонов еще не инициализирован.")
            return
        if not self.creating_window:
            self.creating_window = WindowCreatingNewTemplate(self.template_constructor_view)
            self.creating_window.settings_applied.connect(self.apply_settings_to_table)
        self.creating_window.show()

    def apply_settings_to_table(self, rows, cols, template_name, color):
        # Обновление структуры таблицы и имени шаблона
        column_labels = [TemplateTableService.generate_col_name(col) for col in range(cols)]
        self.template_constructor_view.update_table_structure(rows, cols, column_labels)
        self.template_constructor_view.update_template_name(template_name)
        self.template_constructor_view.update_background_color(color)

    def refresh_template_in_window(self, template_data):
        TemplateTableService.refresh_table_view(self.template_constructor_view.table, template_data)
        # Извлекаем цвет фона из данных шаблона
        background_color = template_data.get("background_color", "#FFFFFF")
        # Передаём цвет фона в представление
        self.template_constructor_view.update_background_color(background_color)

    def handle_save_template(self):
        """Обрабатывает запрос на сохранение шаблона из представления."""
        if not self.template_constructor_view.template_name:
            self.show_message_box("Ошибка", "Имя шаблона не задано. Пожалуйста, введите имя в окне создания шаблона.")
            return
        #Получаем данные шаблона
        rows = self.template_constructor_view.table.rowCount()
        cols = self.template_constructor_view.table.columnCount()
        cell_data = TemplateTableService.collect_table_data(self.template_constructor_view.table)
        background_color = self.template_constructor_view.background_color
        #Проверяем на наличие шаблона с таким именем
        if self.check_template_exists_in_db(self.template_constructor_view.template_name):
            confirm = QMessageBox.question(
                self.template_constructor_view,
                "Перезаписать шаблон?",
                f"Шаблон с именем '{self.template_constructor_view.template_name}' уже существует. Перезаписать данные шаблона?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.update_template_data_in_db(self.template_constructor_view.template_name,
                                                rows, cols, cell_data, background_color)
        else:
            self.save_template_in_db(self.template_constructor_view.template_name, rows, cols, cell_data, background_color)

    def refresh_template_combo_box_in_window(self, new_template_name):
        if hasattr(self, 'template_constructor_view') and self.template_constructor_view:
            self.template_constructor_view.add_template_name_to_combo(new_template_name)
        else:
            print("Ошибка: объект template_constructor_view не инициализирован.")

    def check_template_exists_in_db(self, template_name):
        request_data = {
            "type": "CHECK_TEMPLATE_EXISTS",
            "data": {"template_name": template_name}
        }
        response = ClientController.send_request_to_server(request_data)

        if response.get("status") == "exists":
            return True
        else:
            return False

    def get_template_names_in_db(self):
        request_data = {
            "type": "GET_TEMPLATE_NAMES",
            "data": None
        }
        response = ClientController.send_request_to_server(request_data)
        if response and response.get("status") == "success":
            template_names = response.get("template_names", [])
            return template_names
        else:
            return []

    def get_user_name_in_db(self, username, password):
        request_data = {
            "type": "LOGIN",
            "data": {
                "username": username,
                "password": password
            }
        }
        response = ClientController.send_request_to_server(request_data)
        if response and response.get("status") == "success":
            print('Login successful')
            role = response.get("role")
            admin_name = response.get("name")
            if role == 'admin':
                self.login_pass_view.close()
                self.open_template_constructor_window(admin_name)
            else:
                print('Access denied: User is not an admin')
        else:
            print('Invalid credentials')

    def request_template_data_in_db(self, template_name):
        request_data = {
            "type": "GET_TEMPLATE_DATA",
            "data": template_name
        }
        response = ClientController.send_request_to_server(request_data)

        if response:
            # Если response уже словарь, используйте его напрямую
            if isinstance(response, dict):
                template_data = response
            else:
                # На случай, если сервер вернет строку, делаем проверку
                template_data = json.loads(response)

            self.refresh_template_in_window(template_data)

    def update_template_data_in_db(self, template_name, row_count, col_count, cell_data, background_color):
        request_data = {
            "type": "UPDATE_TEMPLATE",
            "data": {
                "template_name": template_name,
                "row_count": row_count,
                "col_count": col_count,
                "cell_data": cell_data,
                "background_color": background_color
            }
        }
        response = ClientController.send_request_to_server(request_data)

        if response.get("status") == "success":
            ClientController.show_message_box(self, "Обновление шаблона", f"Шаблон '{template_name}' успешно обновлен.")
        else:
            print("Не удалось обновить шаблон.")

    def save_template_in_db(self, template_name, row_count, col_count, cell_data, background_color):
        # Сначала проверяем, существует ли уже шаблон с таким именем
        if self.check_template_exists_in_db(template_name):
            ClientController.show_message_box(
                self, "Ошибка", f"Шаблон с именем '{template_name}' уже существует.", QMessageBox.Warning
            )
            return
        else:
            request_data = {
                "type": "SAVE_TEMPLATE",
                "data": {
                    "template_name": template_name,
                    "row_count": row_count,
                    "col_count": col_count,
                    "cell_data": cell_data,
                    "background_color": background_color
                }
            }
            response = ClientController.send_request_to_server(request_data)

            if response.get("status") == "success":
                self.refresh_template_combo_box_in_window(template_name)
                self.template_constructor_view.set_current_template_in_combo(template_name)
            else:
                print("Не удалось сохранить шаблон.")

    def delete_template_in_db(self, template_name):
        # Сначала проверяем, существует ли уже шаблон с таким именем
        if self.check_template_exists_in_db(template_name):
            request_data = {
                "type": "DELETE_TEMPLATE",
                "data": template_name
            }
            response = ClientController.send_request_to_server(request_data)

            if response.get("status") == "success":
                self.template_constructor_view.remove_template_name_from_combo(template_name)
                ClientController.show_message_box(
                    self, "Удаление шаблона", f"Шаблон '{template_name}' успешно удален."
                )
            else:
                ClientController.show_message_box(
                    self, "Ошибка удаления", "Не удалось удалить шаблон.", QMessageBox.Warning
                )

    def handle_unmerge_cells_request(self, top_row, bottom_row, left_col, right_col):
        """Обрабатывает запрос на отмену объединения ячеек."""
        TemplateTableService.unmerge_cells(self.template_constructor_view.table, top_row, bottom_row, left_col, right_col)

    def handle_merge_cells_request(self, top_row, bottom_row, left_col, right_col):
        """Обрабатывает запрос на объединение ячеек."""
        main_value = self.template_constructor_view.table.item(top_row, left_col).text() \
        if self.template_constructor_view.table.item(top_row, left_col) \
            else ""
        TemplateTableService.merge_cells(self.template_constructor_view.table, top_row, bottom_row, left_col, right_col,
                                         main_value)