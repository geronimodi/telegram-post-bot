from PyQt6.QtWidgets import (
    QWidget, QPushButton, QTextEdit, QLabel, QVBoxLayout,
    QFileDialog, QListWidget, QLineEdit, QMessageBox, QDialog,
    QHBoxLayout, QSystemTrayIcon, QMenu, QInputDialog, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QMetaObject, QSize, Q_ARG, pyqtSlot
from PyQt6.QtGui import QIcon, QAction

from config import load_config, save_config
from utils import resource_path, generate_phrase_with_emoji, check_disk_space, load_phrases, logger
from telegram_bot import send_telegram_post, start_telegram_bot, stop_telegram_bot
import asyncio
import os
import threading
import json
from datetime import datetime


class SettingsDialog(QDialog):
    """Диалог для ввода настроек бота."""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Настройки бота")

        # Создаём поля ввода
        self.token_label = QLabel("BOT_TOKEN:")
        self.token_edit = QLineEdit(self.settings.get("BOT_TOKEN", ""))
        self.channel_id_label = QLabel("CHANNEL_ID:")
        self.channel_id_edit = QLineEdit(str(self.settings.get("CHANNEL_ID", "")))
        self.default_hashtags_label = QLabel("DEFAULT_HASHTAGS:")
        self.default_hashtags_edit = QLineEdit(self.settings.get("DEFAULT_HASHTAGS", ""))
        self.delay_label = QLabel("Задержка (мин):")  #  Удалить, если не используется
        self.delay_input = QLineEdit(str(self.settings.get("DELAY_MINUTES", 60)))

        self.min_delay_label = QLabel("Мин. задержка (мин):")
        self.min_delay_input = QLineEdit(str(self.settings.get("MIN_DELAY_MINUTES", 10)))
        self.max_delay_label = QLabel("Макс. задержка (мин):")
        self.max_delay_input = QLineEdit(str(self.settings.get("MAX_DELAY_MINUTES", 120)))

        self.whitelist_label = QLabel("Белый список (через запятую):")
        self.whitelist_edit = QLineEdit(self.settings.get("WHITELIST_EXTENSIONS", ""))
        self.blacklist_label = QLabel("Черный список (через запятую):")
        self.blacklist_edit = QLineEdit(self.settings.get("BLACKLIST_EXTENSIONS", ""))

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_settings)

        # Размещение виджетов (Layout)
        layout = QVBoxLayout()
        layout.addWidget(self.token_label)
        layout.addWidget(self.token_edit)
        layout.addWidget(self.channel_id_label)
        layout.addWidget(self.channel_id_edit)
        layout.addWidget(self.default_hashtags_label)
        layout.addWidget(self.default_hashtags_edit)
        layout.addWidget(self.delay_label)
        layout.addWidget(self.delay_input)
        layout.addWidget(self.min_delay_label)
        layout.addWidget(self.min_delay_input)
        layout.addWidget(self.max_delay_label)
        layout.addWidget(self.max_delay_input)
        layout.addWidget(self.whitelist_label)
        layout.addWidget(self.whitelist_edit)
        layout.addWidget(self.blacklist_label)
        layout.addWidget(self.blacklist_edit)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    @pyqtSlot()
    def save_settings(self):
        """Сохранение настроек в файл."""
        new_settings = {
            "BOT_TOKEN": self.token_edit.text(),
            "CHANNEL_ID": self.channel_id_edit.text(),
            "DEFAULT_HASHTAGS": self.default_hashtags_edit.text(),
            "FOLDER_PATH": self.settings.get("FOLDER_PATH", "C:\\"),
            "DELAY_MINUTES": self.delay_input.text(),  #  Удалить, если не используется
            "MIN_DELAY_MINUTES": self.min_delay_input.text(),
            "MAX_DELAY_MINUTES": self.max_delay_input.text(),
            "WHITELIST_EXTENSIONS": self.whitelist_edit.text(),
            "BLACKLIST_EXTENSIONS": self.blacklist_edit.text(),
        }

        if not new_settings["BOT_TOKEN"] or not new_settings["CHANNEL_ID"]:
            QMessageBox.critical(self, "Ошибка", "BOT_TOKEN и CHANNEL_ID не могут быть пустыми!")
            return

        try:
            int(new_settings["DELAY_MINUTES"])  #  Удалить, если не используется
            int(new_settings["MIN_DELAY_MINUTES"])
            int(new_settings["MAX_DELAY_MINUTES"])
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Задержки должны быть целыми числами (минуты)!")
            return

        if int(new_settings["MIN_DELAY_MINUTES"]) > int(new_settings["MAX_DELAY_MINUTES"]):
            QMessageBox.critical(self, "Ошибка", "Минимальная задержка не может быть больше максимальной!")
            return

        save_config(new_settings)
        self.settings.update(new_settings)
        self.accept()
        QMessageBox.information(self, "Успех", "Настройки сохранены!")

class PhrasesEditDialog(QDialog):
    """Диалог для редактирования списка фраз."""
    def __init__(self, phrases, parent=None):
        super().__init__(parent)
        self.phrases = phrases  #  Список фраз (не копия!)
        self.setWindowTitle("Редактирование фраз")

        self.phrases_edit = QTextEdit(self)
        self.phrases_edit.setPlainText("\n".join(self.phrases))  #  Загружаем фразы

        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_phrases)
        self.cancel_button = QPushButton("Отмена", self)
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self.phrases_edit)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    @pyqtSlot()
    def save_phrases(self):
        """Сохраняет измененные фразы."""
        new_phrases = self.phrases_edit.toPlainText().splitlines()
        new_phrases = [phrase.strip() for phrase in new_phrases if phrase.strip()]
        self.phrases[:] = new_phrases
        self.accept()

class TelegramBotGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = load_config()
        self.bot_token = self.settings.get("BOT_TOKEN")
        self.channel_id = self.settings.get("CHANNEL_ID")
        self.folder_path = self.settings.get("FOLDER_PATH", "C:\\")
        self.delay_minutes = int(self.settings.get("DELAY_MINUTES", 60))  #  Удалить, если не используется
        self.bot_running = False
        self.loop = asyncio.new_event_loop()
        self.phrases = load_phrases()
        self.send_lock = threading.Lock()

        self.last_post_time = self.load_last_post_time()

        self.initUI()

        if not self.bot_token or not self.channel_id:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, укажите BOT_TOKEN и CHANNEL_ID в настройках.")
            self.show_settings_dialog()

        threading.Thread(target=self.start_loop, daemon=True).start()

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start_bot(self):
        if not self.bot_token or not self.channel_id:
            QMessageBox.warning(self, "Ошибка", "Необходимо указать BOT_TOKEN и CHANNEL_ID.")
            self.show_settings_dialog()
            return
        self.loop.call_soon_threadsafe(asyncio.create_task, start_telegram_bot(self.bot_token, self))

    @pyqtSlot(bool)
    def set_bot_running(self, running):
        self.bot_running = running
        self.btn_start_bot.setEnabled(not running)
        self.btn_stop_bot.setEnabled(running)
        self.btn_settings.setEnabled(not running)

    def stop_bot(self):
        self.loop.call_soon_threadsafe(asyncio.create_task, stop_telegram_bot(self))
        self.set_bot_running(False)
        self.log_output.append("⛔ Бот остановлен")

    def initUI(self):
        self.setWindowTitle("Telegram Бот")

        # Кнопки
        self.btn_send_now = QPushButton("Отправить сейчас", self)
        self.btn_send_now.clicked.connect(self.send_post_now)
        self.btn_send_now.setIcon(QIcon(resource_path("icons/send.png")))
        self.btn_send_now.setIconSize(QSize(24, 24))

        self.btn_start_bot = QPushButton("Запустить бота", self)
        self.btn_start_bot.setIcon(QIcon(resource_path("icons/start.png")))
        self.btn_start_bot.setIconSize(QSize(24, 24))
        self.btn_start_bot.clicked.connect(self.start_bot)

        self.btn_stop_bot = QPushButton("Остановить бота", self)
        self.btn_stop_bot.setIcon(QIcon(resource_path("icons/stop.png")))
        self.btn_stop_bot.setIconSize(QSize(24, 24))
        self.btn_stop_bot.setEnabled(False)
        self.btn_stop_bot.clicked.connect(self.stop_bot)

        self.btn_select_folder = QPushButton("Выбрать папку", self)
        self.btn_select_folder.setIcon(QIcon(resource_path("icons/folder.png")))
        self.btn_select_folder.setIconSize(QSize(24, 24))
        self.btn_select_folder.clicked.connect(self.select_folder)

        self.btn_settings = QPushButton("Настройки", self)
        self.btn_settings.setIcon(QIcon(resource_path("icons/settings.png")))
        self.btn_settings.setIconSize(QSize(24, 24))
        self.btn_settings.clicked.connect(self.show_settings_dialog)

        self.btn_edit_phrases = QPushButton("Редактировать фразы", self)
        self.btn_edit_phrases.clicked.connect(self.show_phrases_dialog)
        self.btn_edit_phrases.setIcon(QIcon(resource_path("icons/edit_note.png")))
        self.btn_edit_phrases.setIconSize(QSize(24, 24))

        self.btn_reset_settings = QPushButton("Сброс настроек", self)
        self.btn_reset_settings.clicked.connect(self.reset_settings)
        self.btn_reset_settings.setIcon(QIcon(resource_path("icons/reset.png")))
        self.btn_reset_settings.setIconSize(QSize(24, 24))

        # Текстовые поля и метки
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.folder_label = QLabel(f"Папка: {self.folder_path}")

        #  Прогресс-бар
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        # Размещение виджетов (Layout)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.btn_select_folder)
        left_layout.addWidget(self.folder_label)
        left_layout.addWidget(self.btn_send_now)
        left_layout.addWidget(self.btn_start_bot)
        left_layout.addWidget(self.btn_stop_bot)
        left_layout.addWidget(self.btn_settings)
        left_layout.addWidget(self.btn_edit_phrases)
        left_layout.addWidget(self.btn_reset_settings)
        left_layout.addWidget(QLabel("Логи:"))
        left_layout.addWidget(self.log_output)
        left_layout.addWidget(self.progress_bar)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        self.setLayout(main_layout)

        self.resize(400, 650)

        # Стиль
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #d3d3d3; }
            QPushButton { background-color: #4a4a4a; border: 1px solid #6a6a6a; border-radius: 4px; padding: 5px; min-width: 80px;}
            QPushButton:hover { background-color: #5a5a5a; }
            QPushButton:pressed { background-color: #3a3a3a; }
            QTextEdit, QListWidget, QLineEdit{ background-color: #3a3a3a; border: 1px solid #6a6a6a; border-radius: 4px; padding: 5px; }
            QLabel{ margin-bottom: 5px; }
            QListWidget { border: none; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #4a4a4a; }
            QListWidget::item:selected { background-color: #5a5a5a; color: #ffffff; }
            QProgressBar {border: 1px solid #6a6a6a; border-radius: 4px; text-align: center; background-color: #3a3a3a; color: #d3d3d3;}
            QProgressBar::chunk {background-color: #4CAF50; }
        """)

        # Иконка в трее
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("icons/app_icon.ico")))
        self.tray_icon.setToolTip("Telegram Bot")

        tray_menu = QMenu()
        show_hide_action = QAction("Показать/Скрыть", self)
        show_hide_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(show_hide_action)

        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        tray_menu.addAction(settings_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    @pyqtSlot()
    def show_phrases_dialog(self):
        """Открывает диалог редактирования фраз."""
        dialog = PhrasesEditDialog(self.phrases, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.save_phrases()
            self.log_output.append("📝 Фразы обновлены.")

    def save_phrases(self):
        """Сохраняет фразы в файл."""
        file_path = resource_path("phrases.txt")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for phrase in self.phrases:
                    f.write(phrase + "\n")
            logger.info("Фразы сохранены.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении фраз: {e}")
            self.log_output.append(f"❌ Ошибка при сохранении фраз: {e}")

    def select_folder(self):
        """Открывает диалог выбора папки и сохраняет путь."""
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder_path:
            self.folder_path = folder_path
            self.settings["FOLDER_PATH"] = folder_path
            self.folder_label.setText(f"Папка: {self.folder_path}")
            logger.info(f"Выбрана папка: {self.folder_path}")
            save_config(self.settings)

    @pyqtSlot()
    def send_post_now(self):
        if not self.bot_running:
            QMessageBox.warning(self, "Предупреждение", "Бот не запущен.")
            return
        self.log_output.append("🚀 Отправка поста...")
        with self.send_lock:
            groups = self.scan_folder()
            if groups:
                self.loop.call_soon_threadsafe(asyncio.create_task, send_telegram_post(self.bot_token, self.channel_id, groups[0], self))
            else:
                self.log_output.append("❌ Нет файлов для отправки.")

    def check_queue(self):
        """Проверяет очередь и отправляет пост, если пришло время."""
        if not self.bot_running:
            return

        with self.send_lock:
            now = datetime.now()
            if self.last_post_time is None:
                next_post_time = now
            else:
                min_delay = int(self.settings.get("MIN_DELAY_MINUTES", 10))
                max_delay = int(self.settings.get("MAX_DELAY_MINUTES", 120))
                random_delay = random.randint(min_delay, max_delay)
                next_post_time = self.last_post_time + timedelta(minutes=random_delay)

            if now >= next_post_time:
                groups = self.scan_folder()
                if groups:
                    self.loop.call_soon_threadsafe(asyncio.create_task, send_telegram_post(self.bot_token, self.channel_id, groups[0], self))

    def scan_folder(self):
        """Сканирует папку и возвращает список *групп* файлов."""
        groups = []
        try:
            entries = []
            for entry_name in os.listdir(self.folder_path):
                entry_path = os.path.join(self.folder_path, entry_name)
                entries.append((entry_path, os.path.getctime(entry_path)))

            entries.sort(key=lambda x: x[1])

            for entry_path, _ in entries:
                if os.path.isfile(entry_path):
                    _, ext = os.path.splitext(entry_path)
                    if ext.lower() in (".jpg", ".jpeg", ".png", ".mp4"):
                        groups.append([entry_path])
                elif os.path.isdir(entry_path):
                    group = []
                    for filename in os.listdir(entry_path):
                        file_path = os.path.join(entry_path, filename)
                        if os.path.isfile(file_path):
                            _, ext = os.path.splitext(filename)
                            if ext.lower() in (".jpg", ".jpeg", ".png", ".mp4"):
                                group.append(file_path)
                    if group:
                        groups.append(group)

        except OSError as e:
            self.log_output.append(f"❌ Ошибка сканирования папки: {e}")
            return []

        return groups

    def save_last_post_time(self):
        """Сохранение времени последнего поста в файл."""
        file_path = resource_path("last_post_time.json")
        if not check_disk_space(os.path.dirname(file_path)):
            QMetaObject.invokeMethod(
                self.log_output, "append", Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "❌ Недостаточно места на диске для сохранения времени последнего поста.")
            )
            return
        try:
            with open(file_path, "w") as f:
                json.dump(self.last_post_time.timestamp(), f)
        except Exception as e:
            logger.error(f"Ошибка сохранения времени последнего поста: {e}")
            QMetaObject.invokeMethod(
                self.log_output, "append", Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"❌ Ошибка сохранения времени последнего поста: {e}")
            )

    def load_last_post_time(self):
        """Загрузка времени последнего поста из файла."""
        file_path = resource_path("last_post_time.json")
        try:
            with open(file_path, "r") as f:
                timestamp = json.load(f)
                return datetime.fromtimestamp(timestamp)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.error(f"Ошибка загрузки времени последнего поста: {e}")
            return None

    @pyqtSlot()
    def show_settings_dialog(self):
        """Показывает диалог настроек."""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.settings
            self.bot_token = self.settings.get("BOT_TOKEN")
            self.channel_id = self.settings.get("CHANNEL_ID")
            self.default_hashtags = self.settings.get("DEFAULT_HASHTAGS")
            self.delay_minutes = int(self.settings.get("DELAY_MINUTES", 60))  #  Удалить, если не используется

    def closeEvent(self, event):
        """Переопределяем обработчик закрытия окна."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Telegram Bot",
            "Приложение свёрнуто в трей",
            QIcon(resource_path("icons/app_icon.ico")),
            2000
        )

    def toggle_window(self):
        """Показывает/скрывает главное окно."""
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()

    @pyqtSlot()
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию."""
        default_settings = {
            "BOT_TOKEN": "",
            "CHANNEL_ID": "",
            "DEFAULT_HASHTAGS": "",
            "FOLDER_PATH": "C:\\",
            "DELAY_MINUTES": "60",  #  Убрали, т.к. используем min/max
            "MIN_DELAY_MINUTES": "50",
            "MAX_DELAY_MINUTES": "70",
            "WHITELIST_EXTENSIONS": ".jpg,.jpeg,.png,.gif,.mp4,.webm,.webp",
            "BLACKLIST_EXTENSIONS": ".txt,.ini,.log,.docx,.pdf,.zip,.rar,.exe,.7z",
        }
        reply = QMessageBox.question(self, 'Сброс настроек',
                                     "Вы уверены, что хотите сбросить настройки к значениям по умолчанию?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.update(default_settings)
            save_config(self.settings)
            self.log_output.append("⚙️ Настройки сброшены к значениям по умолчанию.")
            self.folder_label.setText(f"Папка: {self.settings.get('FOLDER_PATH', 'C:\\')}")


    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()