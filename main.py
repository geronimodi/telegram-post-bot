import sys
from PyQt6.QtWidgets import QApplication
from gui import TelegramBotGUI  # Импортируем класс TelegramBotGUI из gui.py


def main():
    app = QApplication(sys.argv)
    window = TelegramBotGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()