"""
Тесты для основных маршрутов
"""
import pytest


class TestMainRoutes:
    """Тесты для маршрутов main"""
    
    def test_index_page_loads(self, client):
        """Тест загрузки главной страницы"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<title>' in response.data
    
    def test_dashboard_requires_login(self, client):
        """Тест что dashboard требует авторизации"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Редирект
    
    def test_dashboard_with_authenticated_user(self, authenticated_client):
        """Тест доступа к dashboard авторизованным пользователем"""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        assert b'testuser' in response.data
    
    def test_profile_requires_login(self, client):
        """Тест что profile требует авторизации"""
        response = client.get('/profile')
        assert response.status_code == 302  # Редирект
    
    def test_profile_with_authenticated_user(self, authenticated_client):
        """Тест доступа к profile авторизованным пользователем"""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
    
    def test_update_profile(self, authenticated_client, test_user):
        """Тест обновления профиля"""
        response = authenticated_client.post('/profile', data={
            'username': 'updateduser',
            'email': 'updated@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_change_password(self, authenticated_client, test_user):
        """Тест изменения пароля"""
        response = authenticated_client.post('/change-password', data={
            'current_password': 'TestPass123',
            'new_password': 'NewSecurePass123',
            'confirm_password': 'NewSecurePass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_change_password_wrong_current(self, authenticated_client):
        """Тест смены пароля с неправильным текущим паролем"""
        response = authenticated_client.post('/change-password', data={
            'current_password': 'WrongPassword123',
            'new_password': 'NewSecurePass123',
            'confirm_password': 'NewSecurePass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert 'неверн' in response.data.decode('utf-8').lower()


class TestErrorHandlers:
    """Тесты для обработчиков ошибок"""
    
    def test_404_error(self, client):
        """Тест обработки ошибки 404"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
