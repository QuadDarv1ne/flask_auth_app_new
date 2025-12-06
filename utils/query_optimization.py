"""
Database Query Optimization - Query Planning, Indexing, Statistics
"""
import time
import logging
from functools import wraps
from typing import Any, List, Dict
from sqlalchemy import event, text, func
from sqlalchemy.orm import Query

logger = logging.getLogger('flask_auth_app.query_optimizer')


class QueryStats:
    """Статистика выполнения запросов"""
    
    def __init__(self):
        self.queries = []
        self.total_time = 0
        self.slow_queries = []
        self.query_counts = {}
    
    def add_query(self, query: str, duration: float):
        """Добавить статистику запроса"""
        self.queries.append({
            'query': query,
            'duration': duration,
            'timestamp': time.time()
        })
        
        self.total_time += duration
        
        # Отслеживание медленных запросов (> 100ms)
        if duration > 0.1:
            self.slow_queries.append({
                'query': query,
                'duration': duration
            })
        
        # Подсчёт количества запросов
        query_type = query.split()[0].upper()
        self.query_counts[query_type] = self.query_counts.get(query_type, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку по запросам"""
        return {
            'total_queries': len(self.queries),
            'total_time': self.total_time,
            'avg_time': self.total_time / len(self.queries) if self.queries else 0,
            'slow_queries_count': len(self.slow_queries),
            'query_types': self.query_counts
        }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """Получить самые медленные запросы"""
        return sorted(
            self.slow_queries,
            key=lambda x: x['duration'],
            reverse=True
        )[:limit]
    
    def reset(self):
        """Сбросить статистику"""
        self.__init__()


class QueryOptimizer:
    """Оптимизация запросов к БД"""
    
    def __init__(self, db):
        self.db = db
        self.stats = QueryStats()
    
    def setup_query_monitoring(self):
        """Настроить мониторинг запросов"""
        @event.listens_for(self.db.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(self.db.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop(-1)
            self.stats.add_query(statement, total_time)
            
            if total_time > 0.1:
                logger.warning(f"Slow query ({total_time:.3f}s): {statement[:100]}")
    
    def get_execution_plan(self, query: str) -> Dict:
        """Получить план выполнения запроса"""
        try:
            result = self.db.session.execute(text(f"EXPLAIN {query}"))
            plan = [row for row in result]
            return {'plan': plan}
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_table(self, table_name: str):
        """Анализировать таблицу для оптимизации"""
        try:
            self.db.session.execute(text(f"ANALYZE {table_name}"))
            self.db.session.commit()
            logger.info(f"Analyzed table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
    
    def create_index(self, table_name: str, column_name: str, name: str = None):
        """Создать индекс на столбце"""
        index_name = name or f"idx_{table_name}_{column_name}"
        
        try:
            self.db.session.execute(
                text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
            )
            self.db.session.commit()
            logger.info(f"Created index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
    
    def create_composite_index(self, table_name: str, columns: List[str], name: str = None):
        """Создать композитный индекс"""
        index_name = name or f"idx_{table_name}_{'_'.join(columns)}"
        columns_str = ', '.join(columns)
        
        try:
            self.db.session.execute(
                text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns_str})")
            )
            self.db.session.commit()
            logger.info(f"Created composite index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create composite index: {e}")


class EagerLoading:
    """Стратегии eager loading для предотвращения N+1 запросов"""
    
    @staticmethod
    def with_relationships(query: Query, *relationships):
        """Eager load отношений"""
        from sqlalchemy.orm import joinedload
        
        for relationship in relationships:
            query = query.options(joinedload(relationship))
        
        return query
    
    @staticmethod
    def with_subquery_loading(query: Query, *relationships):
        """Subquery loading для сложных отношений"""
        from sqlalchemy.orm import subqueryload
        
        for relationship in relationships:
            query = query.options(subqueryload(relationship))
        
        return query


def optimize_query(func):
    """Декоратор для оптимизации запросов"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        
        optimizer = current_app.extensions.get('query_optimizer')
        
        if optimizer:
            # Сбрасываем статистику перед запросом
            start_stats = len(optimizer.stats.queries)
            
            result = func(*args, **kwargs)
            
            # Логируем количество запросов
            end_stats = len(optimizer.stats.queries)
            query_count = end_stats - start_stats
            
            if query_count > 5:
                logger.warning(f"Function {func.__name__} executed {query_count} queries")
            
            return result
        else:
            return func(*args, **kwargs)
    
    return decorated_function


class BatchOperations:
    """Пакетные операции для оптимизации БД"""
    
    @staticmethod
    def batch_insert(db, model_class, data_list: List[Dict], batch_size: int = 1000):
        """Пакетная вставка данных"""
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            objects = [model_class(**data) for data in batch]
            db.session.add_all(objects)
            db.session.commit()
            logger.info(f"Inserted batch: {len(batch)} records")
    
    @staticmethod
    def batch_update(db, model_class, updates: List[Dict]):
        """Пакетное обновление данных"""
        for update in updates:
            obj_id = update.pop('id')
            db.session.query(model_class).filter_by(id=obj_id).update(update)
        
        db.session.commit()
        logger.info(f"Updated {len(updates)} records")
    
    @staticmethod
    def batch_delete(db, model_class, ids: List[int], batch_size: int = 1000):
        """Пакетное удаление данных"""
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            db.session.query(model_class).filter(model_class.id.in_(batch)).delete()
            db.session.commit()
            logger.info(f"Deleted batch: {len(batch)} records")


class ConnectionPooling:
    """Оптимизация пула соединений"""
    
    @staticmethod
    def get_pool_config(app):
        """Получить оптимальную конфигурацию пула"""
        return {
            'pool_size': app.config.get('SQLALCHEMY_POOL_SIZE', 10),
            'max_overflow': app.config.get('SQLALCHEMY_MAX_OVERFLOW', 20),
            'pool_timeout': app.config.get('SQLALCHEMY_POOL_TIMEOUT', 30),
            'pool_recycle': app.config.get('SQLALCHEMY_POOL_RECYCLE', 3600),
            'pool_pre_ping': app.config.get('SQLALCHEMY_POOL_PRE_PING', True),
        }
    
    @staticmethod
    def get_connection_stats(engine):
        """Получить статистику пула соединений"""
        pool = engine.pool
        
        return {
            'checkedout': pool.checkedout(),
            'size': pool.size(),
            'checked_in': pool.size() - pool.checkedout()
        }
