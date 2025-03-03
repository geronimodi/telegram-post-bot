import asyncio
import os
import logging

import telegram
from telegram.ext import Application, AIORateLimiter
from telegram.error import TelegramError

from utils import generate_phrase_with_emoji, check_disk_space, load_phrases
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG # Добавить!

# Логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_telegram_post(bot_token, channel_id, file_paths, gui_instance):
    """Отправляет пост в Telegram."""
    app = Application.builder().token(bot_token).rate_limiter(AIORateLimiter()).build()

    try:
        phrases = load_phrases()  # Загружаем фразы
        text = generate_phrase_with_emoji(phrases) + "\n\n" + gui_instance.settings.get("DEFAULT_HASHTAGS", "")

        media_group = []
        total_files = len(file_paths) # Общее количество файлов
        for i, file_path in enumerate(file_paths):  # Добавляем индекс файла
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # Проверка на белый/черный список (дублируем логику, т.к. вызываем из другого модуля)
            whitelist = [e.strip().lower() for e in gui_instance.settings.get("WHITELIST_EXTENSIONS", ".jpg,.jpeg,.png,.gif,.mp4").split(",")]
            blacklist = [e.strip().lower() for e in gui_instance.settings.get("BLACKLIST_EXTENSIONS", "").split(",")]

            if (whitelist and ext not in whitelist) or (blacklist and ext in blacklist):
                gui_instance.log_output.append(f"⚠️ Файл {file_path} пропущен (фильтр расширений).")
                continue

            try:
                if ext in (".jpg", ".jpeg", ".png"):
                    with open(file_path, "rb") as file:
                        media_group.append(telegram.InputMediaPhoto(file))
                elif ext == ".mp4":
                    with open(file_path, "rb") as file:
                        media_group.append(telegram.InputMediaVideo(file))
                else:
                    gui_instance.log_output.append(f"⚠️ Неподдерживаемый тип файла: {file_path}. Пропускаем.")
                    continue
            except FileNotFoundError:
                gui_instance.log_output.append(f"⚠️ Файл не найден: {file_path}. Пропускаем.")
                continue
            except OSError as e:
                gui_instance.log_output.append(f"⚠️ Ошибка открытия файла: {file_path}. {e}. Пропускаем.")
                continue

            # Обновляем прогресс-бар *после* добавления файла в media_group
            progress_value = int(((i + 1) / total_files) * 100)  # +1, т.к. индексы начинаются с 0
            # используем QMetaObject.invokeMethod, так как мы в другом потоке
            QMetaObject.invokeMethod(gui_instance.progress_bar, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(int, progress_value))

        if not media_group:
            gui_instance.log_output.append("❌ Нет медиафайлов для отправки.")
            return

        max_attempts = 3  # Максимальное количество попыток отправки
        attempt = 0
        success = False

        while attempt < max_attempts and not success:
            attempt += 1
            try:
                if len(media_group) > 10:
                    gui_instance.log_output.append("⚠️ Группа содержит более 10 элементов. Разбиваем на части.")
                    for i in range(0, len(media_group), 10):
                        chunk = media_group[i:i + 10]
                        #  Увеличиваем таймауты:
                        await app.bot.send_media_group(channel_id, chunk, caption=text if i == 0 else None, read_timeout=60, write_timeout=60, connect_timeout=60)
                        QMetaObject.invokeMethod(
                            gui_instance.log_output, "append", Qt.ConnectionType.QueuedConnection,
                            Q_ARG(str, f"✅ Отправлена часть {i // 10 + 1} поста.")
                        )
                        await asyncio.sleep(30)  # Задержка между частями
                else:
                    #  Увеличиваем таймауты:
                    await app.bot.send_media_group(channel_id, media_group, caption=text, read_timeout=60, write_timeout=60, connect_timeout=60)
                    QMetaObject.invokeMethod(
                        gui_instance.log_output, "append", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, "✅ Пост успешно отправлен.")
                    )

                success = True  # Успешно отправили

            except telegram.error.TimedOut:
                gui_instance.log_output.append(f"❌ Ошибка отправки: Таймаут. Повторная попытка {attempt}/{max_attempts}.")
                await asyncio.sleep(5)  # Ждем перед повторной попыткой
            except TelegramError as e:
                gui_instance.log_output.append(f"❌ Ошибка отправки: {e}")
                break  # Прерываем цикл при других ошибках Telegram API

        if success:
            # Удаляем файлы *только* если отправка была успешной
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        await asyncio.to_thread(os.remove, file_path)
                        QMetaObject.invokeMethod(
                            gui_instance.log_output, "append", Qt.ConnectionType.QueuedConnection,
                            Q_ARG(str, f"🗑️ Файл {file_path} удалён.")
                        )
                    else:
                        QMetaObject.invokeMethod(
                            gui_instance.log_output, "append", Qt.ConnectionType.QueuedConnection,
                            Q_ARG(str, f"⚠️ Файл {file_path} уже удалён.")
                        )
                except Exception as e:
                    QMetaObject.invokeMethod(
                        gui_instance.log_output, "append", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, f"❌ Ошибка удаления файла: {e}")
                    )

            # Сбрасываем прогресс-бар после успешной отправки
            QMetaObject.invokeMethod(gui_instance.progress_bar, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 0))

        else:
            gui_instance.log_output.append("❌ Пост не был отправлен после нескольких попыток. Файлы сохранены.")

    except Exception as e:  # Общий Exception в конце
        gui_instance.log_output.append(f"❌ Критическая ошибка в send_post: {e}")
        #  Сбрасываем прогресс-бар в случае критической ошибки:
        QMetaObject.invokeMethod(gui_instance.progress_bar, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 0))

async def start_telegram_bot(bot_token, gui_instance):
    """Запускает бота."""
    app = Application.builder().token(bot_token).rate_limiter(AIORateLimiter()).build()
    try:
        me = await app.bot.get_me()
        gui_instance.log_output.append(f"✅ Бот запущен.  Имя бота: {me.username}")
        gui_instance.set_bot_running(True)  # Устанавливаем статус бота

    except TelegramError as e:
        gui_instance.log_output.append(f"❌ Ошибка при проверке токена: {e}")
        gui_instance.show_settings_dialog()

async def stop_telegram_bot(gui_instance):
    """Останавливает бота"""
    gui_instance.set_bot_running(False)
    gui_instance.log_output.append("⛔ Бот остановлен")