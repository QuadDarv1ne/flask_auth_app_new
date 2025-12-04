"""
Кастомные валидаторы для форм
"""
import re
from wtforms.validators import ValidationError


class PasswordStrength:
    """
    Валидатор для проверки надежности пароля
    """
    def __init__(self, require_uppercase=True, require_lowercase=True, 
                 require_digit=True, require_special=False, 
                 message='Пароль не соответствует требованиям безопасности'):
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.message = message
    
    def __call__(self, form, field):
        password = field.data
        errors = []
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append('одну заглавную букву')
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append('одну строчную букву')
        
        if self.require_digit and not re.search(r'\d', password):
            errors.append('одну цифру')
        
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('один специальный символ')
        
        if errors:
            message = f'Пароль должен содержать как минимум {", ".join(errors)}'
            raise ValidationError(message)


class NoCommonPasswords:
    """
    Валидатор для проверки пароля на список популярных паролей
    """
    COMMON_PASSWORDS = {
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', '1234567', 'letmein', 'trustno1', 'dragon',
        'baseball', '111111', 'iloveyou', 'master', 'sunshine',
        'ashley', 'bailey', 'passw0rd', 'shadow', '123123',
        '654321', 'superman', 'qazwsx', 'michael', 'football'
    }
    
    def __init__(self, message='Этот пароль слишком распространен. Выберите более надежный пароль.'):
        self.message = message
    
    def __call__(self, form, field):
        if field.data.lower() in self.COMMON_PASSWORDS:
            raise ValidationError(self.message)


class UsernameValidator:
    """
    Валидатор для проверки имени пользователя
    Допускает только буквы, цифры, подчеркивание и дефис
    """
    def __init__(self, message='Имя пользователя может содержать только буквы, цифры, подчеркивание и дефис'):
        self.message = message
    
    def __call__(self, form, field):
        username = field.data
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(self.message)
