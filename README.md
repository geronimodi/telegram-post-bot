# Telegram Post Bot
Автоматический бот для публикации изображений и видео в Telegram-канал.

## Скриншоты

<div style="display: flex; flex-direction: row; justify-content: flex-start; width: 100%; gap: 2%;">
  <div style="text-align: center; width: 20%;">
    <p>Главное окно</p>
    <a href="https://github.com/user-attachments/assets/4b3edd24-be70-46bc-b211-913ede033f7d">
        <img src="https://github.com/user-attachments/assets/c8c068dd-d0b0-4323-aa7e-ebd9d134a9fa" width="10%" alt="Главное окно">
    </a>
  </div>
  <div style="text-align: center; width: 20%;">
    <p>Настройки</p>
    <a href="https://github.com/user-attachments/assets/4b3edd24-be70-46bc-b211-913ede033f7d">
        <img src="https://github.com/user-attachments/assets/f38db6bd-d142-4f73-bf6b-b2c3bf0e67a6" width="10%" alt="Настройки">
    </a>
  </div>
  <div style="text-align: center; width: 20%;">
    <p>Окно рандомайзера фраз</p>
    <a href="https://github.com/user-attachments/assets/4b3edd24-be70-46bc-b211-913ede033f7d">
        <img src="https://github.com/user-attachments/assets/4b3edd24-be70-46bc-b211-913ede033f7d" width="10%" alt="Окно рандомайзера фраз">
    </a>
  </div>
</div>

## Описание

Этот бот позволяет автоматизировать публикацию контента (изображений и видео) в Telegram-канал.  Он сканирует указанную папку на наличие новых файлов, формирует из них посты и отправляет их в канал с заданным интервалом.  Поддерживает настройку списка разрешенных и запрещенных расширений файлов, добавление подписей к постам, а также редактирование списка фраз, используемых в подписях.  Есть возможность сворачивания в трей.

## Установка

1.  **Установите Python:** Убедитесь, что у вас установлен Python 3.7 или новее.  Скачать Python можно с официального сайта: [https://www.python.org/downloads/](https://www.python.org/downloads/)

2.  **Установите зависимости:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Создайте файл конфигурации:**

    *   Создайте файл `config.ini` в той же папке, где находится `main.py`.
    *   Добавьте в `config.ini` следующие строки, заменив значения на свои собственные:

        ```ini
        [Telegram]
        BOT_TOKEN = YOUR_BOT_TOKEN
        CHANNEL_ID = YOUR_CHANNEL_ID
        DEFAULT_HASHTAGS = #your #default #hashtags
        FOLDER_PATH = C:\path\to\your\folder
        MIN_DELAY_MINUTES = 10
        MAX_DELAY_MINUTES = 120
        WHITELIST_EXTENSIONS = .jpg,.jpeg,.png,.gif,.mp4,.webm,.webp
        BLACKLIST_EXTENSIONS = .txt,.ini,.log,.docx,.pdf,.zip,.rar,.exe,.7z
        ```
    * Вместо `YOUR_BOT_TOKEN` подставь свой токен бота
    * Вместо `YOUR_CHANNEL_ID` подставь ID своего канала (с минусом)

4. **Создайте файл phrases.txt**
    *  Создайте файл `phrases.txt`, если хотите, чтобы к посту добавлялась рандомная фраза
    *  Внесите в файл `phrases.txt` фразы, каждая фраза на новой строке.

## Настройка

*   **BOT_TOKEN:** Токен вашего Telegram-бота. Получите его у `@BotFather`.
*   **CHANNEL_ID:** ID вашего Telegram-канала (например, `-1001234567890`).  Убедитесь, что бот добавлен в администраторы канала с правом публикации сообщений. *Важно:* ID канала должен начинаться с `-100` (для супергрупп/каналов)
*   **DEFAULT_HASHTAGS:** Хэштеги, которые будут добавляться к каждому посту (например, `#photo #art`).  Можно оставить пустым.
*   **FOLDER_PATH:** Путь к папке, из которой бот будет брать файлы для публикации (например, `C:\Users\YourName\Pictures\TelegramBot`).
*   **MIN_DELAY_MINUTES:** Минимальная задержка между постами в минутах (случайное значение между MIN и MAX).
*   **MAX_DELAY_MINUTES:** Максимальная задержка между постами в минутах.
*   **WHITELIST_EXTENSIONS:** Список разрешенных расширений файлов (через запятую, с точкой, например, `.jpg,.jpeg,.png`).
*   **BLACKLIST_EXTENSIONS:** Список запрещенных расширений файлов (через запятую, с точкой, например, `.txt,.exe`).

## Использование

1.  **Запустите** файл `main.py`:

    ```bash
    python main.py
    ```
    Или, если вы создали `.exe`:
      Запустите `TelegramBot.exe`.

2.  **Настройте** бота через графический интерфейс (GUI):
    *   При первом запуске откроется окно настроек.  Введите необходимые данные (токен, ID канала и т.д.) и нажмите "Сохранить".
    *   В дальнейшем настройки можно изменить, нажав кнопку "Настройки" в главном окне бота.
    *  Выберите папку с помощью кнопки "Выбрать папку".
    *   Добавьте/измените/удалите фразы, используемые в подписях, нажав кнопку "Редактировать фразы".

3.  **Запустите** бота, нажав кнопку "Запустить бота".

4.  **Остановите** бота, нажав кнопку "Остановить бота".

5. **Отправка вне очереди:** Нажмите кнопку "Отправить сейчас".

6. **Сворачивание в трей.** Сверните окно, и приложение продолжит работу в трее.

**Для выхода** из приложения воспользуйтесь иконкой в трее.

## Сборка в .exe (необязательно)

Вы можете создать исполняемый файл `.exe`, чтобы запускать бота без необходимости установки Python и зависимостей.  Для этого используется PyInstaller:

1.  **Установите PyInstaller:**

    ```bash
    pip install pyinstaller
    ```

2.  **Соберите проект:**

    ```bash
    pyinstaller --onefile --noconsole --icon=icons/app_icon.ico --add-data "icons;icons" --add-data "config.ini;." --add-data "phrases.txt;." --name "TelegramBot" main.py
    ```

    *   `--onefile`:  Создать один `.exe` файл.
    *   `--noconsole`:  Скрыть консольное окно.
    *   `--icon`:  Установить иконку для `.exe` (замените `icons/app_icon.ico` на путь к вашей иконке).
    *   `--add-data`:  Добавить файлы и папки, необходимые для работы бота (иконки, `config.ini` и `phrases.txt`).
    *    `--name`: Название `.exe` файла.
    *   `main.py`:  Главный файл вашего проекта.

    Исполняемый файл будет создан в папке `dist`.

## Лицензия

[MIT License]

## Автор

Слепов Максим Алексеевич

## Благодарности

*   [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
*   [PyQt6](https://riverbankcomputing.com/software/pyqt/)
---
