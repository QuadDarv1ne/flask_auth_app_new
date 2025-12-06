"""
Background Tasks & Job Queue - Celery alternative using SQLAlchemy
"""
import json
import time
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass
import uuid

logger = logging.getLogger('flask_auth_app.background_tasks')


class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRY = 'retry'


class TaskPriority(Enum):
    """Приоритеты задач"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskConfig:
    """Конфигурация задачи"""
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    timeout: int = 300
    expires_in: int = 3600


class TaskQueue:
    """Очередь фоновых задач"""
    
    def __init__(self, db):
        self.db = db
        self.tasks = {}
        self.workers = []
    
    def register_task(self, name: str, func: Callable):
        """Зарегистрировать задачу"""
        self.tasks[name] = func
        logger.info(f"Task registered: {name}")
    
    def enqueue(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_at: datetime = None
    ) -> str:
        """Добавить задачу в очередь"""
        if kwargs is None:
            kwargs = {}
        
        from models import BackgroundTask
        
        task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            id=task_id,
            name=task_name,
            args=json.dumps(args),
            kwargs=json.dumps(kwargs),
            status=TaskStatus.PENDING.value,
            priority=priority.value,
            scheduled_at=scheduled_at or datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        self.db.session.add(task)
        self.db.session.commit()
        
        logger.info(f"Task enqueued: {task_name} ({task_id})")
        return task_id
    
    def get_next_task(self):
        """Получить следующую задачу из очереди"""
        from models import BackgroundTask
        
        task = BackgroundTask.query.filter_by(
            status=TaskStatus.PENDING.value
        ).filter(
            BackgroundTask.scheduled_at <= datetime.utcnow()
        ).order_by(
            BackgroundTask.priority.desc(),
            BackgroundTask.created_at.asc()
        ).first()
        
        return task
    
    def execute_task(self, task_id: str):
        """Выполнить задачу"""
        from models import BackgroundTask
        
        task = BackgroundTask.query.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        try:
            # Обновляем статус на RUNNING
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.utcnow()
            self.db.session.commit()
            
            # Получаем функцию
            if task.name not in self.tasks:
                raise ValueError(f"Unknown task: {task.name}")
            
            func = self.tasks[task.name]
            
            # Выполняем задачу
            args = json.loads(task.args)
            kwargs = json.loads(task.kwargs)
            
            result = func(*args, **kwargs)
            
            # Обновляем статус на COMPLETED
            task.status = TaskStatus.COMPLETED.value
            task.completed_at = datetime.utcnow()
            task.result = json.dumps({'success': True, 'data': result})
            
            logger.info(f"Task completed: {task.name} ({task_id})")
            
        except Exception as e:
            logger.error(f"Task failed: {task.name} ({task_id}) - {e}")
            
            # Проверяем повторы
            if task.retries < task.max_retries:
                task.status = TaskStatus.RETRY.value
                task.retries += 1
                task.scheduled_at = datetime.utcnow() + timedelta(minutes=5)
            else:
                task.status = TaskStatus.FAILED.value
                task.error = str(e)
            
            task.completed_at = datetime.utcnow()
        
        finally:
            self.db.session.commit()
    
    def process_queue(self, batch_size: int = 10):
        """Обработать очередь"""
        logger.info("Processing task queue...")
        
        processed = 0
        while processed < batch_size:
            task = self.get_next_task()
            if not task:
                break
            
            self.execute_task(task.id)
            processed += 1
        
        logger.info(f"Processed {processed} tasks")
        
        return processed


class ScheduledTask:
    """Периодическая задача"""
    
    def __init__(
        self,
        name: str,
        func: Callable,
        schedule: str,  # 'hourly', 'daily', 'weekly', 'monthly'
        args: tuple = (),
        kwargs: dict = None
    ):
        self.name = name
        self.func = func
        self.schedule = schedule
        self.args = args
        self.kwargs = kwargs or {}
        self.last_run = None
    
    def should_run(self) -> bool:
        """Проверить, нужно ли запустить задачу"""
        if self.last_run is None:
            return True
        
        now = datetime.utcnow()
        
        if self.schedule == 'hourly':
            return now - self.last_run >= timedelta(hours=1)
        elif self.schedule == 'daily':
            return now - self.last_run >= timedelta(days=1)
        elif self.schedule == 'weekly':
            return now - self.last_run >= timedelta(weeks=1)
        elif self.schedule == 'monthly':
            return now - self.last_run >= timedelta(days=30)
        
        return False
    
    def run(self):
        """Запустить задачу"""
        try:
            logger.info(f"Running scheduled task: {self.name}")
            result = self.func(*self.args, **self.kwargs)
            self.last_run = datetime.utcnow()
            logger.info(f"Scheduled task completed: {self.name}")
            return result
        except Exception as e:
            logger.error(f"Scheduled task failed: {self.name} - {e}")
            raise


class TaskScheduler:
    """Планировщик периодических задач"""
    
    def __init__(self):
        self.scheduled_tasks = {}
    
    def register_scheduled_task(self, task: ScheduledTask):
        """Зарегистрировать периодическую задачу"""
        self.scheduled_tasks[task.name] = task
        logger.info(f"Scheduled task registered: {task.name} ({task.schedule})")
    
    def run_due_tasks(self):
        """Запустить задачи, которые нужно выполнить"""
        for task_name, task in self.scheduled_tasks.items():
            if task.should_run():
                try:
                    task.run()
                except Exception as e:
                    logger.error(f"Failed to run scheduled task: {task_name} - {e}")
    
    def get_tasks_info(self) -> dict:
        """Получить информацию о всех задачах"""
        return {
            name: {
                'schedule': task.schedule,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': self._calculate_next_run(task)
            }
            for name, task in self.scheduled_tasks.items()
        }
    
    def _calculate_next_run(self, task: ScheduledTask) -> str:
        """Вычислить время следующего запуска"""
        if task.last_run is None:
            return datetime.utcnow().isoformat()
        
        if task.schedule == 'hourly':
            next_run = task.last_run + timedelta(hours=1)
        elif task.schedule == 'daily':
            next_run = task.last_run + timedelta(days=1)
        elif task.schedule == 'weekly':
            next_run = task.last_run + timedelta(weeks=1)
        elif task.schedule == 'monthly':
            next_run = task.last_run + timedelta(days=30)
        else:
            next_run = datetime.utcnow()
        
        return next_run.isoformat()


# Common background tasks
class CommonTasks:
    """Обычные фоновые задачи"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        """Отправить email"""
        from utils.email_service import email_service
        
        logger.info(f"Sending email to {to_email}: {subject}")
        
        try:
            email_service.send_email(to_email, subject, body)
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    @staticmethod
    def backup_database(db_path: str) -> bool:
        """Резервная копия БД"""
        from utils.backup import backup_database
        
        logger.info("Starting database backup...")
        
        try:
            backup_database(db_path)
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    @staticmethod
    def cleanup_old_sessions() -> int:
        """Очистить старые сессии"""
        from models import Session
        from sqlalchemy import and_
        
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_sessions = Session.query.filter(
            Session.created_at < cutoff_date
        ).delete()
        
        logger.info(f"Deleted {old_sessions} old sessions")
        return old_sessions
    
    @staticmethod
    def clear_cache() -> bool:
        """Очистить кэш"""
        from flask import current_app
        
        cache = current_app.extensions.get('cache')
        if cache:
            cache.clear()
            logger.info("Cache cleared")
            return True
        return False
    
    @staticmethod
    def generate_reports() -> dict:
        """Генерировать отчеты"""
        logger.info("Generating reports...")
        
        reports = {
            'timestamp': datetime.utcnow().isoformat(),
            'users_count': 0,  # Получить из БД
            'sessions_count': 0,  # Получить из БД
            'errors_count': 0  # Получить из логов
        }
        
        logger.info("Reports generated successfully")
        return reports
