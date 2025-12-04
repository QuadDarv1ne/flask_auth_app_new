from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User
from validators import PasswordStrength, NoCommonPasswords, UsernameValidator

class LoginForm(FlaskForm):
    """Форма входа в систему"""
    
    username = StringField('Имя пользователя', 
                          validators=[DataRequired(message='Введите имя пользователя')])
    password = PasswordField('Пароль', 
                            validators=[DataRequired(message='Введите пароль')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    """Форма регистрации нового пользователя"""
    
    username = StringField('Имя пользователя', 
                          validators=[
                              DataRequired(message='Введите имя пользователя'),
                              Length(min=3, max=80, message='Имя пользователя должно быть от 3 до 80 символов'),
                              UsernameValidator()
                          ])
    email = StringField('Email', 
                       validators=[
                           DataRequired(message='Введите email'),
                           Email(message='Введите корректный email адрес')
                       ])
    password = PasswordField('Пароль', 
                            validators=[
                                DataRequired(message='Введите пароль'),
                                Length(min=8, message='Пароль должен содержать минимум 8 символов'),
                                PasswordStrength(require_uppercase=True, require_lowercase=True, 
                                               require_digit=True, require_special=False),
                                NoCommonPasswords()
                            ])
    password2 = PasswordField('Повторите пароль', 
                             validators=[
                                 DataRequired(message='Повторите пароль'),
                                 EqualTo('password', message='Пароли должны совпадать')
                             ])
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        """Проверка уникальности имени пользователя"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Выберите другое.')
    
    def validate_email(self, email):
        """Проверка уникальности email"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Используйте другой.')

class UpdateProfileForm(FlaskForm):
    """Форма обновления профиля пользователя"""
    
    username = StringField('Имя пользователя', 
                          validators=[
                              DataRequired(message='Введите имя пользователя'),
                              Length(min=3, max=80, message='Имя пользователя должно быть от 3 до 80 символов'),
                              UsernameValidator()
                          ])
    email = StringField('Email', 
                       validators=[
                           DataRequired(message='Введите email'),
                           Email(message='Введите корректный email адрес')
                       ])
    submit = SubmitField('Сохранить изменения')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        """Проверка уникальности имени пользователя"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Это имя пользователя уже занято. Выберите другое.')
    
    def validate_email(self, email):
        """Проверка уникальности email"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Этот email уже зарегистрирован. Используйте другой.')

class ChangePasswordForm(FlaskForm):
    """Форма изменения пароля"""
    
    current_password = PasswordField('Текущий пароль', 
                                    validators=[DataRequired(message='Введите текущий пароль')])
    new_password = PasswordField('Новый пароль', 
                                validators=[
                                    DataRequired(message='Введите новый пароль'),
                                    Length(min=8, message='Пароль должен содержать минимум 8 символов'),
                                    PasswordStrength(require_uppercase=True, require_lowercase=True, 
                                                   require_digit=True, require_special=False),
                                    NoCommonPasswords()
                                ])
    confirm_password = PasswordField('Подтвердите новый пароль', 
                                    validators=[
                                        DataRequired(message='Подтвердите новый пароль'),
                                        EqualTo('new_password', message='Пароли должны совпадать')
                                    ])
    submit = SubmitField('Изменить пароль')

class ContactForm(FlaskForm):
    """Форма обратной связи"""
    
    name = StringField('Имя', 
                      validators=[
                          DataRequired(message='Введите ваше имя'),
                          Length(min=2, max=100, message='Имя должно быть от 2 до 100 символов')
                      ])
    email = StringField('Email', 
                       validators=[
                           DataRequired(message='Введите email'),
                           Email(message='Введите корректный email адрес')
                       ])
    subject = StringField('Тема', 
                         validators=[
                             DataRequired(message='Введите тему сообщения'),
                             Length(min=5, max=200, message='Тема должна быть от 5 до 200 символов')
                         ])
    message = TextAreaField('Сообщение', 
                           validators=[
                               DataRequired(message='Введите текст сообщения'),
                               Length(min=10, max=2000, message='Сообщение должно быть от 10 до 2000 символов')
                           ])
    submit = SubmitField('Отправить сообщение')
