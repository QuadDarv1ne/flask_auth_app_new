"""
Email notifications service
"""
from flask_mail import Mail, Message
from flask import current_app, render_template_string
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger('flask_auth_app.email')

mail = Mail()


class EmailService:
    """Сервис для отправки email."""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация с приложением Flask."""
        mail.init_app(app)
    
    @staticmethod
    def send_email(
        subject: str,
        recipients: List[str],
        text_body: str = None,
        html_body: str = None,
        sender: str = None,
        attachments: List = None
    ) -> bool:
        """
        Отправить email.
        
        Args:
            subject: Тема письма
            recipients: Список получателей
            text_body: Текстовое тело письма
            html_body: HTML тело письма
            sender: Отправитель (если не указан, берётся из конфига)
            attachments: Список вложений [(filename, content_type, data), ...]
        
        Returns:
            True если отправка успешна
        """
        try:
            if sender is None:
                sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
            
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=recipients
            )
            
            if text_body:
                msg.body = text_body
            
            if html_body:
                msg.html = html_body
            
            if attachments:
                for filename, content_type, data in attachments:
                    msg.attach(filename, content_type, data)
            
            mail.send(msg)
            logger.info(f"Email sent to {', '.join(recipients)}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(user_email: str, username: str) -> bool:
        """Отправить приветственное письмо."""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 10px; text-align: center; color: #666; font-size: 12px; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #4CAF50; 
                          color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Добро пожаловать!</h1>
                </div>
                <div class="content">
                    <h2>Здравствуйте, {username}!</h2>
                    <p>Спасибо за регистрацию в нашем приложении.</p>
                    <p>Ваш аккаунт успешно создан и готов к использованию.</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:5000/login" class="button">Войти в аккаунт</a>
                    </p>
                    <p>Если у вас возникнут вопросы, не стесняйтесь обращаться к нам.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} Flask Auth App. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Здравствуйте, {username}!
        
        Спасибо за регистрацию в нашем приложении.
        Ваш аккаунт успешно создан и готов к использованию.
        
        Войти: http://localhost:5000/login
        
        С уважением,
        Команда Flask Auth App
        """
        
        return EmailService.send_email(
            subject='Добро пожаловать в Flask Auth App!',
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
    
    @staticmethod
    def send_password_reset_email(user_email: str, username: str, reset_token: str) -> bool:
        """Отправить письмо для сброса пароля."""
        reset_url = f"http://localhost:5000/reset-password/{reset_token}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 10px; text-align: center; color: #666; font-size: 12px; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #f44336; 
                          color: white; text-decoration: none; border-radius: 5px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; 
                           border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Сброс пароля</h1>
                </div>
                <div class="content">
                    <h2>Здравствуйте, {username}!</h2>
                    <p>Мы получили запрос на сброс пароля для вашего аккаунта.</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" class="button">Сбросить пароль</a>
                    </p>
                    <div class="warning">
                        <strong>Важно:</strong> Эта ссылка действительна в течение 1 часа.
                    </div>
                    <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
                    <p style="color: #666; font-size: 12px;">
                        Или скопируйте эту ссылку в браузер:<br>
                        {reset_url}
                    </p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} Flask Auth App. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Здравствуйте, {username}!
        
        Мы получили запрос на сброс пароля для вашего аккаунта.
        
        Перейдите по ссылке для сброса пароля:
        {reset_url}
        
        Эта ссылка действительна в течение 1 часа.
        
        Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
        
        С уважением,
        Команда Flask Auth App
        """
        
        return EmailService.send_email(
            subject='Сброс пароля - Flask Auth App',
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
    
    @staticmethod
    def send_security_alert(user_email: str, username: str, alert_type: str, details: str) -> bool:
        """Отправить предупреждение о безопасности."""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 10px; text-align: center; color: #666; font-size: 12px; }}
                .alert {{ background: #ffebee; border: 1px solid #f44336; padding: 15px; 
                         border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Предупреждение безопасности</h1>
                </div>
                <div class="content">
                    <h2>Здравствуйте, {username}!</h2>
                    <p>Мы обнаружили необычную активность в вашем аккаунте.</p>
                    <div class="alert">
                        <strong>Тип события:</strong> {alert_type}<br>
                        <strong>Детали:</strong> {details}<br>
                        <strong>Время:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                    </div>
                    <p>Если это были вы, можете игнорировать это сообщение.</p>
                    <p>Если это были не вы, немедленно:</p>
                    <ul>
                        <li>Смените пароль</li>
                        <li>Включите двухфакторную аутентификацию</li>
                        <li>Проверьте активные сессии</li>
                    </ul>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} Flask Auth App. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Здравствуйте, {username}!
        
        ⚠️ ПРЕДУПРЕЖДЕНИЕ БЕЗОПАСНОСТИ
        
        Мы обнаружили необычную активность в вашем аккаунте.
        
        Тип события: {alert_type}
        Детали: {details}
        Время: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        
        Если это были вы, можете игнорировать это сообщение.
        
        Если это были не вы, немедленно:
        - Смените пароль
        - Включите двухфакторную аутентификацию
        - Проверьте активные сессии
        
        С уважением,
        Команда Flask Auth App
        """
        
        return EmailService.send_email(
            subject=f'🔒 Предупреждение безопасности - {alert_type}',
            recipients=[user_email],
            text_body=text_body,
            html_body=html_body
        )
    
    @staticmethod
    def send_2fa_enabled_email(user_email: str, username: str) -> bool:
        """Уведомление о включении 2FA."""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ padding: 10px; text-align: center; color: #666; font-size: 12px; }}
                .success {{ background: #e8f5e9; border: 1px solid #4caf50; padding: 15px; 
                           border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Двухфакторная аутентификация включена</h1>
                </div>
                <div class="content">
                    <h2>Здравствуйте, {username}!</h2>
                    <div class="success">
                        ✓ Двухфакторная аутентификация успешно включена для вашего аккаунта.
                    </div>
                    <p>Ваш аккаунт теперь защищён дополнительным уровнем безопасности.</p>
                    <p>При каждом входе вам потребуется вводить код из приложения-аутентификатора.</p>
                    <p><strong>Важно:</strong> Сохраните резервные коды в надёжном месте!</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.utcnow().year} Flask Auth App. Все права защищены.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            subject='🔐 Двухфакторная аутентификация включена',
            recipients=[user_email],
            html_body=html_body
        )


# Инициализация сервиса
email_service = EmailService()
