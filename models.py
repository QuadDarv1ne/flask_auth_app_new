from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
import pyotp
import base64
import os

class User(UserMixin, db.Model):
    """Модель пользователя для системы аутентификации"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    # Added fields for admin_required and check_confirmed decorators
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_confirm_token = db.Column(db.String(100), unique=True, nullable=True)
    # Avatar field
    avatar_filename = db.Column(db.String(255), nullable=True)
    # 2FA fields
    totp_secret = db.Column(db.String(32), nullable=True)
    is_2fa_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Хеширование пароля при установке"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Обновление времени последнего входа"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()
    
    def generate_email_confirm_token(self):
        """Генерация токена для подтверждения email"""
        import secrets
        self.email_confirm_token = secrets.token_urlsafe(32)
        return self.email_confirm_token
    
    def confirm_email(self):
        """Подтверждение email адреса"""
        self.email_confirmed = True
        self.email_confirm_token = None
        db.session.commit()
    
    def set_avatar(self, filename):
        """Установка аватара пользователя с оптимизацией"""
        self.avatar_filename = filename
        db.session.commit()
        
        # Автоматическая оптимизация аватара если файл существует
        if filename:
            from utils.image_optimizer import optimize_image, WEBP_SUPPORTED
            from flask import current_app
            import os
            
            avatar_path = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars', filename)
            if os.path.exists(avatar_path):
                # Используем WebP если поддерживается
                format_type = 'WEBP' if WEBP_SUPPORTED else 'JPEG'
                optimized_data = optimize_image(avatar_path, quality=85, max_width=200, max_height=200, format=format_type)
                if optimized_data:
                    # Если используется WebP, меняем расширение файла
                    if format_type == 'WEBP':
                        name, ext = os.path.splitext(filename)
                        webp_filename = f"{name}.webp"
                        webp_path = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars', webp_filename)
                        with open(webp_path, 'wb') as f:
                            f.write(optimized_data)
                        # Обновляем имя файла в базе данных
                        self.avatar_filename = webp_filename
                        db.session.commit()
                    else:
                        with open(avatar_path, 'wb') as f:
                            f.write(optimized_data)
    
    def get_avatar_url(self):
        """Получение URL аватара пользователя"""
        if self.avatar_filename:
            return f"/static/uploads/avatars/{self.avatar_filename}"
        return None
    
    def get_avatar_url_with_fallback(self):
        """Получение URL аватара с фолбэком для WebP"""
        if self.avatar_filename:
            avatar_url = f"/static/uploads/avatars/{self.avatar_filename}"
            # Если это WebP файл, добавляем фолбэк для старых браузеров
            if self.avatar_filename.endswith('.webp'):
                # Для современных браузеров поддерживается WebP
                return avatar_url
            return avatar_url
        return None
    
    def enable_2fa(self):
        """Включение двухфакторной аутентификации"""
        if not self.totp_secret:
            # Generate a random secret for TOTP
            self.totp_secret = base64.b32encode(os.urandom(20)).decode('utf-8')
        self.is_2fa_enabled = True
        db.session.commit()
        return self.totp_secret
    
    def disable_2fa(self):
        """Отключение двухфакторной аутентификации"""
        self.totp_secret = None
        self.is_2fa_enabled = False
        db.session.commit()
    
    def verify_totp(self, token):
        """Проверка TOTP токена"""
        if not self.totp_secret or not self.is_2fa_enabled:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def get_totp_uri(self):
        """Получение URI для настройки 2FA в приложении"""
        if not self.totp_secret:
            return None
        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(self.username, issuer_name="Flask Auth App")

@login_manager.user_loader
def load_user(user_id):
    """Загрузчик пользователя для Flask-Login"""
    return User.query.get(int(user_id))