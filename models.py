from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

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
        """Установка аватара пользователя"""
        self.avatar_filename = filename
        db.session.commit()
    
    def get_avatar_url(self):
        """Получение URL аватара пользователя"""
        if self.avatar_filename:
            return f"/static/uploads/avatars/{self.avatar_filename}"
        return None

@login_manager.user_loader
def load_user(user_id):
    """Загрузчик пользователя для Flask-Login"""
    return User.query.get(int(user_id))