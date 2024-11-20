# client/views/template_constructor_window.py
import json
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QTableWidget, QHBoxLayout, \
    QTableWidgetItem, QMessageBox, QFontComboBox
from PySide6.QtCore import Qt, Signal, QFile, QSize

from client.services.template_table_service import TemplateTableService
from client.views.window_creating_new_template import WindowCreatingNewTemplate


class TemplateConstructorWindow(QWidget):
    create_requested = Signal()  # Открытия окна настроек
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
        self.font_combo_box = None
        self.background_color = "#FFFFFF"

        self.init_ui()
        self.load_styles()

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

        # Кнопка для открытия окна создания шаблона
        settings_button = QPushButton("Создать новый шаблон")
        settings_button.clicked.connect(
            self.open_create_template_window)  # Подключаем к методу для открытия окна создания
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

        # Определяем текущую директорию, в которой находится данный файл
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path_merge_cells = os.path.join(current_dir, "..", "icons", "merge_cells.png")
        # Кнопка "Объединить" — стилизуем её как кнопку объединения ячеек
        merge_button = QPushButton()
        merge_button.setIcon(QIcon(icon_path_merge_cells))
        merge_button.setIconSize(QSize(24, 24))  # Устанавливаем размер иконки
        merge_button.setFixedSize(24, 24)
        merge_button.clicked.connect(self.handle_merge_cells)
        secondary_menu_layout.addWidget(merge_button)

        # Выбо формат текста
        self.font_combo_box = QFontComboBox()
        self.font_combo_box.setFixedWidth(150)
        self.font_combo_box.currentFontChanged.connect(self.change_font)
        secondary_menu_layout.addWidget(self.font_combo_box)

        bold_button = QPushButton()
        icon_bold_text = os.path.join(current_dir, "..", "icons", "icon_bold_text.png")
        bold_button.setIcon(QIcon(icon_bold_text))
        bold_button.setIconSize(QSize(24, 24))
        bold_button.setFixedSize(24, 24)
        bold_button.clicked.connect(lambda: TemplateTableService.toggle_bold(self.table))
        secondary_menu_layout.addWidget(bold_button)

        italic_button = QPushButton()
        icon_italic_text = os.path.join(current_dir, "..", "icons", "icon_italic_text.png")
        italic_button.setIcon(QIcon(icon_italic_text))
        italic_button.setIconSize(QSize(24, 24))
        italic_button.setFixedSize(24, 24)
        italic_button.clicked.connect(lambda: TemplateTableService.toggle_italic(self.table))
        secondary_menu_layout.addWidget(italic_button)

        underline_button = QPushButton()
        icon_underline_text = os.path.join(current_dir, "..", "icons", "icon_underline_text.png")
        underline_button.setIcon(QIcon(icon_underline_text))
        underline_button.setIconSize(QSize(24, 24))
        underline_button.setFixedSize(24, 24)
        underline_button.clicked.connect(lambda: TemplateTableService.toggle_underline(self.table))
        secondary_menu_layout.addWidget(underline_button)

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

    def open_create_template_window(self):
        # Открытие окна создания нового шаблона
        self.create_template_window = WindowCreatingNewTemplate(self)
        self.create_template_window.settings_applied.connect(self.apply_settings_to_template)
        self.create_template_window.show()

    def apply_settings_to_template(self, rows, cols, template_name, background_color):
        # Применяем настройки
        self.template_name = template_name
        self.background_color = background_color  # Сохраняем цвет фона

        self.update_table_structure(rows, cols, [chr(65 + i) for i in range(cols)])
        self.update_background_color(background_color)

        # Обновляем имя шаблона в метке
        self.update_template_name(template_name)

    def load_styles(self):
        """Загружает стили из файла .qss"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_file_path = os.path.join(current_dir, "..", "styles", "styles.qss")
        file = QFile(style_file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stylesheet = file.readAll().data().decode()
            self.setStyleSheet(stylesheet)
            print("Стили успешно загружены")
        else:
            print(f"Ошибка: не удалось открыть файл стилей по пути: {style_file_path}")

    def change_font(self, font):
        # Получаем список выделенных ячеек
        selected_ranges = self.table.selectedRanges()

        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.table.item(row, col)
                    if item is None:
                        item = QTableWidgetItem()
                        self.table.setItem(row, col, item)

                    # Применяем новый шрифт к ячейке
                    item.setFont(font)

                    # Сохраняем данные о шрифте в Qt.UserRole
                    cell_data_str = item.data(Qt.UserRole)
                    if cell_data_str:
                        cell_data = json.loads(cell_data_str)
                    else:
                        cell_data = {}

                    # Обновляем данные о шрифте
                    cell_data['font'] = font.toString()
                    item.setData(Qt.UserRole, json.dumps(cell_data))

                    # Обновляем отображение
                    item.setTextAlignment(Qt.AlignCenter)

    def handle_function3(self):
        print("Функция 3 выполнена")

    # Выбор имени в комбо-боксе
    def name_on_template_selected(self, template_name):
        self.template_name = template_name
        self.template_name_label.setText(f"Шаблон: {template_name}")

    #Перед отрисовкой нового шаблона необходимо обновить структуру шаблона
    def update_table_structure(self, row_count, col_count, column_labels):
        # Сброс объединений ячеек перед загрузкой нового шаблона
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                self.table.setSpan(row, col, 1, 1)  # Сбрасываем объединение для каждой ячейки

        # Очищаем содержимое таблицы от данных
        self.table.clearContents()
        self.table.setRowCount(row_count)
        self.table.setColumnCount(col_count)
        # Обращается к сервису для генерации цифровых и буквенных имен ячеек
        self.table.setHorizontalHeaderLabels(column_labels)
        self.table.setVerticalHeaderLabels([str(i + 1) for i in range(row_count)])

    def update_template_name(self, template_name):
        # Обновляем имя шаблона в метке
        self.template_name = template_name
        self.template_name_label.setText(f"Шаблон: {template_name}")

    def update_background_color(self, color):
        # Применяем цвет фона к таблице
        self.table.setStyleSheet(f"background-color: {color};")

    def add_template_name_to_combo(self, template_name):
    # Проверяем, что имя шаблона не пустое и не дублируется
        if template_name and template_name not in [self.template_combo.itemText(i) for i in range(self.template_combo.count())]:
            print(f"Добавляем шаблон '{template_name}' в комбо бокс.")
            self.template_combo.addItem(template_name)
        else:
            print(f"Шаблон '{template_name}' уже существует в комбо боксе или имя пустое.")

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

    def handle_merge_cells(self):
        selected_ranges = self.table.selectedRanges()
        if len(selected_ranges) == 1:
            merge_range = selected_ranges[0]
            top_row = merge_range.topRow()
            bottom_row = merge_range.bottomRow()
            left_col = merge_range.leftColumn()
            right_col = merge_range.rightColumn()

            # Проверяем, является ли верхняя левая ячейка объединенной
            if TemplateTableService.is_merged(self.table, top_row, left_col):
                # Если ячейки объединены, отменяем объединение
                self.controller.handle_unmerge_cells_request(top_row, bottom_row, left_col, right_col)
            else:
                # Если ячейки не объединены, выполняем объединение
                self.controller.handle_merge_cells_request(top_row, bottom_row, left_col, right_col)
