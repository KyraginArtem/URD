# ========== Импорты ==========
import json
import os
from PySide6 import QtGui
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QTableWidget,
    QHBoxLayout, QTableWidgetItem, QMessageBox, QFontComboBox, QColorDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QFile, QSize
from client.services.table_cell_parser import TableCellParser
from client.services.template_table_service import TemplateTableService
from client.views.window_creating_new_template import WindowCreatingNewTemplate

# ========== Класс TemplateConstructorWindow ==========
class TemplateConstructorWindow(QWidget):
    # -------- Сигналы --------
    create_requested = Signal()  # Открытие окна настроек
    template_selected = Signal(str)  # Выбор шаблона
    template_save_requested = Signal()  # Сохранение шаблона
    delete_template_signal = Signal(str)  # Удаление шаблона
    template_update = Signal(str, int, int, str)  # Обновление шаблона

    # -------- Инициализация --------
    def __init__(self, admin_name, template_names, controller):
        super().__init__()
        self.setWindowTitle("Редактор шаблонов")
        self.resize(1000, 700)

        # Параметры
        self.admin_name = admin_name
        self.template_names = template_names
        self.controller = controller

        # Переменные интерфейса
        self.template_combo = None
        self.template_name = ""
        self.settings_window = None
        self.template_name_label = None
        self.font_combo_box = None
        self.background_color = "#FFFFFF"

        # Инициализация интерфейса
        self.init_ui()
        self.load_styles()

    # -------- Основной метод создания интерфейса --------
    def init_ui(self):
        """
        Формирует весь интерфейс: панель, меню, таблицу.
        """
        # Основной лейаут
        main_layout = QVBoxLayout()

        # Создание и добавление частей интерфейса
        main_layout.addLayout(self.create_top_panel())  # Верхняя панель
        lower_menu = self.create_side_menus()  # нижнее меню меню
        main_layout.addLayout(lower_menu)
        self.create_table(main_layout)  # Таблица

        # Установка лейаута
        self.setLayout(main_layout)

    # -------- Методы создания секций интерфейса --------
    def create_top_panel(self):
        """
        Создает верхнюю панель с выпадающим меню, кнопками, метками.
        """
        layout = QHBoxLayout()

        # Выпадающее меню для выбора шаблона
        self.template_combo = QComboBox()
        self.template_combo.addItems(self.template_names)
        self.template_combo.currentTextChanged.connect(self.name_on_template_selected)
        self.template_combo.currentTextChanged.connect(
            lambda: self.template_selected.emit(self.template_combo.currentText())
        )
        layout.addWidget(self.template_combo)

        # Кнопка для создания нового шаблона
        create_button = QPushButton("Создать шаблон")
        create_button.clicked.connect(self.create_requested)
        layout.addWidget(create_button)

        # Метка имени шаблона
        self.template_name_label = QLabel("Шаблон: Не выбран")
        layout.addWidget(self.template_name_label)

        # Метка имени администратора
        admin_label = QLabel(self.admin_name)
        admin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(admin_label)

        return layout

    def create_side_menus(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Нижнее меню
        lower_menu = QHBoxLayout()

        # Кнопка "Объединить"
        merge_button = QPushButton()
        merge_button.setIcon(QIcon(os.path.join(current_dir, "..", "icons", "merge_cells.png")))
        merge_button.setIconSize(QSize(24, 24))
        merge_button.setFixedSize(24, 24)
        merge_button.clicked.connect(self.handle_merge_cells)
        lower_menu.addWidget(merge_button)

        #Выделенный текст
        bold_button = self.create_icon_button("icon_bold_text.png",
                                              lambda: TemplateTableService.toggle_bold(self.table))
        lower_menu.addWidget(bold_button)

        #наклон текста
        italic_button = self.create_icon_button("icon_italic_text.png",
                                              lambda: TemplateTableService.toggle_italic(self.table))
        lower_menu.addWidget(italic_button)

        #подчеркивание
        underline_button = self.create_icon_button("icon_underline_text.png",
                                                lambda: TemplateTableService.toggle_underline(self.table))
        lower_menu.addWidget(underline_button)

        #цвет текста
        text_color = self.create_icon_button("icon_color_text.png", lambda: self.change_text_color())
        lower_menu.addWidget(text_color)

        #цвет ячейки
        cell_color = self.create_icon_button("icon_color_cell.png", lambda:  self.change_cell_color())
        lower_menu.addWidget(cell_color)

        #цвет фона
        template_background_color = self.create_icon_button("icon_background.png",
                                                            lambda: self.change_template_background_color())
        lower_menu.addWidget(template_background_color)

        #Увеличить значение после запятой
        increase_decimal = self.create_icon_button("icon_increase_decimal.png",
                                        lambda: TemplateTableService.change_decimal_places(self.table, increase=True))
        lower_menu.addWidget(increase_decimal)

        #Уменьшить значение после запятой
        decrease_decimal = self.create_icon_button("icon_increase_decimal.png",
                                    lambda: TemplateTableService.change_decimal_places(self.table, increase=False))
        lower_menu.addWidget(decrease_decimal)

        #Выбор шрифта
        self.font_combo_box = QFontComboBox()
        self.font_combo_box.setFixedWidth(150)
        self.font_combo_box.currentFontChanged.connect(self.change_font)
        lower_menu.addWidget(self.font_combo_box)

        # Добавляем выпадающий список для выбора размера шрифта
        font_size_combo_box = QComboBox()
        font_size_combo_box.setFixedSize(40, 24)  # Устанавливаем размер
        font_size_combo_box.addItems([str(size) for size in range(8, 73, 2)])  # Размеры шрифтов от 8 до 72 с шагом 2
        font_size_combo_box.currentTextChanged.connect(
            lambda size: TemplateTableService.change_font_size(self.table, int(size)))
        lower_menu.addWidget(font_size_combo_box)

        # Поле для ввода количества строк
        row_input = QLineEdit()
        row_input.setFixedWidth(30)  # Устанавливаем ширину поля
        row_input.setValidator(QtGui.QIntValidator(1, 99))  # Ограничиваем ввод только числами от 1 до 1000
        lower_menu.addWidget(row_input)

        # Поле для ввода количества столбцов
        column_input = QLineEdit()
        column_input.setFixedWidth(30)
        column_input.setValidator(QtGui.QIntValidator(1, 99))
        lower_menu.addWidget(column_input)

        #Кнопка применить изменения размера
        resize_button = self.create_icon_button("icon_check.png",
                                            lambda: TemplateTableService.resize_table(self.table,
                                            int(row_input.text()), int(column_input.text()), self.background_color))
        lower_menu.addWidget(resize_button)

        download_file = self.create_icon_button("icon_download.png",
                                            lambda: TemplateTableService().export_to_excel(self.table))
        lower_menu.addWidget(download_file)

        save_button = self.create_icon_button("icon_save.png", self.template_save_requested.emit)
        lower_menu.addWidget(save_button)

        delete_button = self.create_icon_button("icon_delete.png", self.delete_template)
        lower_menu.addWidget(delete_button)
        lower_menu.setSpacing(10)

        return lower_menu

    def create_table(self, layout):
        """
        Создает таблицу и добавляет её в лейаут.
        """
        self.table = QTableWidget(0, 0)
        self.table.setHorizontalHeaderLabels([chr(65 + i) for i in range(4)])
        self.table.setVerticalHeaderLabels([str(i + 1) for i in range(4)])
        self.table.itemChanged.connect(lambda item: self.handle_cell_change(item.row(), item.column()))
        layout.addWidget(self.table)

    def create_icon_button(self, icon_name, callback):
        """
        Создает кнопку с иконкой.
        """
        button = QPushButton()
        button.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "icons", icon_name)))
        button.setIconSize(QSize(24, 24))
        button.setFixedSize(24, 24)
        button.clicked.connect(callback)
        return button

    # -------- Загрузка стилей --------
    def load_styles(self):
        """
        Загружает стили из файла .qss.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_file_path = os.path.join(current_dir, "..", "styles", "styles.qss")
        file = QFile(style_file_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stylesheet = file.readAll().data().decode()
            self.setStyleSheet(stylesheet)
            print("Стили успешно загружены")
        else:
            print(f"Ошибка: не удалось открыть файл стилей по пути: {style_file_path}")

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

    #Метод закомментирован для оптимизации
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

    def change_text_color(self):
        """Открывает палитру для выбора цвета текста и применяет его к выделенным ячейкам."""
        color = QColorDialog.getColor()
        if color.isValid():
            TemplateTableService.apply_text_color(self.table, color.name())

    def change_cell_color(self):
        """Открывает палитру для выбора цвета фона ячейки и применяет его к выделенным ячейкам."""
        color = QColorDialog.getColor()
        if color.isValid():
            TemplateTableService.apply_cell_background_color(self.table, color.name())

    def change_template_background_color(self):
        """Открывает палитру для изменения общего цвета фона шаблона."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.background_color = color.name()
            self.table.setStyleSheet(f"background-color: {self.background_color};")


    def update_background_color(self, color):
        """Обновляет цвет фона таблицы."""
        self.background_color = color  # Сохраняем цвет в переменную
        self.table.setStyleSheet(f"background-color: {color};")

    def handle_cell_change(self, row, col):
        """
        Обрабатывает изменение значения в ячейке. Если текст начинается с '=', выполняется парсинг формулы.
        """
        item = self.table.item(row, col)
        if not item:
            return

        text = item.text().strip()
        if text.startswith("="):
            try:
                result = TableCellParser.parse_formula(text, self.table)
                # Сохраняем результат в ячейку
                item.setText(str(result))

                # Сохраняем формулу в Qt.UserRole для восстановления
                cell_data_str = item.data(Qt.UserRole)
                cell_data = json.loads(cell_data_str) if cell_data_str else {}
                cell_data["formula"] = text
                item.setData(Qt.UserRole, json.dumps(cell_data))
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка формулы", str(e))