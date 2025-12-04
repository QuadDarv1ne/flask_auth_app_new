"""API routes with Swagger documentation"""

from flask import Blueprint, jsonify, request, current_app
from flask_restx import Api, Resource, fields
from flask_login import login_required, current_user
from models import User, db
from utils.metrics import set_active_users
from utils.performance import cache_response
from datetime import datetime

# Создание blueprint для API
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Создание API с Swagger UI
api = Api(
    api_bp,
    title='Flask Auth API',
    version='1.0',
    description='API для управления пользователями и аутентификацией',
    doc='/docs/',
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
    security='apikey'
)

# Модели для документации
user_model = api.model('User', {
    'id': fields.Integer(required=True, description='ID пользователя'),
    'username': fields.String(required=True, description='Имя пользователя'),
    'email': fields.String(required=True, description='Email пользователя'),
    'is_admin': fields.Boolean(required=True, description='Является ли администратором'),
    'email_confirmed': fields.Boolean(required=True, description='Подтвержден ли email'),
    'created_at': fields.DateTime(required=False, description='Дата создания'),
    'last_login': fields.DateTime(required=False, description='Дата последнего входа')
})

user_input_model = api.model('UserInput', {
    'username': fields.String(required=True, description='Имя пользователя'),
    'email': fields.String(required=True, description='Email пользователя')
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
            'email_confirmed': user.email_confirmed,
            'created_at': user.created_at,
            'last_login': user.last_login
        } for user in users]

    @api.doc('create_user')
    @api.expect(user_input_model)
    @api.marshal_with(user_model, code=201)
    @login_required
    def post(self):
        """Создать нового пользователя (только для администраторов)"""
        if not current_user.is_admin:
            api.abort(403, 'Только администраторы могут создавать пользователей')
        
        data = request.json
        
        # Проверка существующего пользователя
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            api.abort(400, 'Пользователь с таким email уже существует')
        
        # Создание нового пользователя
        user = User(
            username=data['username'],
            email=data['email']
        )
        db.session.add(user)
        db.session.commit()
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'email_confirmed': user.email_confirmed,
            'created_at': user.created_at,
            'last_login': user.last_login
        }, 201

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
            'email_confirmed': user.email_confirmed,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
    
    @api.doc('update_user')
    @api.expect(user_input_model)
    @api.marshal_with(user_model)
    @login_required
    def put(self, user_id):
        """Обновить информацию о пользователе"""
        user = User.query.get_or_404(user_id)
        
        # Проверка прав доступа
        if current_user.id != user_id and not current_user.is_admin:
            api.abort(403, 'У вас нет прав на изменение этого пользователя')
        
        data = request.json
        
        # Проверка уникальности email
        if data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                api.abort(400, 'Пользователь с таким email уже существует')
        
        # Обновление данных
        user.username = data['username']
        user.email = data['email']
        db.session.commit()
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'email_confirmed': user.email_confirmed,
            'created_at': user.created_at,
            'last_login': user.last_login
        }
    
    @api.doc('delete_user')
    @login_required
    def delete(self, user_id):
        """Удалить пользователя (только для администраторов)"""
        if not current_user.is_admin:
            api.abort(403, 'Только администраторы могут удалять пользователей')
        
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        
        return {'message': 'Пользователь успешно удален'}, 204

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
        return {'status': 'healthy', 'service': 'flask-auth-api', 'timestamp': datetime.utcnow().isoformat()}

@metrics_ns.route('/stats')
class SystemStats(Resource):
    @api.doc('get_system_stats')
    @login_required
    @cache_response(timeout=60)  # Кэшируем статистику на 1 минуту
    def get(self):
        """Получить системную статистику"""
        total_users = User.query.count()
        confirmed_users = User.query.filter_by(email_confirmed=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        
        return {
            'total_users': total_users,
            'confirmed_users': confirmed_users,
            'unconfirmed_users': total_users - confirmed_users,
            'admin_users': admin_users,
            'timestamp': datetime.utcnow().isoformat()
        }

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
            'email_confirmed': current_user.email_confirmed,
            'created_at': current_user.created_at,
            'last_login': current_user.last_login
        }
    
    @api.doc('update_profile')
    @api.expect(user_input_model)
    @api.marshal_with(user_model)
    @login_required
    def put(self):
        """Обновить профиль текущего пользователя"""
        data = request.json
        
        # Проверка уникальности email
        if data['email'] != current_user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                api.abort(400, 'Пользователь с таким email уже существует')
        
        # Обновление данных
        current_user.username = data['username']
        current_user.email = data['email']
        db.session.commit()
        
        return {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'is_admin': current_user.is_admin,
            'email_confirmed': current_user.email_confirmed,
            'created_at': current_user.created_at,
            'last_login': current_user.last_login
        }
    
    @api.doc('delete_profile')
    @login_required
    def delete(self):
        """Удалить профиль текущего пользователя"""
        db.session.delete(current_user)
        db.session.commit()
        
        return {'message': 'Профиль успешно удален'}, 204