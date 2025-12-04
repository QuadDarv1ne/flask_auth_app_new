"""
Тесты для моделей базы данных
"""
import pytest
from models import User
from app import db


class TestUserModel:
    """Тесты для модели User"""
    
    def test_user_creation(self, app):
        """Тест создания пользователя"""
        user = User(username='newuser', email='new@example.com')
        user.set_password('SecurePass123')
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.password_hash is not None
        assert user.created_at is not None
    
    def test_password_hashing(self, app):
        """Тест хеширования пароля"""
        user = User(username='hashtest', email='hash@example.com')
        password = 'MyPassword123'
        user.set_password(password)
        
        assert user.password_hash != password
        assert user.check_password(password)
        assert not user.check_password('WrongPassword')
    
    def test_unique_username(self, app, test_user):
        """Тест уникальности имени пользователя"""
        duplicate_user = User(username='testuser', email='other@example.com')
        duplicate_user.set_password('Pass123')
        
        db.session.add(duplicate_user)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_unique_email(self, app, test_user):
        """Тест уникальности email"""
        duplicate_user = User(username='otheruser', email='test@example.com')
        duplicate_user.set_password('Pass123')
        
        db.session.add(duplicate_user)
        
        with pytest.raises(Exception):
            db.session.commit()
    
    def test_update_last_login(self, app, test_user):
        """Тест обновления времени последнего входа"""
        assert test_user.last_login is None
        
        test_user.update_last_login()
        
        assert test_user.last_login is not None
    
    def test_user_representation(self, app, test_user):
        """Тест строкового представления пользователя"""
        assert repr(test_user) == '<User testuser>'
