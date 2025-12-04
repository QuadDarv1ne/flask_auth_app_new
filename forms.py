from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

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
                              Length(min=3, max=80, message='Имя пользователя должно быть от 3 до 80 символов')
                          ])
    email = StringField('Email', 
                       validators=[
                           DataRequired(message='Введите email'),
                           Email(message='Введите корректный email адрес')
                       ])
    password = PasswordField('Пароль', 
                            validators=[
                                DataRequired(message='Введите пароль'),
                                Length(min=6, message='Пароль должен содержать минимум 6 символов')
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
                              Length(min=3, max=80, message='Имя пользователя должно быть от 3 до 80 символов')
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
                                    Length(min=6, message='Пароль должен содержать минимум 6 символов')
                                ])
    confirm_password = PasswordField('Подтвердите новый пароль', 
                                    validators=[
                                        DataRequired(message='Подтвердите новый пароль'),
                                        EqualTo('new_password', message='Пароли должны совпадать')
                                    ])
    submit = SubmitField('Изменить пароль')
