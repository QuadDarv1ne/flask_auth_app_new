"""
WebSocket support for real-time features
"""
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask import request
from flask_login import current_user
import logging

logger = logging.getLogger('flask_auth_app.websocket')

# Инициализация SocketIO
socketio = SocketIO(cors_allowed_origins="*")


class WebSocketManager:
    """Менеджер WebSocket соединений."""
    
    def __init__(self):
        self.active_connections = {}
        self.user_rooms = {}
    
    def add_connection(self, sid: str, user_id: int = None):
        """Добавить соединение."""
        self.active_connections[sid] = {
            'user_id': user_id,
            'connected_at': None,
        }
        logger.info(f"WebSocket connected: {sid} (user: {user_id})")
    
    def remove_connection(self, sid: str):
        """Удалить соединение."""
        if sid in self.active_connections:
            user_id = self.active_connections[sid].get('user_id')
            del self.active_connections[sid]
            logger.info(f"WebSocket disconnected: {sid} (user: {user_id})")
    
    def get_user_connections(self, user_id: int) -> list:
        """Получить все соединения пользователя."""
        return [
            sid for sid, data in self.active_connections.items()
            if data.get('user_id') == user_id
        ]
    
    def broadcast_to_user(self, user_id: int, event: str, data: dict):
        """Отправить сообщение всем соединениям пользователя."""
        connections = self.get_user_connections(user_id)
        for sid in connections:
            socketio.emit(event, data, room=sid)
    
    def get_stats(self) -> dict:
        """Получить статистику соединений."""
        return {
            'total_connections': len(self.active_connections),
            'authenticated_users': len(set(
                data['user_id'] for data in self.active_connections.values()
                if data.get('user_id')
            ))
        }


# Глобальный менеджер
ws_manager = WebSocketManager()


@socketio.on('connect')
def handle_connect():
    """Обработка подключения."""
    user_id = current_user.id if current_user.is_authenticated else None
    ws_manager.add_connection(request.sid, user_id)
    
    emit('connected', {
        'message': 'Successfully connected to WebSocket',
        'sid': request.sid
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения."""
    ws_manager.remove_connection(request.sid)


@socketio.on('join')
def handle_join(data):
    """Присоединение к комнате."""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room}, room=request.sid)
        logger.info(f"User joined room: {room}")


@socketio.on('leave')
def handle_leave(data):
    """Покинуть комнату."""
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left', {'room': room}, room=request.sid)
        logger.info(f"User left room: {room}")


@socketio.on('message')
def handle_message(data):
    """Обработка сообщения."""
    logger.info(f"Message received: {data}")
    emit('message', data, broadcast=True)


@socketio.on('notification')
def handle_notification(data):
    """Отправка уведомления."""
    if current_user.is_authenticated:
        user_id = data.get('user_id')
        if user_id:
            ws_manager.broadcast_to_user(user_id, 'notification', {
                'message': data.get('message'),
                'type': data.get('type', 'info'),
                'timestamp': data.get('timestamp')
            })


@socketio.on('ping')
def handle_ping():
    """Обработка ping."""
    emit('pong', {'timestamp': str(datetime.utcnow())})


def init_websocket(app):
    """Инициализация WebSocket с приложением."""
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    logger.info("WebSocket initialized")


# Утилиты для отправки событий
def send_notification(user_id: int, message: str, notification_type: str = 'info'):
    """Отправить уведомление пользователю."""
    ws_manager.broadcast_to_user(user_id, 'notification', {
        'message': message,
        'type': notification_type,
        'timestamp': str(datetime.utcnow())
    })


def broadcast_message(event: str, data: dict, room: str = None):
    """Отправить сообщение всем или в комнату."""
    if room:
        socketio.emit(event, data, room=room)
    else:
        socketio.emit(event, data, broadcast=True)
