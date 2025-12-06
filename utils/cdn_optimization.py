"""
Content Delivery Optimization - Gzip, Brotli, WebP support
"""
import gzip
import io
from functools import wraps
from flask import request, current_app, make_response
import logging

logger = logging.getLogger('flask_auth_app.cdn')


class ContentCompression:
    """Управление сжатием контента"""
    
    SUPPORTED_ENCODINGS = ['gzip', 'deflate', 'br', 'identity']
    
    @staticmethod
    def get_best_encoding(accept_encoding: str) -> str:
        """Выбрать лучший формат сжатия"""
        encodings = [
            enc.split(';')[0].strip()
            for enc in accept_encoding.split(',')
        ]
        
        # Приоритет: brotli > gzip > deflate > none
        if 'br' in encodings:
            return 'br'
        elif 'gzip' in encodings:
            return 'gzip'
        elif 'deflate' in encodings:
            return 'deflate'
        else:
            return 'identity'
    
    @staticmethod
    def compress_gzip(data: bytes) -> bytes:
        """Сжатие Gzip"""
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            f.write(data)
        return buf.getvalue()
    
    @staticmethod
    def should_compress(response_size: int, content_type: str) -> bool:
        """Проверить, стоит ли сжимать контент"""
        # Не сжимаем маленькие файлы
        if response_size < 500:
            return False
        
        # Сжимаем текстовый контент
        compressible_types = [
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'application/xml',
            'image/svg+xml'
        ]
        
        return any(ct in content_type for ct in compressible_types)


class ImageOptimization:
    """Оптимизация изображений"""
    
    WEBP_THRESHOLD = 100 * 1024  # 100KB - порог для конвертации в WebP
    
    @staticmethod
    def get_optimal_image_format(accept_header: str) -> str:
        """Получить оптимальный формат изображения"""
        if 'image/webp' in accept_header:
            return 'webp'
        return 'jpeg'
    
    @staticmethod
    def should_convert_to_webp(size: int) -> bool:
        """Стоит ли конвертировать в WebP"""
        return size > ImageOptimization.WEBP_THRESHOLD
    
    @staticmethod
    def get_responsive_image_url(base_url: str, width: int) -> str:
        """Получить URL для responsive image"""
        return f"{base_url}?w={width}&q=80"
    
    @staticmethod
    def get_srcset(base_url: str, widths: list = None) -> str:
        """Генерировать srcset для изображения"""
        if widths is None:
            widths = [320, 640, 1024, 1920]
        
        srcset_parts = []
        for width in widths:
            url = ImageOptimization.get_responsive_image_url(base_url, width)
            srcset_parts.append(f"{url} {width}w")
        
        return ', '.join(srcset_parts)


class CDNHeaders:
    """Генератор оптимальных CDN заголовков"""
    
    @staticmethod
    def get_cache_headers(
        content_type: str,
        max_age: int = 3600,
        public: bool = True,
        immutable: bool = False
    ) -> dict:
        """Генерировать кэш-заголовки"""
        cache_control_parts = []
        
        if public:
            cache_control_parts.append('public')
        else:
            cache_control_parts.append('private')
        
        cache_control_parts.append(f'max-age={max_age}')
        
        if immutable:
            cache_control_parts.append('immutable')
        else:
            cache_control_parts.append('must-revalidate')
        
        return {
            'Cache-Control': ', '.join(cache_control_parts),
            'Pragma': 'cache',
            'Expires': CDNHeaders._get_expires_header(max_age)
        }
    
    @staticmethod
    def _get_expires_header(max_age: int) -> str:
        """Генерировать Expires заголовок"""
        from datetime import datetime, timedelta
        expires = datetime.utcnow() + timedelta(seconds=max_age)
        return expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    @staticmethod
    def get_etag_headers(content: bytes) -> dict:
        """Генерировать ETag заголовки"""
        import hashlib
        etag = hashlib.md5(content).hexdigest()
        return {
            'ETag': f'"{etag}"',
            'Vary': 'Accept-Encoding'
        }
    
    @staticmethod
    def get_cdn_headers(
        content_type: str,
        is_static: bool = False
    ) -> dict:
        """Комбинированные оптимальные заголовки для CDN"""
        if is_static:
            # Статические файлы кэшируются на год
            cache_headers = CDNHeaders.get_cache_headers(
                content_type,
                max_age=31536000,
                immutable=True
            )
        else:
            # Динамический контент кэшируется на час
            cache_headers = CDNHeaders.get_cache_headers(
                content_type,
                max_age=3600,
                public=False
            )
        
        headers = {
            **cache_headers,
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'Vary': 'Accept-Encoding, Accept'
        }
        
        # Дополнительные заголовки для SVG
        if 'svg' in content_type:
            headers['X-XSS-Protection'] = '1; mode=block'
        
        return headers


def optimize_response(f):
    """Декоратор для оптимизации ответа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, make_response
        
        response = f(*args, **kwargs)
        
        # Если это не Response объект, пропускаем
        if not hasattr(response, 'status_code'):
            return response
        
        # Получаем принятые кодировки
        accept_encoding = request.headers.get('Accept-Encoding', '')
        content_type = response.headers.get('Content-Type', '')
        
        # Добавляем CDN заголовки
        is_static = '/static/' in request.path
        cdn_headers = CDNHeaders.get_cdn_headers(content_type, is_static)
        
        for header, value in cdn_headers.items():
            response.headers[header] = value
        
        # Сжимаем контент если нужно
        if ContentCompression.should_compress(
            len(response.data),
            content_type
        ):
            encoding = ContentCompression.get_best_encoding(accept_encoding)
            
            if encoding == 'gzip':
                compressed = ContentCompression.compress_gzip(response.data)
                response.data = compressed
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed)
        
        return response
    
    return decorated_function


class CDNOptimizer:
    """Интеграция с CDN провайдерами"""
    
    def __init__(self, cdn_url: str = None):
        self.cdn_url = cdn_url
    
    def get_asset_url(self, asset_path: str) -> str:
        """Получить URL для ассета из CDN"""
        if not self.cdn_url:
            return asset_path
        
        # Удаляем /static/ если есть
        clean_path = asset_path.replace('/static/', '')
        return f"{self.cdn_url}/{clean_path}"
    
    def get_image_url(
        self,
        image_path: str,
        width: int = None,
        quality: int = 80
    ) -> str:
        """Получить URL для изображения с параметрами"""
        url = self.get_asset_url(image_path)
        
        params = []
        if width:
            params.append(f"w={width}")
        if quality:
            params.append(f"q={quality}")
        
        if params:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}{'&'.join(params)}"
        
        return url
