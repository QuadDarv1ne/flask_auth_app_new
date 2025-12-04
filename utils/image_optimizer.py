"""
Утилиты для оптимизации изображений
"""

import os
from PIL import Image
import io
import base64
from flask import current_app


def optimize_image(image_path, quality=85, max_width=1920, max_height=1080):
    """
    Оптимизация изображения для веба
    
    Args:
        image_path (str): Путь к изображению
        quality (int): Качество JPEG (по умолчанию 85)
        max_width (int): Максимальная ширина (по умолчанию 1920)
        max_height (int): Максимальная высота (по умолчанию 1080)
    
    Returns:
        bytes: Оптимизированное изображение
    """
    try:
        # Открываем изображение
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                # Для изображений с прозрачностью создаем белый фон
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Изменяем размер если изображение слишком большое
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Сохраняем в буфер с оптимизацией
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
    except Exception as e:
        current_app.logger.error(f"Ошибка оптимизации изображения {image_path}: {e}")
        return None


def create_responsive_images(image_path, sizes=[300, 600, 1200]):
    """
    Создание набора изображений разных размеров для адаптивного дизайна
    
    Args:
        image_path (str): Путь к исходному изображению
        sizes (list): Список размеров для создания вариантов
    
    Returns:
        dict: Словарь с путями к изображениям разных размеров
    """
    responsive_images = {}
    
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Создаем изображения разных размеров
            for size in sizes:
                if img.width > size:
                    # Рассчитываем пропорциональную высоту
                    ratio = size / float(img.width)
                    height = int(float(img.height) * ratio)
                    
                    resized_img = img.copy()
                    resized_img.thumbnail((size, height), Image.Resampling.LANCZOS)
                    
                    # Сохраняем оптимизированное изображение
                    buffer = io.BytesIO()
                    resized_img.save(buffer, format='JPEG', quality=80, optimize=True)
                    
                    # Генерируем имя файла
                    filename = os.path.basename(image_path)
                    name, ext = os.path.splitext(filename)
                    new_filename = f"{name}_{size}w.jpg"
                    new_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'responsive', new_filename)
                    
                    # Создаем папку если нужно
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    
                    # Сохраняем файл
                    with open(new_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    
                    responsive_images[size] = new_path
    except Exception as e:
        current_app.logger.error(f"Ошибка создания адаптивных изображений {image_path}: {e}")
    
    return responsive_images


def get_image_base64(image_path):
    """
    Получение base64 представления изображения для inline использования
    
    Args:
        image_path (str): Путь к изображению
    
    Returns:
        str: Base64 строка изображения
    """
    try:
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        current_app.logger.error(f"Ошибка кодирования изображения в base64 {image_path}: {e}")
        return None


def compress_and_resize_avatar(image_data, max_size=200):
    """
    Сжатие и изменение размера аватара пользователя
    
    Args:
        image_data (bytes): Данные изображения
        max_size (int): Максимальный размер стороны (по умолчанию 200px)
    
    Returns:
        bytes: Сжатое изображение
    """
    try:
        # Открываем изображение из байтов
        img = Image.open(io.BytesIO(image_data))
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Изменяем размер до квадратного
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Если изображение не квадратное, делаем его квадратным
        if img.width != img.height:
            size = min(img.width, img.height)
            left = (img.width - size) // 2
            top = (img.height - size) // 2
            right = left + size
            bottom = top + size
            img = img.crop((left, top, right, bottom))
        
        # Сохраняем с оптимизацией
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        return buffer.getvalue()
    except Exception as e:
        current_app.logger.error(f"Ошибка сжатия аватара: {e}")
        return None