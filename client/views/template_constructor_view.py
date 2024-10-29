# client/views/template_constructor_view.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QTableWidget, QHBoxLayout, \
    QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt, Signal

from client.services.template_table_service import TemplateTableService


class TemplateConstructorWindow(QWidget):
    settings_requested = Signal()  # Открытия окна настроек
    template_selected = Signal(str)  # Выбор шаблона
    template_save_requested = Signal()
    delete_template_signal = Signal(str)
    template_update = Signal(str, int, int, str)

    def __init__(self, admin_name, template_names, controller):
        super().__init__()
        self.setWindowTitle("Редактор шаблонов")
        self.resize(1000, 700)
        self.admin_name = admin_name
        self.template_names = template_names
        self.controller = controller

        self.template_combo = None
        self.template_name = ""
        self.settings_window = None
        self.template_name_label = None

        self.init_ui()
    def init_ui(self):
        main_layout = QVBoxLayout()
        top_panel_layout = QHBoxLayout()
        secondary_menu_layout = QHBoxLayout()

        # Выпадающее меню для выбора шаблона
        self.template_combo = QComboBox()
        self.template_combo.addItems(self.template_names)
        self.template_combo.currentTextChanged.connect(self.name_on_template_selected)
        self.template_combo.currentTextChanged.connect(lambda: self.template_selected.emit(self.template_combo.currentText()))  # Подключаем сигнал выбора шаблона
        top_panel_layout.addWidget(self.template_combo)

        # Кнопка для открытия настроек шаблона
        settings_button = QPushButton("Создать новый шаблон")
        settings_button.clicked.connect(self.settings_requested.emit)  # Эмитируем сигнал при нажатии
        top_panel_layout.addWidget(settings_button)

        # Метка для отображения имени шаблона
        self.template_name_label = QLabel("Шаблон: Не выбран")
        top_panel_layout.addWidget(self.template_name_label)

        # Метка с именем администратора
        admin_label = QLabel(self.admin_name)
        admin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_panel_layout.addWidget(admin_label)

        # Добавляем верхнюю панель в основной макет
        main_layout.addLayout(top_panel_layout)
        main_layout.addLayout(secondary_menu_layout)

        function1_button = QPushButton("Функция 1")
        function1_button.clicked.connect(self.handle_function1)  # Связать с функцией обработки
        secondary_menu_layout.addWidget(function1_button)

        function2_button = QPushButton("Функция 2")
        function2_button.clicked.connect(self.handle_function2)  # Связать с другой функцией
        secondary_menu_layout.addWidget(function2_button)

        function3_button = QPushButton("Функция 3")
        function3_button.clicked.connect(self.handle_function3)  # Добавить больше кнопок по мере необходимости
        secondary_menu_layout.addWidget(function3_button)

        # Таблица для отображения шаблона
        self.table = QTableWidget(4, 4)
        self.table.setHorizontalHeaderLabels([chr(65 + i) for i in range(10)])
        self.table.setVerticalHeaderLabels([str(i + 1) for i in range(10)])
        main_layout.addWidget(self.table)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.template_save_requested.emit)
        main_layout.addWidget(save_button)

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(self.delete_template)
        main_layout.addWidget(delete_button)

        # Устанавливаем основной макет
        self.setLayout(main_layout)

    def handle_function1(self):
        print("Функция 1 выполнена")

    def handle_function2(self):
        print("Функция 2 выполнена")

    def handle_function3(self):
        print("Функция 3 выполнена")

    #Выбор имени в комбо-боксе
    def name_on_template_selected(self, template_name):
        self.template_name = template_name
        self.template_name_label.setText(f"Шаблон: {template_name}")


    def update_table_structure(self, row_count, col_count):
        self.table.setRowCount(row_count)
        self.table.setColumnCount(col_count)
        column_labels = [TemplateTableService.generate_cell_name(0, col) for col in range(col_count)]
        self.table.setHorizontalHeaderLabels(column_labels)
        self.table.setVerticalHeaderLabels([str(i + 1) for i in range(row_count)])

    def apply_settings_to_table(self, rows, cols, template_name):
        # Обновление структуры таблицы и имени шаблона
        self.update_table_structure(rows, cols)
        self.update_template_name(template_name)

    def update_background_color(self, color):
        # Применяем цвет фона к таблице
        self.table.setStyleSheet(f"background-color: {color};")

    def update_template_name(self, template_name):
        # Обновляем имя шаблона в метке
        self.template_name = template_name
        self.template_name_label.setText(f"Шаблон: {template_name}")

    def add_template_name_to_combo(self, template_name):
        # Проверяем, что имя шаблона не пустое и не дублируется
        if template_name and template_name not in [self.template_combo.itemText(i) for i in
                                                   range(self.template_combo.count())]:
            print(f"Добавляем шаблон '{template_name}' в комбо бокс.")
            self.template_combo.addItem(template_name)
        else:
            print(f"Шаблон '{template_name}' уже существует в комбо боксе или имя пустое.")

    def update_table_data(self, parsed_data):
        """Обновляет данные таблицы на основе переданных данных."""
        # Очистка таблицы перед обновлением данных
        self.table.clearContents()

        # Обновляем данные в таблице на основе полученного списка
        for row_index, col_index, value in parsed_data:
            if 0 <= row_index < self.table.rowCount() and 0 <= col_index < self.table.columnCount():
                self.table.setItem(row_index, col_index, QTableWidgetItem(value))

    def remove_template_name_from_combo(self, template_name):
        index = self.template_combo.findText(template_name)
        if index != -1:
            self.template_combo.removeItem(index)

    def set_current_template_in_combo(self, template_name):
        # Устанавливаем текущий элемент в комбо-боксе на только что добавленный шаблон
        index = self.template_combo.findText(template_name)
        if index != -1:
            self.template_combo.setCurrentIndex(index)

    def delete_template(self):
        if not self.template_name:
            QMessageBox.warning(self, "Ошибка удаления", "Пожалуйста, выберите шаблон для удаления.")
            return
        confirm = QMessageBox.question(
            self, "Подтверждение удаления", f"Вы уверены, что хотите удалить шаблон '{self.template_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.delete_template_signal.emit(self.template_name)


