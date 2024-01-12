import telebot  # Импорт библиотеки для работы с Telegram ботом
import fitz  # Импорт библиотеки PyMuPDF для работы с PDF
import os  # Импорт модуля для работы с операционной системой
import zipfile  # Импорт модуля для работы с ZIP-архивами
from PIL import Image, ImageFile  # Импорт модулей для работы с изображениями

# Токен вашего бота в Telegram
TOKEN = 'Ваш токен тг'
bot = telebot.TeleBot(TOKEN)  # Инициализация бота с вашим токеном

# Увеличение лимита пикселей для обработки больших изображений и поддержка усеченных изображений
Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True


# Функция для проверки существования директории и ее создания при отсутствии
def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Функция для сжатия изображения и сохранения его в формате JPEG
def compress_image(image_path, quality=50):
    picture = Image.open(image_path)  # Открытие изображения
    picture_rgb = picture.convert('RGB')  # Конвертация в RGB
    compressed_path = image_path.replace('.jpg', '_compressed.jpg')  # Путь к сжатому изображению
    picture_rgb.save(compressed_path, "JPEG", optimize=True, quality=quality)  # Сохранение сжатого изображения
    return compressed_path


# Функция для преобразования страниц PDF в отдельные изображения
def transformation_to_img(input_file):
    zoom_x = 8  # Масштабирование по оси X
    zoom_y = 8  # Масштабирование по оси Y
    rotate = 90  # Угол поворота страницы
    output_files = []  # Список для сохранения путей к обработанным файлам
    mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)  # Создание матрицы трансформации
    file = os.path.abspath(input_file)  # Получение абсолютного пути файла
    if file.endswith(".pdf"):
        PDF = fitz.open(file)  # Открытие PDF файла
        for i, page in enumerate(range(PDF.page_count)):  # Обработка каждой страницы
            pg = PDF[page]
            pix = pg.get_pixmap(matrix=mat, alpha=False)
            output_file = f"./images/Page{i}.jpg"
            pix.save(output_file)  # Сохранение страницы в виде изображения
            compressed_file = compress_image(output_file)  # Сжатие изображения
            output_files.append(compressed_file)
        PDF.close()
    return output_files


# Функция для создания ZIP-архива из списка файлов
def create_zip_archive(files, zip_name):
    with zipfile.ZipFile(zip_name, 'w') as zipf:  # Создание нового ZIP-архива
        for file in files:
            zipf.write(file, os.path.basename(file))  # Добавление файлов в архив
    return zip_name


# Обработчик команды /start для Telegram бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Отправьте мне PDF и я преобразую его страницы в изображения, сожму их и отправлю вам архив ZIP.")


# Обработчик для получения документов от пользователей
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        chat_id = message.chat.id  # Получение ID чата
        bot.send_message(chat_id, "Ваш PDF получен. Начинаю конвертацию...")  # Отправка сообщения о начале конвертации

        ensure_directory_exists('./images/')  # Проверка и создание необходимой директории
        file_info = bot.get_file(message.document.file_id)  # Получение информации о файле
        downloaded_file = bot.download_file(file_info.file_path)  # Загрузка файла

        src = f'{message.document.file_name}'  # Имя загруженного файла
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)  # Сохранение файла на диск

        output_files = transformation_to_img(src)  # Преобразование PDF в изображения

        zip_name = f'./images/{os.path.splitext(src)[0]}.zip'  # Имя ZIP-архива
        create_zip_archive(output_files, zip_name)  # Создание ZIP-архива

        with open(zip_name, 'rb') as zip_file:
            bot.send_document(chat_id, zip_file)  # Отправка ZIP-архива пользователю

        # Опционально: удаление PDF, изображений и ZIP после обработки
        os.remove(src)
        for output_file in output_files:
            os.remove(output_file)
        os.remove(zip_name)

    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка: {e}')  # Обработка исключений


bot.polling()  # Запуск бота
