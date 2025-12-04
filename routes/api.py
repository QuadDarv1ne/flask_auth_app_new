"""API routes with Swagger documentation"""

from flask import Blueprint, jsonify, request, current_app
from flask_restx import Api, Resource, fields
from flask_login import login_required, current_user
from models import User, db
from utils.metrics import set_active_users

# Создание blueprint для API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Создание API с Swagger UI
api = Api(
    api_bp,
    title='Flask Auth API',
    version='1.0',
    description='API для управления пользователями и аутентификацией',
    doc='/docs/'
)

# Модели для документации
user_model = api.model('User', {
    'id': fields.Integer(required=True, description='ID пользователя'),
    'username': fields.String(required=True, description='Имя пользователя'),
    'email': fields.String(required=True, description='Email пользователя'),
    'is_admin': fields.Boolean(required=True, description='Является ли администратором'),
    'email_confirmed': fields.Boolean(required=True, description='Подтвержден ли email')
})

# Namespace для пользователей
ns = api.namespace('users', description='Операции с пользователями')

@ns.route('/')
class UserList(Resource):
    @api.doc('list_users')
    @api.marshal_list_with(user_model)
    @login_required
    def get(self):
        """Получить список всех пользователей"""
        users = User.query.all()
        return [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'email_confirmed': user.email_confirmed
        } for user in users]

@ns.route('/<int:user_id>')
@api.param('user_id', 'ID пользователя')
class UserResource(Resource):
    @api.doc('get_user')
    @api.marshal_with(user_model)
    @login_required
    def get(self, user_id):
        """Получить информацию о пользователе по ID"""
        user = User.query.get_or_404(user_id)
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'email_confirmed': user.email_confirmed
        }

# Namespace для метрик
metrics_ns = api.namespace('metrics', description='Метрики приложения')

@metrics_ns.route('/active-users')
class ActiveUsers(Resource):
    @api.doc('get_active_users')
    @login_required
    def get(self):
        """Получить количество активных пользователей"""
        # Здесь должна быть логика подсчета активных пользователей
        # Для примера возвращаем фиксированное значение
        active_count = User.query.filter_by(email_confirmed=True).count()
        set_active_users(active_count)  # Обновляем метрику
        return {'active_users': active_count}

@metrics_ns.route('/health')
class HealthCheck(Resource):
    @api.doc('health_check')
    def get(self):
        """Проверка состояния приложения"""
        return {'status': 'healthy', 'service': 'flask-auth-api'}

# Namespace для профиля
profile_ns = api.namespace('profile', description='Операции с профилем пользователя')

@profile_ns.route('/me')
class Profile(Resource):
    @api.doc('get_profile')
    @api.marshal_with(user_model)
    @login_required
    def get(self):
        """Получить информацию о текущем пользователе"""
        return {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'is_admin': current_user.is_admin,
            'email_confirmed': current_user.email_confirmed
        }