#!/usr/bin/env python
"""
Утилита для резервного копирования и восстановления базы данных
"""
import os
import sys
import subprocess
import gzip
import json
from pathlib import Path
from datetime import datetime


class DatabaseBackup:
    """Управление резервным копированием БД."""
    
    def __init__(self, db_config, backup_dir='backups'):
        self.db_config = db_config
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def get_postgres_connection(self):
        """Получить параметры подключения PostgreSQL."""
        return {
            'host': self.db_config.get('host', 'localhost'),
            'port': self.db_config.get('port', 5432),
            'user': self.db_config.get('user'),
            'password': self.db_config.get('password'),
            'database': self.db_config.get('database'),
        }
    
    def backup_postgresql(self, backup_type='full'):
        """Создать резервную копию PostgreSQL."""
        conn = self.get_postgres_connection()
        
        # Название файла
        backup_file = self.backup_dir / f"postgres_{self.timestamp}_{backup_type}.sql.gz"
        
        try:
            # Команда pg_dump
            cmd = [
                'pg_dump',
                '-h', conn['host'],
                '-p', str(conn['port']),
                '-U', conn['user'],
                '-d', conn['database'],
                '--format=plain',
                '--verbose',
            ]
            
            # Параметры бэкапа
            if backup_type == 'schema_only':
                cmd.append('--schema-only')
            elif backup_type == 'data_only':
                cmd.append('--data-only')
            
            # Установка пароля для pg_dump
            env = os.environ.copy()
            if conn['password']:
                env['PGPASSWORD'] = conn['password']
            
            # Выполнение с сжатием
            with gzip.open(backup_file, 'wb') as gz:
                process = subprocess.Popen(
                    cmd,
                    stdout=gz,
                    stderr=subprocess.PIPE,
                    env=env
                )
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"pg_dump error: {stderr.decode()}")
            
            # Запись метаданных
            metadata = {
                'timestamp': self.timestamp,
                'type': backup_type,
                'database': conn['database'],
                'size': backup_file.stat().st_size,
                'compressed': True
            }
            self._save_metadata(backup_file, metadata)
            
            print(f"✓ Бэкап создан: {backup_file}")
            return backup_file
        
        except Exception as e:
            print(f"✗ Ошибка создания бэкапа: {e}")
            return None
    
    def backup_sqlite(self):
        """Создать резервную копию SQLite."""
        db_file = self.db_config.get('database')
        
        if not Path(db_file).exists():
            print(f"✗ БД файл не найден: {db_file}")
            return None
        
        backup_file = self.backup_dir / f"sqlite_{self.timestamp}.db.gz"
        
        try:
            with open(db_file, 'rb') as f_in:
                with gzip.open(backup_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            metadata = {
                'timestamp': self.timestamp,
                'type': 'full',
                'database': db_file,
                'size': backup_file.stat().st_size,
                'compressed': True
            }
            self._save_metadata(backup_file, metadata)
            
            print(f"✓ Бэкап создан: {backup_file}")
            return backup_file
        
        except Exception as e:
            print(f"✗ Ошибка создания бэкапа: {e}")
            return None
    
    def restore_postgresql(self, backup_file):
        """Восстановить БД из резервной копии PostgreSQL."""
        if not Path(backup_file).exists():
            print(f"✗ Файл бэкапа не найден: {backup_file}")
            return False
        
        conn = self.get_postgres_connection()
        
        try:
            # Проверка целостности архива
            print("Проверка целостности архива...")
            subprocess.run(['gzip', '-t', str(backup_file)], check=True)
            print("✓ Архив целостен")
            
            # Восстановление
            print(f"Восстановление БД из {backup_file}...")
            env = os.environ.copy()
            if conn['password']:
                env['PGPASSWORD'] = conn['password']
            
            with gzip.open(backup_file, 'rb') as gz:
                process = subprocess.Popen(
                    [
                        'psql',
                        '-h', conn['host'],
                        '-p', str(conn['port']),
                        '-U', conn['user'],
                        '-d', conn['database'],
                    ],
                    stdin=gz,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"psql error: {stderr.decode()}")
            
            print("✓ БД успешно восстановлена")
            return True
        
        except Exception as e:
            print(f"✗ Ошибка восстановления: {e}")
            return False
    
    def restore_sqlite(self, backup_file):
        """Восстановить БД из резервной копии SQLite."""
        if not Path(backup_file).exists():
            print(f"✗ Файл бэкапа не найден: {backup_file}")
            return False
        
        db_file = self.db_config.get('database')
        
        try:
            # Проверка целостности
            print("Проверка целостности архива...")
            subprocess.run(['gzip', '-t', str(backup_file)], check=True)
            print("✓ Архив целостен")
            
            # Создание резервной копии текущей БД
            if Path(db_file).exists():
                backup_current = Path(db_file).with_suffix('.db.bak')
                print(f"Создание резервной копии текущей БД...")
                os.rename(db_file, backup_current)
            
            # Восстановление
            print(f"Восстановление БД из {backup_file}...")
            with gzip.open(backup_file, 'rb') as f_in:
                with open(db_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            print("✓ БД успешно восстановлена")
            return True
        
        except Exception as e:
            print(f"✗ Ошибка восстановления: {e}")
            return False
    
    def list_backups(self):
        """Список всех резервных копий."""
        backups = sorted(self.backup_dir.glob('*.sql.gz')) + \
                  sorted(self.backup_dir.glob('*.db.gz'))
        
        if not backups:
            print("Резервных копий не найдено")
            return
        
        print("\nДоступные резервные копии:")
        print("-" * 80)
        
        for backup_file in backups:
            metadata = self._load_metadata(backup_file)
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            
            if metadata:
                print(f"Файл: {backup_file.name}")
                print(f"  Время: {metadata.get('timestamp', 'N/A')}")
                print(f"  Тип: {metadata.get('type', 'unknown')}")
                print(f"  Размер: {size_mb:.2f} MB")
                print()
    
    def cleanup_old_backups(self, keep_count=10):
        """Удалить старые резервные копии, оставив последние."""
        backups = sorted(
            list(self.backup_dir.glob('*.sql.gz')) + 
            list(self.backup_dir.glob('*.db.gz')),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if len(backups) > keep_count:
            for backup_file in backups[keep_count:]:
                backup_file.unlink()
                meta_file = backup_file.with_suffix('.json')
                if meta_file.exists():
                    meta_file.unlink()
                print(f"✓ Удален старый бэкап: {backup_file.name}")
    
    def _save_metadata(self, backup_file, metadata):
        """Сохранить метаданные бэкапа."""
        meta_file = backup_file.with_suffix('.json')
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_metadata(self, backup_file):
        """Загрузить метаданные бэкапа."""
        meta_file = backup_file.with_suffix('.json')
        if meta_file.exists():
            with open(meta_file, 'r') as f:
                return json.load(f)
        return None


def main():
    """Главная функция CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Управление резервными копиями БД'
    )
    parser.add_argument(
        'action',
        choices=['backup', 'restore', 'list', 'cleanup'],
        help='Действие'
    )
    parser.add_argument(
        '--db-type',
        choices=['postgres', 'sqlite'],
        default='postgres',
        help='Тип БД'
    )
    parser.add_argument(
        '--backup-type',
        choices=['full', 'schema_only', 'data_only'],
        default='full',
        help='Тип бэкапа (для PostgreSQL)'
    )
    parser.add_argument(
        '--file',
        help='Файл бэкапа для восстановления'
    )
    parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='Количество бэкапов для сохранения'
    )
    
    args = parser.parse_args()
    
    # Конфигурация БД из environment
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', 5432),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME') or os.getenv('DATABASE_URL'),
    }
    
    backup = DatabaseBackup(db_config)
    
    if args.action == 'backup':
        if args.db_type == 'postgres':
            backup.backup_postgresql(args.backup_type)
        else:
            backup.backup_sqlite()
    
    elif args.action == 'restore':
        if not args.file:
            print("Укажите файл бэкапа через --file")
            return 1
        
        if args.db_type == 'postgres':
            success = backup.restore_postgresql(args.file)
        else:
            success = backup.restore_sqlite(args.file)
        
        return 0 if success else 1
    
    elif args.action == 'list':
        backup.list_backups()
    
    elif args.action == 'cleanup':
        backup.cleanup_old_backups(args.keep)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
