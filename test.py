from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton, QColorDialog
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor, QPalette

class DateRangeSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Устанавливаем размеры окна
        self.setFixedSize(400, 250)

        # Устанавливаем цвет фона
        self.setAutoFillBackground(True)
        self.update_background_color("#08BFFD")

        # Основной макет
        main_layout = QVBoxLayout()

        # Горизонтальный макет для выбора интервала времени
        date_selection_layout = QHBoxLayout()

        # Виджет для выбора начальной даты
        start_date_label = QLabel("Начальная дата:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())

        # Виджет для выбора конечной даты
        end_date_label = QLabel("Конечная дата:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())

        # Добавление виджетов в горизонтальный макет
        date_selection_layout.addWidget(start_date_label)
        date_selection_layout.addWidget(self.start_date_edit)
        date_selection_layout.addWidget(end_date_label)
        date_selection_layout.addWidget(self.end_date_edit)

        # Кнопка "Просмотреть отчет"
        report_button = QPushButton("Просмотреть отчет")
        report_button.setStyleSheet("background-color: #99CCFF; color: black; font-weight: bold;")
        report_button.clicked.connect(self.show_selected_dates)

        # Кнопка для выбора цвета фона
        color_button = QPushButton("Выбрать цвет фона")
        color_button.setStyleSheet("background-color: #99CCFF; color: black; font-weight: bold;")
        color_button.clicked.connect(self.open_color_dialog)

        # Добавление горизонтального макета и кнопок в основной макет
        main_layout.addLayout(date_selection_layout)
        main_layout.addWidget(report_button)
        main_layout.addWidget(color_button)

        # Установка основного макета для виджета
        self.setLayout(main_layout)
        self.setWindowTitle("Выбор интервала времени")

    def update_background_color(self, color_code):
        """Обновляет цвет фона окна."""
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color_code))
        self.setPalette(palette)

    def open_color_dialog(self):
        """Открывает диалоговое окно для выбора цвета и обновляет фон."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_background_color(color.name())

    def show_selected_dates(self):
        start_date = self.start_date_edit.date().toString("dd.MM.yyyy")
        end_date = self.end_date_edit.date().toString("dd.MM.yyyy")
        print(f"Выбранный интервал: с {start_date} по {end_date}")

if __name__ == "__main__":
    app = QApplication([])
    window = DateRangeSelector()
    window.show()
    app.exec()
