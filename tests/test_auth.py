"""
Тесты для маршрутов аутентификации
"""
import pytest
from models import User
from app import db


class TestAuthRoutes:
    """Тесты для маршрутов auth"""
    
    def test_login_page_loads(self, client):
        """Тест загрузки страницы входа"""
        response = client.get('/login')
        assert response.status_code == 200
        assert 'Вход' in response.data.decode('utf-8')
    
    def test_register_page_loads(self, client):
        """Тест загрузки страницы регистрации"""
        response = client.get('/register')
        assert response.status_code == 200
        assert 'регистрация' in response.data.decode('utf-8').lower()
    
    def test_successful_registration(self, client):
        """Тест успешной регистрации"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123',
            'password2': 'SecurePass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Проверяем, что пользователь создан
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'
    
    def test_registration_with_existing_username(self, client, test_user):
        """Тест регистрации с существующим именем пользователя"""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'different@example.com',
            'password': 'SecurePass123',
            'password2': 'SecurePass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'занято' in response.data.decode('utf-8').lower()
    
    def test_registration_password_mismatch(self, client):
        """Тест регистрации с несовпадающими паролями"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123',
            'password2': 'DifferentPass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'совпадать' in response.data.decode('utf-8').lower()
    
    def test_successful_login(self, client, test_user):
        """Тест успешного входа"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'TestPass123',
            'remember_me': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_with_wrong_password(self, client, test_user):
        """Тест входа с неправильным паролем"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'неверн' in response.data.decode('utf-8').lower()
    
    def test_login_with_nonexistent_user(self, client):
        """Тест входа с несуществующим пользователем"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'AnyPassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'неверн' in response.data.decode('utf-8').lower()
    
    def test_logout(self, authenticated_client):
        """Тест выхода из системы"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Проверяем, что доступ к защищенной странице закрыт
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 302  # Редирект на страницу входа
