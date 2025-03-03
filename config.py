import configparser
import os
from utils import check_disk_space, resource_path, get_app_data_path, logger #  Импортируем
# from utils import check_disk_space #  Удалить, если импортировали выше

CONFIG_FILE_NAME = "config.ini"  #  Имя файла (без пути)

def load_config(filename=CONFIG_FILE_NAME):
    """
    Загружает настройки.
    Сначала пытается загрузить измененный файл из AppData,
    если не находит - загружает из ресурсов.
    """

    config = configparser.ConfigParser()
    app_data_file = get_app_data_path(filename) # Путь в AppData
    loaded_from_appdata = False

     # Пытаемся загрузить измененный файл из AppData
    if os.path.exists(app_data_file):
        try:
            config.read(app_data_file, encoding="utf-8")
            loaded_from_appdata = True
        except configparser.Error as e:
            logger.error(f"Ошибка чтения файла конфигурации из AppData ({app_data_file}): {e}")
            #  Если не получилось - продолжаем. Будем загружать из ресурсов

    # Если из AppData не загрузили, грузим из ресурсов
    if not loaded_from_appdata:
        try:
            config.read(resource_path(filename), encoding="utf-8") # Читаем из ресурсов.
        except configparser.Error as e:
            logger.error(f"Ошибка чтения файла конфигурации из ресурсов: {e}")
            return {}  #  Возвращаем пустой словарь, если не удалось прочитать
        except FileNotFoundError:
            logger.error("Файл config.ini не найден.") # Если файла нет
            return {}


    if "Telegram" not in config:
        logger.error(f"В файле конфигурации отсутствует секция [Telegram]!")
        return {}

    settings = {
        "BOT_TOKEN": config.get("Telegram", "BOT_TOKEN", fallback=None),
        "CHANNEL_ID": config.get("Telegram", "CHANNEL_ID", fallback=None),
        "DEFAULT_HASHTAGS": config.get("Telegram", "DEFAULT_HASHTAGS", fallback=""),
        "FOLDER_PATH": config.get("Telegram", "FOLDER_PATH", fallback="C:\\"),
        "DELAY_MINUTES": config.getint("Telegram", "DELAY_MINUTES", fallback=60),
        "MIN_DELAY_MINUTES": config.getint("Telegram", "MIN_DELAY_MINUTES", fallback=10),
        "MAX_DELAY_MINUTES": config.getint("Telegram", "MAX_DELAY_MINUTES", fallback=120),
        "WHITELIST_EXTENSIONS": config.get("Telegram", "WHITELIST_EXTENSIONS", fallback=".jpg,.jpeg,.png,.gif,.mp4,.webm,.webp"),
        "BLACKLIST_EXTENSIONS": config.get("Telegram", "BLACKLIST_EXTENSIONS", fallback=".txt,.ini,.log,.docx,.pdf,.zip,.rar,.exe,.7z"),
    }

    if settings["BOT_TOKEN"] is None or settings["CHANNEL_ID"] is None:
        logger.error("BOT_TOKEN и CHANNEL_ID должны быть указаны в config.ini!")
        return {}

    return settings

def save_config(settings, filename=CONFIG_FILE_NAME):
    """Сохраняет настройки в AppData."""

    config_path = get_app_data_path(filename) # получаем путь

    if not check_disk_space(os.path.dirname(config_path)):
        logger.error(f"Недостаточно места на диске для сохранения конфигурации.")
        return

    config = configparser.ConfigParser()
    config["Telegram"] = settings
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        logger.info(f"Настройки сохранены в '{config_path}'")
    except Exception as e:
        logger.error(f"Ошибка записи файла конфигурации '{config_path}': {e}")