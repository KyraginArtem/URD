from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QListWidget, QPushButton, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt

class AccessSettingsWindow(QMainWindow):
    def __init__(self, template_names, users_names, controller):
        super().__init__()
        self.setWindowTitle("Настройки доступа")
        self.setFixedSize(400, 200)  # Увеличиваем размер окна
        self.controller = controller

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Главный вертикальный лейаут для всего окна
        global_layout = QVBoxLayout()
        central_widget.setLayout(global_layout)

        # Сплиттер между левой и правой частями
        splitter = QSplitter(Qt.Horizontal)

        # Левая часть: Список шаблонов с чекбоксами
        left_widget = QScrollArea()
        left_widget.setWidgetResizable(True)
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_container.setLayout(left_layout)

        self.checkboxes = []
        for template in template_names:
            checkbox = QCheckBox(template)
            left_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        left_layout.addStretch()
        left_widget.setWidget(left_container)

        # Устанавливаем пропорции для левой части (50%)
        left_widget.setFixedWidth(self.width() // 2 - 10)

        # Правая часть: Список имен
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        self.name_list = QListWidget()
        self.name_list.addItems([user['name'] for user in users_names])  # Корректно отображаем имена пользователей
        self.name_list.currentItemChanged.connect(self.on_user_selection_changed)
        right_layout.addWidget(self.name_list)

        # Добавляем лейауты в сплиттер
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Добавляем сплиттер в общий лейаут
        global_layout.addWidget(splitter)

        # Нижняя часть: Кнопка "Применить"
        apply_button = QPushButton("Применить")
        apply_button.setStyleSheet("background-color: #007BFF; color: white; font-weight: bold;")
        apply_button.clicked.connect(self.apply_settings)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(apply_button)
        global_layout.addLayout(bottom_layout)

    def load_data(self, users_names, template_names):
        self.name_list.clear()
        self.name_list.addItems([user['name'] for user in users_names])

        for checkbox in self.checkboxes:
            checkbox.setParent(None)  # Удаляем старые чекбоксы
        self.checkboxes.clear()

        left_layout = self.findChild(QScrollArea).widget().layout()

        for template in template_names:
            checkbox = QCheckBox(template)
            self.checkboxes.append(checkbox)
            left_layout.addWidget(checkbox)
        left_layout.addStretch()

    def apply_settings(self):
        selected_templates = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        selected_name = self.name_list.currentItem().text() if self.name_list.currentItem() else None

        self.controller.update_accessible_templates_for_user(selected_templates, selected_name)
        print("Выбранные шаблоны:", selected_templates)
        print("Выбранное имя:", selected_name)

    def on_user_selection_changed(self, current, previous):
        if current:
            selected_user = current.text()
            print(f"Пользователь выбран: {selected_user}")

            # Получаем доступные шаблоны для пользователя
            accessible_templates = [item['name'] for item in self.controller.get_accessible_templates_for_user_in_db(selected_user)]

            print("Доступные шаблоны:", accessible_templates)

            # Сбрасываем все чекбоксы
            for checkbox in self.checkboxes:
                checkbox.setChecked(False)

            # Отмечаем только те шаблоны, которые доступны пользователю
            for checkbox in self.checkboxes:
                if checkbox.text() in accessible_templates:
                    checkbox.setChecked(True)
