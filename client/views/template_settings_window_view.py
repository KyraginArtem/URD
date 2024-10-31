# client/views/template_settings_window_view.py
from PySide6.QtWidgets import QWidget, QFormLayout, QSpinBox, QPushButton, QLineEdit
from PySide6.QtCore import Qt, Signal

class TemplateSettingsWindow(QWidget):
    # Определяем сигнал для передачи новых значений строк и столбцов
    settings_applied = Signal(int, int, str)

    def __init__(self, parent_view):
        super().__init__()
        self.template_name_input = None
        self.row_spinbox = None
        self.col_spinbox = None
        self.parent_view = parent_view
        self.setWindowTitle("Настройки шаблона")
        self.resize(600, 500)
        self.setWindowModality(Qt.ApplicationModal)  # Устанавливаем модальность окна
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        self.template_name_input = QLineEdit()

        layout.addRow("Название шаблона", self.template_name_input)

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
        rows = self.row_spinbox.value()
        cols = self.col_spinbox.value()
        template_name = self.template_name_input.text().strip()
        if not template_name:
            print("Имя шаблона не может быть пустым.")
            return
        self.settings_applied.emit(rows, cols, template_name)
        self.close()