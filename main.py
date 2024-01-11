import telebot
import fitz
import os
import zipfile
from PIL import Image, ImageFile

TOKEN = 'Ваш токен тг'
bot = telebot.TeleBot(TOKEN)

# Увеличение лимита пикселей
Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True


# Проверка директории
def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


# Сжатие изображения и сохранение его как JPEG
def compress_image(image_path, quality=50):
    picture = Image.open(image_path)
    picture_rgb = picture.convert('RGB')
    compressed_path = image_path.replace('.jpg', '_compressed.jpg')
    picture_rgb.save(compressed_path, "JPEG", optimize=True, quality=quality)
    return compressed_path


# Преобразование PDF в изображения
def transformation_to_img(input_file):
    zoom_x = 8
    zoom_y = 8
    rotate = 90
    output_files = []
    mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
    file = os.path.abspath(input_file)
    if file.endswith(".pdf"):
        PDF = fitz.open(file)
        for i, page in enumerate(range(PDF.page_count)):
            pg = PDF[page]
            pix = pg.get_pixmap(matrix=mat, alpha=False)
            output_file = f"./images/Page{i}.jpg"
            pix.save(output_file)
            compressed_file = compress_image(output_file)
            output_files.append(compressed_file)
        PDF.close()
    return output_files


# Создание ZIP-архива
def create_zip_archive(files, zip_name):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))
    return zip_name


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 "Отправьте мне PDF и я преобразую его страницы в изображения, сожму их и отправлю вам архив ZIP.")


# Обработчик загруженных документов
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        chat_id = message.chat.id
        bot.send_message(chat_id, "Ваш PDF получен. Начинаю конвертацию...")

        # Создание директории, если она не существует
        ensure_directory_exists('./images/')
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = f'{message.document.file_name}'
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        output_files = transformation_to_img(src)

        # Создание ZIP-архива
        zip_name = f'./images/{os.path.splitext(src)[0]}.zip'
        create_zip_archive(output_files, zip_name)

        with open(zip_name, 'rb') as zip_file:
            bot.send_document(chat_id, zip_file)

        # Удаление PDF, изображений и ZIP после обработки (опционально)
        os.remove(src)
        for output_file in output_files:
            os.remove(output_file)
        os.remove(zip_name)

    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка: {e}')


bot.polling()
