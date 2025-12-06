"""
Конфигурация для pytest
"""
import pytest
from app import create_app, db
from models import User
from config import Config


class TestConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    
    # Disable Redis for testing
    REDIS_URL = 'redis://localhost:6379/0'
    CACHE_TYPE = 'null'


@pytest.fixture
def app():
    """Создание приложения для тестов"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Тестовый клиент Flask"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Тестовый CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Создание тестового пользователя"""
    user = User(username='testuser', email='test@example.com')
    user.set_password('TestPass123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Аутентифицированный клиент"""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'TestPass123'
    }, follow_redirects=True)
    return client
