# client/views/template_constructor_view.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox, QPushButton, QTableWidget, QHBoxLayout, QSpinBox, QFormLayout
from PySide6.QtCore import Qt, Signal

class TemplateConstructorWindow(QWidget):
    settings_requested = Signal()  # Сигнал для запроса открытия окна настроек

    def __init__(self, admin_name, template_names):
        super().__init__()
        self.admin_name = admin_name
        self.template_names = template_names
        # Устанавливаем заголовок окна
        self.setWindowTitle("Редактор шаблонов")
        # Инициализируем пользовательский интерфейс
        self.init_ui()

    def init_ui(self):
        # Основной вертикальный макет
        main_layout = QVBoxLayout()

        # Верхняя панель с выпадающим меню, кнопкой и именем администратора
        top_panel_layout = QHBoxLayout()

        # Выпадающее меню для выбора шаблона
        self.template_combo = QComboBox()
        self.template_combo.addItems(self.template_names)
        top_panel_layout.addWidget(self.template_combo)

        # Кнопка для открытия настроек шаблона
        settings_button = QPushButton("Настройки Шаблона")
        settings_button.clicked.connect(self.settings_requested.emit)  # Эмитируем сигнал при нажатии
        top_panel_layout.addWidget(settings_button)

        # Метка с именем администратора
        admin_label = QLabel(self.admin_name)
        admin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_panel_layout.addWidget(admin_label)

        # Добавляем верхнюю панель в основной макет
        main_layout.addLayout(top_panel_layout)

        # Таблица для отображения шаблона
        self.table = QTableWidget(10, 10)
        self.table.setHorizontalHeaderLabels([chr(65 + i) for i in range(10)])
        self.table.setVerticalHeaderLabels([str(i + 1) for i in range(10)])
        main_layout.addWidget(self.table)

        # Устанавливаем основной макет
        self.setLayout(main_layout)
