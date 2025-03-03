import sys
import os
import shutil
import random
import logging
import configparser  #  Добавляем configparser сюда

# Логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#  Имена файлов (теперь просто имена, без путей)
LAST_POST_TIME_FILE_NAME = "last_post_time.json"
PHRASES_FILE_NAME = "phrases.txt"
CONFIG_FILE_NAME = "config.ini"

EMOJIS = ["🍆", "💦", "🔥", "😏", "✨", "🤗", "🎨", "👇"]

def resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсу, работает и для PyInstaller, и для обычного запуска.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def get_app_data_path(filename):
    """
    Получает путь к файлу в папке AppData. Создает папку, если нужно.
    """
    app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TelegramBot") # Можно Roaming, вместо Local
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    return os.path.join(app_data_dir, filename)

def check_disk_space(path, required_space_mb=10):
    """Проверяет, достаточно ли свободного места на диске."""
    try:
        disk_usage = shutil.disk_usage(path)
        free_space_mb = disk_usage.free / (1024 * 1024)  # Переводим в мегабайты
        return free_space_mb >= required_space_mb
    except Exception:
        return False

def generate_phrase_with_emoji(phrases):
    """Генерирует фразу со случайными смайликами."""
    phrase = random.choice(phrases)
    num_emojis = random.randint(1, 3)
    emojis = random.choices(EMOJIS, k=num_emojis)
    return phrase + " " + "".join(emojis)

def load_phrases(filename=PHRASES_FILE_NAME):
    """
    Загружает фразы.
    Сначала пытается загрузить измененный файл из AppData,
    если не находит - загружает из ресурсов.
    """
    app_data_file = get_app_data_path(filename)
    phrases = []

    # Пытаемся загрузить из AppData
    if os.path.exists(app_data_file):
        try:
            with open(app_data_file, "r", encoding="utf-8") as f:
                for line in f:
                    phrases.append(line.strip())
        except Exception as e:
            logger.error(f"Ошибка при загрузке фраз из AppData: {e}")
            # Если не получилось - продолжаем, будем загружать из ресурсов

    # Если в AppData файла нет или не загрузился, грузим из ресурсов
    if not phrases:
        try:
            with open(resource_path(filename), "r", encoding="utf-8") as f:
                for line in f:
                    phrases.append(line.strip())
        except FileNotFoundError:
            logger.error(f"Файл с фразами '{filename}' не найден (ни в AppData, ни в ресурсах)!")
            return ["Вот это да!...", "Шикарно!..", "Огонь! 🔥"]  # Стандартные фразы

    return phrases


def save_phrases(phrases, filename=PHRASES_FILE_NAME):
    """Сохраняет фразы в AppData."""
    app_data_file = get_app_data_path(filename)
    if not check_disk_space(os.path.dirname(app_data_file)):
        logger.error(f"Недостаточно места на диске для сохранения фраз.")
        return  # Выходим, если недостаточно места
    try:
        with open(app_data_file, "w", encoding="utf-8") as f:
            for phrase in phrases:
                f.write(phrase + "\n")
        logger.info("Фразы сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении фраз: {e}")