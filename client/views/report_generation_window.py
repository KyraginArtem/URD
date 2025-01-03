import json
import os

from PySide6.QtCore import QDate, QSize, Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHBoxLayout,
    QComboBox, QDateEdit
)

from client.services.template_table_service import TemplateTableService


class ReportWindow(QWidget):
    create_report = Signal(str, str, str)
    data_processed = Signal(dict, str, str)

    def __init__(self, template_data, start_date, end_date, template_name , user_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Отчеты")
        self.resize(1000, 700)
        self.start_date = start_date
        self.end_date = end_date
        self.template_name = template_name
        self.user_name = user_name
        self.data_processed.connect(self.update_data_report)

        # Данные шаблона
        self.template_data = template_data

        # Инициализируем интерфейс
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.create_top_panel())  # Верхняя панель
        # Создаем таблицу c параметрами и конфигурациями
        self.table = QTableWidget(self.template_data["rows"], self.template_data["cols"])
        main_layout.addWidget(self.table)

        self.download_table()

    def create_top_panel(self):
        """
        Создает верхнюю панель с выпадающим меню, кнопками, метками.
        """
        layout = QHBoxLayout()

        # Выпадающее меню для выбора шаблона
        self.template_combo = QComboBox()

        # Извлекаем только имена шаблонов из списка словарей
        template_names = [template['name'] for template in self.template_name]

        # Добавляем их в выпадающее меню
        self.template_combo.addItems(template_names)

        # Подключаем сигнал изменения текста
        self.template_combo.currentTextChanged.connect(self.name_on_template_selected)

        layout.addWidget(self.template_combo)
        # Поля для выбора даты
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))  # Устанавливаем начальную дату по умолчанию
        layout.addWidget(QLabel("С даты:"))
        layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())  # Устанавливаем текущую дату по умолчанию
        layout.addWidget(QLabel("По дату:"))
        layout.addWidget(self.end_date_edit)

        # Кнопка для формирования отчета
        generate_report_button = QPushButton("Сформировать отчет")
        generate_report_button.clicked.connect(
            lambda: self.create_report.emit(
                self.template_combo.currentText(),
                self.start_date_edit.date().toString("yyyy-MM-dd"),
                self.end_date_edit.date().toString("yyyy-MM-dd")
            )
        )
        layout.addWidget(generate_report_button)

        download_file = QPushButton()
        download_file.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "icons", "icon_download.png")))
        download_file.setIconSize(QSize(24, 24))
        download_file.setFixedSize(24, 24)
        download_file.clicked.connect(lambda: TemplateTableService().export_to_excel(self.table))
        layout.addWidget(download_file)

        # Метка имени администратора
        admin_label = QLabel(self.user_name)
        admin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(admin_label)

        return layout

    def download_table(self):
        """
        Загружает данные в таблицу. Обрабатывает конфигурации и типы ячеек.
        """
        # Очистка таблицы
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        # Устанавливаем фон таблицы
        self.table.setStyleSheet(f"background-color: {self.template_data['background_color']}")

        # Устанавливаем размер таблицы
        self.table.setRowCount(self.template_data["rows"])
        self.table.setColumnCount(self.template_data["cols"])

        # Устанавливаем буквенные заголовки столбцов
        header_labels = [TemplateTableService.generate_col_name(i) for i in range(self.table.columnCount())]
        self.table.setHorizontalHeaderLabels(header_labels)

        # Заполняем таблицу данными
        for cell_info in self.template_data["cell_data"]:
            # Получаем позицию ячейки
            cell_name = cell_info["cell_name"]
            row_index, col_index = TemplateTableService.parse_cell_position(cell_name)

            cell_config = cell_info.get("config", {})

            if cell_info.get("type") == "list":
                # Если данные множественные, распределяем их по строкам
                values = cell_info["value"]
                if isinstance(values, dict) and len(values) == 1:
                    key = next(iter(values))
                    values = values[key]

                self.shift_rows_down(row_index + 1, len(values) - 1)

                for offset, value in enumerate(values):
                    target_row = row_index + offset
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(target_row, col_index, item)
                    TemplateTableService.apply_cell_configuration(item, self.table, target_row, col_index, cell_config)

            elif cell_info.get("type") == "single":
                cell_value = str(cell_info["value"]) if cell_info["value"] is not None else ""
                item = QTableWidgetItem(cell_value)
                self.table.setItem(row_index, col_index, item)
                TemplateTableService.apply_cell_configuration(item, self.table, row_index, col_index, cell_config)

        # Применяем объединение ячеек
        for cell_info in self.template_data["cell_data"]:
            merge_range = cell_info["config"].get("merger")
            if merge_range:
                TemplateTableService.apply_merged_cells(self.table, [merge_range])

        self.table.viewport().update()

    def shift_rows_down(self, start_row, count):
        """
        Сдвигает строки вниз начиная с `start_row` на `count` строк.
        """
        current_row_count = self.table.rowCount()
        new_row_count = max(current_row_count + count, start_row + count)

        # Увеличиваем количество строк в таблице
        TemplateTableService.resize_table(self.table, new_row_count, self.table.columnCount(),
                                          self.template_data['background_color'])

        # Сдвигаем строки вниз
        for row in range(current_row_count - 1, start_row - 1, -1):
            for col in range(self.table.columnCount()):
                # Получаем текущую ячейку
                item = self.table.takeItem(row, col)
                if item:
                    # Перемещаем ячейку вниз
                    self.table.setItem(row + count, col, item)

    def name_on_template_selected(self, template_name):
        self.template_name = template_name
        print(f"Шаблон выбран: {template_name}")

    def update_data_report(self, new_template_data, new_start_date, new_end_date):
        """
        Обновляет данные отчета и перезагружает таблицу.
        """
        self.template_data = new_template_data
        self.start_date = new_start_date
        self.end_date = new_end_date

        # Перезагружаем таблицу с новыми данными
        self.download_table()