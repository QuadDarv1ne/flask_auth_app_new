"""
Advanced Performance Monitoring - Real-time dashboards, alerts
"""
import time
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger('flask_auth_app.advanced_monitoring')


class PerformanceMetricsCollector:
    """Сбор продвинутых метрик производительности"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.lock = threading.Lock()
        self.thresholds = {
            'response_time': 1.0,  # секунды
            'error_rate': 0.05,    # 5%
            'cpu_usage': 80,       # %
            'memory_usage': 80     # %
        }
    
    def record_metric(self, metric_name: str, value: float, tags: dict = None):
        """Записать метрику"""
        with self.lock:
            metric_entry = {
                'timestamp': datetime.utcnow(),
                'value': value,
                'tags': tags or {}
            }
            self.metrics[metric_name].append(metric_entry)
    
    def get_metric_stats(self, metric_name: str, time_window: int = 300) -> Dict:
        """Получить статистику по метрике"""
        with self.lock:
            if metric_name not in self.metrics:
                return {}
            
            cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
            recent_metrics = [
                m for m in self.metrics[metric_name]
                if m['timestamp'] > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            values = [m['value'] for m in recent_metrics]
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99),
                'last_value': values[-1] if values else None
            }
    
    def check_thresholds(self) -> List[Dict]:
        """Проверить пороги и вернуть нарушения"""
        violations = []
        
        for metric_name, threshold in self.thresholds.items():
            stats = self.get_metric_stats(metric_name)
            
            if stats and stats.get('avg', 0) > threshold:
                violations.append({
                    'metric': metric_name,
                    'threshold': threshold,
                    'current': stats['avg'],
                    'timestamp': datetime.utcnow()
                })
        
        return violations
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Вычислить перцентиль"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_metrics_summary(self) -> Dict:
        """Получить сводку по всем метрикам"""
        summary = {}
        
        with self.lock:
            for metric_name in self.metrics.keys():
                stats = self.get_metric_stats(metric_name)
                if stats:
                    summary[metric_name] = stats
        
        return summary
    
    def cleanup_old_metrics(self, retention_hours: int = 24):
        """Удалить старые метрики"""
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        
        with self.lock:
            for metric_name in self.metrics:
                self.metrics[metric_name] = [
                    m for m in self.metrics[metric_name]
                    if m['timestamp'] > cutoff_time
                ]


class AlertSystem:
    """Система алертов"""
    
    def __init__(self):
        self.alerts = []
        self.alert_handlers = []
    
    def register_handler(self, handler):
        """Зарегистрировать обработчик алертов"""
        self.alert_handlers.append(handler)
    
    def trigger_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        data: dict = None
    ):
        """Создать алерт"""
        alert = {
            'id': len(self.alerts),
            'type': alert_type,
            'severity': severity,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow(),
            'acknowledged': False
        }
        
        self.alerts.append(alert)
        
        # Вызываем все обработчики
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def acknowledge_alert(self, alert_id: int):
        """Отметить алерт как прочитанный"""
        if 0 <= alert_id < len(self.alerts):
            self.alerts[alert_id]['acknowledged'] = True
    
    def get_active_alerts(self) -> List[Dict]:
        """Получить активные алерты"""
        return [a for a in self.alerts if not a['acknowledged']]
    
    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        """Получить последние алерты"""
        return self.alerts[-limit:]


class AnomalyDetection:
    """Обнаружение аномалий"""
    
    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity
        self.baselines = {}
    
    def set_baseline(self, metric_name: str, baseline_value: float):
        """Установить базовое значение"""
        self.baselines[metric_name] = baseline_value
    
    def detect_anomaly(self, metric_name: str, current_value: float) -> bool:
        """Обнаружить аномалию используя Z-score"""
        if metric_name not in self.baselines:
            return False
        
        baseline = self.baselines[metric_name]
        
        # Z-score = (value - mean) / std
        # Если |Z-score| > sensitivity, это аномалия
        deviation = abs(current_value - baseline)
        z_score = deviation / (baseline * 0.1 + 0.001)  # Примерное std
        
        return z_score > self.sensitivity
    
    def get_anomaly_severity(self, metric_name: str, current_value: float) -> str:
        """Получить серьезность аномалии"""
        if metric_name not in self.baselines:
            return 'unknown'
        
        baseline = self.baselines[metric_name]
        deviation_percent = abs(current_value - baseline) / baseline * 100
        
        if deviation_percent > 50:
            return 'critical'
        elif deviation_percent > 30:
            return 'warning'
        else:
            return 'info'


class DashboardData:
    """Данные для отображения на дашборде"""
    
    def __init__(self, metrics_collector, alert_system):
        self.metrics = metrics_collector
        self.alerts = alert_system
    
    def get_dashboard_data(self) -> Dict:
        """Получить все данные для дашборда"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': self.metrics.get_all_metrics_summary(),
            'active_alerts': self.alerts.get_active_alerts(),
            'recent_alerts': self.alerts.get_recent_alerts(limit=20),
            'health_status': self._get_health_status(),
            'recommendations': self._get_recommendations()
        }
    
    def _get_health_status(self) -> str:
        """Получить статус здоровья системы"""
        active_alerts = self.alerts.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a['severity'] == 'critical']
        
        if critical_alerts:
            return 'critical'
        elif len(active_alerts) > 5:
            return 'warning'
        else:
            return 'healthy'
    
    def _get_recommendations(self) -> List[str]:
        """Получить рекомендации"""
        recommendations = []
        violations = self.metrics.check_thresholds()
        
        for violation in violations:
            if violation['metric'] == 'response_time':
                recommendations.append("Оптимизируйте запросы к БД")
            elif violation['metric'] == 'error_rate':
                recommendations.append("Проверьте ошибки в логах")
            elif violation['metric'] == 'cpu_usage':
                recommendations.append("Увеличьте ресурсы сервера")
            elif violation['metric'] == 'memory_usage':
                recommendations.append("Оптимизируйте использование памяти")
        
        return recommendations


class LoadTesting:
    """Инструменты для нагрузочного тестирования"""
    
    @staticmethod
    def simulate_traffic(
        url: str,
        requests_count: int = 100,
        concurrent: int = 10
    ) -> Dict:
        """Симулировать трафик"""
        import requests
        import concurrent.futures
        
        results = {
            'total_requests': requests_count,
            'successful': 0,
            'failed': 0,
            'response_times': [],
            'errors': []
        }
        
        def make_request():
            try:
                start = time.time()
                response = requests.get(url, timeout=10)
                duration = time.time() - start
                
                results['response_times'].append(duration)
                
                if response.status_code == 200:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(requests_count)]
            concurrent.futures.wait(futures)
        
        # Вычисляем статистику
        if results['response_times']:
            results['avg_time'] = sum(results['response_times']) / len(results['response_times'])
            results['min_time'] = min(results['response_times'])
            results['max_time'] = max(results['response_times'])
            results['success_rate'] = results['successful'] / requests_count
        
        return results


class CapacityPlanning:
    """Планирование емкости"""
    
    @staticmethod
    def predict_resource_needs(
        current_users: int,
        growth_rate: float,
        months: int = 12
    ) -> Dict:
        """Предсказать потребность в ресурсах"""
        predictions = []
        
        for month in range(1, months + 1):
            projected_users = int(current_users * ((1 + growth_rate) ** month))
            
            # Примерные требования: 1 ядро на 1000 пользователей
            cpu_cores = max(2, int(projected_users / 1000) + 1)
            
            # Примерно 512MB на 1000 пользователей + базовое
            memory_mb = 1024 + int(projected_users / 1000) * 512
            
            # Примерно 10GB на 1000 пользователей
            storage_gb = 50 + int(projected_users / 1000) * 10
            
            predictions.append({
                'month': month,
                'projected_users': projected_users,
                'cpu_cores': cpu_cores,
                'memory_mb': memory_mb,
                'storage_gb': storage_gb
            })
        
        return {
            'current_users': current_users,
            'growth_rate': f"{growth_rate * 100:.1f}%",
            'predictions': predictions
        }
