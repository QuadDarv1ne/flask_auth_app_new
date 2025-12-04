from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from forms import UpdateProfileForm, ChangePasswordForm, ContactForm
from utils.logging import log_user_action
import os
from werkzeug.utils import secure_filename

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
    
    # Handle profile form submission (when accessed via GET or POST but not from password form)
    if request.method == 'POST' and 'submit' in request.form and profile_form.validate_on_submit():
        old_username = current_user.username
        current_user.username = profile_form.username.data
        current_user.email = profile_form.email.data
        
        # Handle avatar upload
        if profile_form.avatar.data:
            avatar_file = profile_form.avatar.data
            filename = secure_filename(avatar_file.filename)
            if filename:
                # Create avatars directory if it doesn't exist
                avatar_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(avatar_dir, exist_ok=True)
                
                # Generate unique filename
                name, ext = os.path.splitext(filename)
                unique_filename = f"{current_user.id}_{secure_filename(name)}{ext}"
                filepath = os.path.join(avatar_dir, unique_filename)
                
                # Save the file
                avatar_file.save(filepath)
                
                # Update user's avatar filename
                current_user.set_avatar(unique_filename)
        
        db.session.commit()
        
        log_user_action(
            current_user.username,
            'profile_updated',
            f'Old username: {old_username}, New email: {current_user.email}'
        )
        
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('main.profile'))
    
    # Populate forms with current data
    profile_form.username.data = current_user.username
    profile_form.email.data = current_user.email
    
    return render_template('main/profile.html', 
                         title='Профиль',
                         user=current_user,
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
        
        log_user_action(
            current_user.username,
            'password_changed',
            'Password successfully updated'
        )
        
        flash('Пароль успешно изменен!', 'success')
        return redirect(url_for('main.profile'))
    
    # Handle form validation errors
    for field, errors in password_form.errors.items():
        for error in errors:
            flash(f'{getattr(password_form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('main.profile'))

@main_bp.route('/about')
def about():
    """Страница О нас"""
    return render_template('main/about.html', title='О нас')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Страница контактов"""
    form = ContactForm()
    
    if form.validate_on_submit():
        # Здесь можно добавить отправку email
        # или сохранение сообщения в БД
        
        log_user_action(
            form.email.data,
            'contact_form_submitted',
            f'Subject: {form.subject.data}'
        )
        
        flash('Спасибо за ваше сообщение! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('main/contact.html', title='Контакты', form=form)