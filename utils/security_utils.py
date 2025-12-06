"""
Security utilities and helpers
"""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger('flask_auth_app.security')


class PasswordValidator:
    """Валидатор паролей с настраиваемыми правилами."""
    
    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.special_chars = special_chars
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        Валидация пароля.
        
        Returns:
            (is_valid, errors) - True/False и список ошибок
        """
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Пароль должен содержать минимум {self.min_length} символов")
        
        if len(password) > self.max_length:
            errors.append(f"Пароль не должен превышать {self.max_length} символов")
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Пароль должен содержать хотя бы одну строчную букву")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Пароль должен содержать хотя бы одну цифру")
        
        if self.require_special and not re.search(f'[{re.escape(self.special_chars)}]', password):
            errors.append(f"Пароль должен содержать хотя бы один спецсимвол: {self.special_chars}")
        
        return len(errors) == 0, errors
    
    def get_strength(self, password: str) -> dict:
        """
        Оценка надёжности пароля.
        
        Returns:
            {'score': 0-100, 'level': 'weak'|'medium'|'strong'|'very_strong'}
        """
        score = 0
        
        # Длина
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Разнообразие символов
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'\d', password):
            score += 15
        if re.search(f'[{re.escape(self.special_chars)}]', password):
            score += 20
        
        # Уникальность символов
        unique_ratio = len(set(password)) / len(password) if password else 0
        score += int(unique_ratio * 10)
        
        # Определение уровня
        if score < 40:
            level = 'weak'
        elif score < 60:
            level = 'medium'
        elif score < 80:
            level = 'strong'
        else:
            level = 'very_strong'
        
        return {
            'score': min(100, score),
            'level': level
        }


class TokenGenerator:
    """Генератор безопасных токенов."""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Генерация случайного токена."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_hex_token(length: int = 32) -> str:
        """Генерация HEX токена."""
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """Генерация числового кода."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Хеширование токена для хранения."""
        return hashlib.sha256(token.encode()).hexdigest()


class CSRFProtection:
    """CSRF защита."""
    
    TOKEN_LENGTH = 32
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Генерация CSRF токена."""
        return TokenGenerator.generate_hex_token(CSRFProtection.TOKEN_LENGTH)
    
    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """Валидация CSRF токена."""
        return secrets.compare_digest(token, session_token)


class IPValidator:
    """Валидация и работа с IP адресами."""
    
    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """Проверка валидности IPv4."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Проверка, является ли IP приватным."""
        if not IPValidator.is_valid_ipv4(ip):
            return False
        
        parts = [int(p) for p in ip.split('.')]
        
        # 10.0.0.0/8
        if parts[0] == 10:
            return True
        
        # 172.16.0.0/12
        if parts[0] == 172 and 16 <= parts[1] <= 31:
            return True
        
        # 192.168.0.0/16
        if parts[0] == 192 and parts[1] == 168:
            return True
        
        # 127.0.0.0/8 (localhost)
        if parts[0] == 127:
            return True
        
        return False
    
    @staticmethod
    def get_ip_range(ip: str, cidr: int) -> Tuple[Optional[int], Optional[int]]:
        """Получить диапазон IP адресов."""
        # Простая реализация для IPv4
        if not IPValidator.is_valid_ipv4(ip):
            return None, None
        
        parts = [int(p) for p in ip.split('.')]
        ip_int = (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]
        
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        network = ip_int & mask
        broadcast = network | (0xffffffff >> cidr)
        
        return network, broadcast


class RateLimitChecker:
    """Проверка rate limiting."""
    
    def __init__(self):
        self.attempts = {}
    
    def check_limit(
        self,
        identifier: str,
        max_attempts: int,
        time_window: int = 3600
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Проверка лимита попыток.
        
        Args:
            identifier: идентификатор (IP, user_id и т.д.)
            max_attempts: максимальное количество попыток
            time_window: временное окно в секундах
        
        Returns:
            (allowed, reset_time) - разрешён ли запрос и время сброса
        """
        now = datetime.utcnow()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        # Удаляем старые попытки
        cutoff = now - timedelta(seconds=time_window)
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if attempt > cutoff
        ]
        
        # Проверяем лимит
        if len(self.attempts[identifier]) >= max_attempts:
            reset_time = self.attempts[identifier][0] + timedelta(seconds=time_window)
            return False, reset_time
        
        # Добавляем новую попытку
        self.attempts[identifier].append(now)
        return True, None
    
    def reset(self, identifier: str):
        """Сброс счётчика для идентификатора."""
        if identifier in self.attempts:
            del self.attempts[identifier]


class InputSanitizer:
    """Очистка пользовательского ввода."""
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Базовая очистка строки."""
        if not text:
            return ""
        
        # Обрезаем по длине
        text = text[:max_length]
        
        # Удаляем управляющие символы
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Удаляем лишние пробелы
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """Очистка имени пользователя."""
        if not username:
            return ""
        
        # Только буквы, цифры, подчёркивание, дефис
        username = re.sub(r'[^\w\-]', '', username)
        
        # Обрезаем длину
        username = username[:50]
        
        return username.lower()
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Очистка email."""
        if not email:
            return ""
        
        email = email.strip().lower()
        
        # Базовая валидация формата
        if not re.match(r'^[\w\.\-]+@[\w\.\-]+\.\w+$', email):
            return ""
        
        return email[:120]
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Очистка URL."""
        if not url:
            return ""
        
        url = url.strip()
        
        # Разрешаем только http/https
        if not url.startswith(('http://', 'https://')):
            return ""
        
        # Простая валидация
        if not re.match(r'^https?://[\w\.\-]+(:\d+)?(/.*)?$', url):
            return ""
        
        return url[:500]


class SecureHeaders:
    """Генератор заголовков безопасности."""
    
    @staticmethod
    def get_security_headers() -> dict:
        """Получить рекомендуемые заголовки безопасности."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:;",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }


class SessionSecurity:
    """Безопасность сессий."""
    
    @staticmethod
    def generate_session_id() -> str:
        """Генерация безопасного ID сессии."""
        return TokenGenerator.generate_hex_token(32)
    
    @staticmethod
    def validate_session_fingerprint(
        stored_fingerprint: str,
        current_user_agent: str,
        current_ip: str
    ) -> bool:
        """Валидация отпечатка сессии."""
        current_fingerprint = SessionSecurity.create_fingerprint(
            current_user_agent,
            current_ip
        )
        return secrets.compare_digest(stored_fingerprint, current_fingerprint)
    
    @staticmethod
    def create_fingerprint(user_agent: str, ip: str) -> str:
        """Создание отпечатка сессии."""
        data = f"{user_agent}:{ip}"
        return hashlib.sha256(data.encode()).hexdigest()


# Глобальные экземпляры
password_validator = PasswordValidator()
rate_limiter = RateLimitChecker()
