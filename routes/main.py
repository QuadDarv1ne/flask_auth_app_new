from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from forms import UpdateProfileForm, ChangePasswordForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Главная страница"""
    return render_template('main/index.html', title='Главная')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Личный кабинет пользователя"""
    return render_template('main/dashboard.html', title='Личный кабинет', user=current_user)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Страница профиля пользователя"""
    profile_form = UpdateProfileForm(current_user.username, current_user.email)
    password_form = ChangePasswordForm()
    
    if profile_form.validate_on_submit():
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        db.session.commit()
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('main.profile'))
    elif profile_form.is_submitted():
        flash('Пожалуйста, исправьте ошибки в форме.', 'error')
    
    # Заполнение формы текущими данными
    profile_form.username.data = current_user.username
    profile_form.email.data = current_user.email
    
    return render_template('main/profile.html', 
                         title='Профиль', 
                         profile_form=profile_form,
                         password_form=password_form)

@main_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Изменение пароля пользователя"""
    password_form = ChangePasswordForm()
    
    if password_form.validate_on_submit():
        # Проверка текущего пароля
        if not current_user.check_password(password_form.current_password.data):
            flash('Неверный текущий пароль!', 'error')
            return redirect(url_for('main.profile'))
        
        # Установка нового пароля
        current_user.set_password(password_form.new_password.data)
        db.session.commit()
        flash('Пароль успешно изменен!', 'success')
        return redirect(url_for('main.profile'))
    
    flash('Пожалуйста, исправьте ошибки в форме смены пароля.', 'error')
    return redirect(url_for('main.profile'))
