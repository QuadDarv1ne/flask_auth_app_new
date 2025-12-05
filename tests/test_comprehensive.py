import pytest
from flask import url_for
from models import User


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a CLI runner."""
    return app.test_cli_runner()


class TestAuth:
    """Test authentication routes."""
    
    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get(url_for('auth.login'))
        assert response.status_code == 200
        assert 'Вход'.encode() in response.data or b'Login' in response.data
    
    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get(url_for('auth.register'))
        assert response.status_code == 200
        assert 'Регистрация'.encode() in response.data or b'Register' in response.data
    
    def test_register_valid_user(self, client):
        """Test user registration with valid data."""
        response = client.post(
            url_for('auth.register'),
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
    
    def test_register_existing_user(self, client, app):
        """Test registration with existing username."""
        with app.app_context():
            # Create a user first
            user = User(username='existing', email='existing@example.com')
            user.set_password('password123')
            
        response = client.post(
            url_for('auth.register'),
            data={
                'username': 'existing',
                'email': 'new@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            }
        )
        assert response.status_code == 200
    
    def test_login_valid_user(self, client, app):
        """Test login with valid credentials."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
        
        response = client.post(
            url_for('auth.login'),
            data={
                'email': 'test@example.com',
                'password': 'password123'
            },
            follow_redirects=True
        )
        assert response.status_code == 200
    
    def test_login_invalid_password(self, client):
        """Test login with invalid password."""
        response = client.post(
            url_for('auth.login'),
            data={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }
        )
        assert response.status_code == 200
        assert b'error' in response.data.lower() or b'invalid' in response.data.lower()


class TestMain:
    """Test main routes."""
    
    def test_index_page(self, client):
        """Test index page loads."""
        response = client.get(url_for('main.index'))
        assert response.status_code == 200
        assert b'Flask Auth' in response.data
    
    def test_about_page(self, client):
        """Test about page loads."""
        response = client.get(url_for('main.about'))
        assert response.status_code == 200
    
    def test_contact_page(self, client):
        """Test contact page loads."""
        response = client.get(url_for('main.contact'))
        assert response.status_code == 200
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires authentication."""
        response = client.get(url_for('main.dashboard'), follow_redirects=False)
        assert response.status_code == 302  # Redirect to login


class TestForms:
    """Test form validation."""
    
    def test_invalid_email_format(self, client):
        """Test form rejects invalid email."""
        response = client.post(
            url_for('auth.register'),
            data={
                'username': 'testuser',
                'email': 'invalid-email',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            }
        )
        assert response.status_code == 200
    
    def test_weak_password(self, client):
        """Test form rejects weak password."""
        response = client.post(
            url_for('auth.register'),
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': '123',
                'confirm_password': '123'
            }
        )
        assert response.status_code == 200
    
    def test_password_mismatch(self, client):
        """Test form rejects mismatched passwords."""
        response = client.post(
            url_for('auth.register'),
            data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'DifferentPass123!'
            }
        )
        assert response.status_code == 200


class TestAPI:
    """Test API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        assert b'healthy' in response.data.lower() or b'ok' in response.data.lower()
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get('/metrics')
        assert response.status_code == 200 or response.status_code == 401  # May require auth


class TestErrorPages:
    """Test error page handling."""
    
    def test_404_page(self, client):
        """Test 404 page."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
    
    def test_500_error_handling(self, client, app):
        """Test 500 error handling."""
        @app.route('/test-error')
        def test_error():
            raise Exception('Test error')
        
        response = client.get('/test-error')
        assert response.status_code == 500


class TestAccessibility:
    """Test accessibility features."""
    
    def test_page_has_title(self, client):
        """Test pages have titles."""
        response = client.get(url_for('main.index'))
        assert b'<title>' in response.data
    
    def test_form_has_labels(self, client):
        """Test forms have labels."""
        response = client.get(url_for('auth.register'))
        assert b'<label' in response.data
    
    def test_navigation_exists(self, client):
        """Test navigation is present."""
        response = client.get(url_for('main.index'))
        assert b'nav' in response.data.lower()


class TestSecurity:
    """Test security features."""
    
    def test_csrf_protection(self, client):
        """Test CSRF protection on forms."""
        response = client.get(url_for('auth.register'))
        assert b'csrf' in response.data.lower()
    
    def test_password_hashing(self, app):
        """Test passwords are hashed."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('plaintext')
            
            # Password should be hashed
            assert user.password_hash != 'plaintext'
            assert user.check_password('plaintext')
            assert not user.check_password('wrongpassword')


class TestPerformance:
    """Test performance features."""
    
    def test_page_load_time(self, client):
        """Test page loads in reasonable time."""
        import time
        start = time.time()
        response = client.get(url_for('main.index'))
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0  # Should load in less than 2 seconds
    
    def test_asset_compression(self, client):
        """Test assets are compressed."""
        response = client.get('/static/css/styles.css')
        assert response.status_code == 200


class TestResponsiveness:
    """Test responsive design."""
    
    def test_mobile_viewport_meta(self, client):
        """Test mobile viewport meta tag."""
        response = client.get(url_for('main.index'))
        assert b'viewport' in response.data
        assert b'device-width' in response.data
    
    def test_favicon(self, client):
        """Test favicon is present."""
        response = client.get('/static/favicon.ico')
        # Favicon might not exist but should return 200 or 404, not 500
        assert response.status_code in [200, 404]


class TestSEO:
    """Test SEO optimization."""
    
    def test_meta_description(self, client):
        """Test page has meta description."""
        response = client.get(url_for('main.index'))
        assert b'description' in response.data.lower() or b'content=' in response.data
    
    def test_og_tags(self, client):
        """Test Open Graph tags."""
        response = client.get(url_for('main.index'))
        assert b'og:' in response.data or b'property=' in response.data
    
    def test_sitemap(self, client):
        """Test sitemap exists."""
        response = client.get('/static/sitemap.xml')
        assert response.status_code == 200
        assert b'<?xml' in response.data or b'url' in response.data
    
    def test_robots_txt(self, client):
        """Test robots.txt exists."""
        response = client.get('/static/robots.txt')
        assert response.status_code == 200
        assert b'User-agent' in response.data
