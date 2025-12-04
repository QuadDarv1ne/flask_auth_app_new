"""
Утилиты для работы с email
"""
from flask_mail import Mail, Message
from flask import current_app, render_template
from threading import Thread


mail = Mail()


def send_async_email(app, msg):
    """
    Асинхронная отправка email
    """
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {str(e)}")


def send_email(subject, recipients, text_body, html_body, sender=None):
    """
    Отправка email сообщения
    
    Args:
        subject: Тема письма
        recipients: Список получателей
        text_body: Текстовая версия письма
        html_body: HTML версия письма
        sender: Отправитель (если None, используется из конфига)
    """
    app = current_app._get_current_object()
    
    msg = Message(
        subject,
        sender=sender or app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=recipients
    )
    msg.body = text_body
    msg.html = html_body
    
    # Отправляем асинхронно
    Thread(target=send_async_email, args=(app, msg)).start()


def send_verification_email(user, token):
    """
    Отправка письма для подтверждения email
    
    Args:
        user: Объект пользователя
        token: Токен для верификации
    """
    subject = "Подтвердите ваш email - Flask Auth App"
    
    # Генерируем ссылку для подтверждения
    verification_url = f"{current_app.config.get('APP_URL')}/verify-email/{token}"
    
    text_body = f"""
    Здравствуйте, {user.username}!
    
    Для активации вашей учетной записи, пожалуйста, перейдите по ссылке:
    {verification_url}
    
    Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.
    
    С уважением,
    Команда Flask Auth App
    """
    
    html_body = render_template(
        'email/verify_email.html',
        user=user,
        verification_url=verification_url
    )
    
    send_email(subject, [user.email], text_body, html_body)


def send_password_reset_email(user, token):
    """
    Отправка письма для сброса пароля
    
    Args:
        user: Объект пользователя
        token: Токен для сброса пароля
    """
    subject = "Сброс пароля - Flask Auth App"
    
    reset_url = f"{current_app.config.get('APP_URL')}/reset-password/{token}"
    
    text_body = f"""
    Здравствуйте, {user.username}!
    
    Для сброса пароля перейдите по ссылке:
    {reset_url}
    
    Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
    
    С уважением,
    Команда Flask Auth App
    """
    
    html_body = render_template(
        'email/reset_password.html',
        user=user,
        reset_url=reset_url
    )
    
    send_email(subject, [user.email], text_body, html_body)


def send_welcome_email(user):
    """
    Отправка приветственного письма новому пользователю
    
    Args:
        user: Объект пользователя
    """
    subject = "Добро пожаловать в Flask Auth App!"
    
    text_body = f"""
    Здравствуйте, {user.username}!
    
    Спасибо за регистрацию в Flask Auth App.
    
    Теперь вы можете войти в систему и начать использовать все возможности приложения.
    
    С уважением,
    Команда Flask Auth App
    """
    
    html_body = render_template(
        'email/welcome.html',
        user=user
    )
    
    send_email(subject, [user.email], text_body, html_body)
