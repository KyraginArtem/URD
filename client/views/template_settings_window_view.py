# client/views/template_settings_window_view.py
from PySide6.QtWidgets import QWidget, QFormLayout, QSpinBox, QPushButton
from PySide6.QtCore import Qt, Signal

class TemplateSettingsWindow(QWidget):
    # Определяем сигнал для передачи новых значений строк и столбцов
    settings_applied = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройки шаблона")
        self.resize(600, 500)
        self.setWindowModality(Qt.ApplicationModal)  # Устанавливаем модальность окна
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        # Настройка количества строк
        self.row_spinbox = QSpinBox()
        self.row_spinbox.setMinimum(1)
        self.row_spinbox.setMaximum(1000)
        self.row_spinbox.setValue(10)
        layout.addRow("Количество строк", self.row_spinbox)

        # Настройка количества столбцов
        self.col_spinbox = QSpinBox()
        self.col_spinbox.setMinimum(1)
        self.col_spinbox.setMaximum(1000)
        self.col_spinbox.setValue(10)
        layout.addRow("Количество столбцов", self.col_spinbox)

        # Кнопка для применения изменений
        apply_button = QPushButton("Применить")
        apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(apply_button)

        self.setLayout(layout)

    def apply_settings(self):
        # Получение новых значений строк и столбцов
        rows = self.row_spinbox.value()
        cols = self.col_spinbox.value()

        # Эмитируем сигнал с новыми значениями строк и столбцов
        self.settings_applied.emit(rows, cols)

        # Закрываем окно после применения настроек
        self.close()
