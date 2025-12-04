"""
Скрипт инициализации базы данных
Создает таблицы и добавляет тестовых пользователей
"""
from app import create_app, db
from models import User

def init_database():
    """Инициализация базы данных с тестовыми данными"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗄️  Создание таблиц базы данных...")
            db.create_all()
            print("✅ Таблицы созданы успешно!")
            
            # Проверка существования тестовых пользователей
            if User.query.filter_by(username='admin').first():
                print("⚠️  Тестовые пользователи уже существуют")
                return True
            
            print("\n👥 Создание тестовых пользователей...")
            
            # Создание администратора
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True,  # Make admin user an administrator
                email_confirmed=True  # Admin email is confirmed by default
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Создание тестового пользователя
            test_user = User(
                username='testuser',
                email='test@example.com',
                email_confirmed=True  # Test user email is confirmed by default
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            
            # Создание демо пользователя
            demo_user = User(
                username='demo',
                email='demo@example.com',
                email_confirmed=True  # Demo user email is confirmed by default
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            
            db.session.commit()
            
            print("✅ Тестовые пользователи созданы успешно!")
            print("\n📋 Данные для входа:")
            print("=" * 50)
            print("1️⃣  Администратор:")
            print("   Username: admin")
            print("   Password: admin123")
            print()
            print("2️⃣  Тестовый пользователь:")
            print("   Username: testuser")
            print("   Password: test123")
            print()
            print("3️⃣  Демо пользователь:")
            print("   Username: demo")
            print("   Password: demo123")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации базы данных: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Инициализация базы данных Flask Auth App")
    print("="*50 + "\n")
    
    success = init_database()
    
    if success:
        print("\n✨ Инициализация завершена успешно!")
        print("🌐 Запустите приложение: python app.py\n")
    else:
        print("\n❌ Инициализация завершена с ошибками!")
        print("Пожалуйста, проверьте сообщения об ошибках выше.\n")
        exit(1)
