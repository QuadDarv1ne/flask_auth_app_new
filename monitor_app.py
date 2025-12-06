"""
Скрипт мониторинга Flask Auth App
Проверяет метрики, здоровье приложения и производительность
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any
import sys

# Цвета для вывода
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class AppMonitor:
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 5
    
    def get_health(self) -> Dict[str, Any]:
        """Получить статус здоровья приложения"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"{RED}✗ Health check failed: {e}{RESET}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получить метрики приложения"""
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"{RED}✗ Metrics request failed: {e}{RESET}")
            return None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Получить статус API"""
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"{RED}✗ API status request failed: {e}{RESET}")
            return None
    
    def print_header(self, title: str):
        """Печать заголовка секции"""
        print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
        print(f"{BLUE}{BOLD}  {title}{RESET}")
        print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")
    
    def print_status(self, status: str, is_healthy: bool = True):
        """Печать статуса"""
        color = GREEN if is_healthy else RED
        symbol = "[OK]" if is_healthy else "[ERROR]"
        print(f"{color}{symbol} {status}{RESET}")
    
    def format_percentage(self, value: float, threshold: float = None) -> str:
        """Форматировать процент с цветом"""
        if threshold and value > threshold:
            return f"{RED}{value:.1f}%{RESET}"
        elif value > 75:
            return f"{YELLOW}{value:.1f}%{RESET}"
        else:
            return f"{GREEN}{value:.1f}%{RESET}"
    
    def monitor(self):
        """Основной цикл мониторинга"""
        try:
            # Заголовок
            print(f"\n{BOLD}Flask Auth App - Мониторинг{RESET}")
            print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"URL: {self.base_url}\n")
            
            # Проверка доступности
            try:
                response = self.session.get(self.base_url, timeout=2)
                if response.status_code == 200:
                    self.print_status("[OK] Приложение доступно", True)
                else:
                    self.print_status(f"Приложение вернуло код {response.status_code}", False)
            except:
                self.print_status("Приложение недоступно", False)
                return
            
            # Health Check
            self.print_header("🏥 HEALTH CHECK")
            health = self.get_health()
            if health:
                overall_status = health.get('status', 'unknown')
                is_healthy = overall_status == 'healthy'
                
                status_color = GREEN if is_healthy else YELLOW if overall_status == 'degraded' else RED
                print(f"Статус: {status_color}{BOLD}{overall_status.upper()}{RESET}")
                
                db_status = health.get('database', 'unknown')
                print(f"БД: {GREEN if db_status == 'healthy' else RED}{db_status.upper()}{RESET}")
                
                redis_status = health.get('redis', 'unknown')
                print(f"Redis: {GREEN if redis_status == 'healthy' else RED}{redis_status.upper()}{RESET}")
                
                print(f"WebSocket соединений: {health.get('websocket_connections', 0)}")
            
            # Метрики приложения
            self.print_header("📊 МЕТРИКИ ПРИЛОЖЕНИЯ")
            metrics = self.get_metrics()
            if metrics:
                app_metrics = metrics.get('application', {})
                
                # Запросы
                requests_data = app_metrics.get('requests', {})
                print(f"{BOLD}Запросы:{RESET}")
                print(f"  Всего: {GREEN}{requests_data.get('total', 0)}{RESET}")
                print(f"  Средняя длительность: {requests_data.get('average_duration', 0):.3f}s")
                
                # Ошибки
                errors_data = app_metrics.get('errors', {})
                error_rate = errors_data.get('error_rate', 0)
                print(f"\n{BOLD}Ошибки:{RESET}")
                print(f"  Всего: {RED}{errors_data.get('total', 0)}{RESET}")
                print(f"  Процент ошибок: {self.format_percentage(error_rate, 5.0)}")
                
                # Кэш
                cache_data = app_metrics.get('cache', {})
                cache_hit_rate = cache_data.get('hit_rate', 0)
                print(f"\n{BOLD}Кэш:{RESET}")
                print(f"  Попадания: {cache_data.get('hits', 0)}")
                print(f"  Промахи: {cache_data.get('misses', 0)}")
                print(f"  Коэффициент попаданий: {self.format_percentage(cache_hit_rate)}")
                
                # Эндпоинты
                endpoints = app_metrics.get('endpoints', {})
                if endpoints:
                    print(f"\n{BOLD}Топ эндпоинты (по запросам):{RESET}")
                    top_endpoints = sorted(
                        endpoints.items(),
                        key=lambda x: x[1].get('requests', 0),
                        reverse=True
                    )[:5]
                    for endpoint, data in top_endpoints:
                        requests_count = data.get('requests', 0)
                        avg_time = data.get('average_duration', 0)
                        print(f"  {endpoint}: {requests_count} запросов, {avg_time:.3f}s avg")
            
            # Системные метрики
            self.print_header("💻 СИСТЕМНЫЕ МЕТРИКИ")
            if metrics:
                system_metrics = metrics.get('system', {})
                
                cpu_usage = system_metrics.get('cpu', 0)
                print(f"CPU Usage: {self.format_percentage(cpu_usage, 80.0)}")
                
                memory = system_metrics.get('memory', {})
                mem_percent = memory.get('percent', 0)
                mem_available = memory.get('available', 0)
                print(f"Память: {self.format_percentage(mem_percent, 80.0)} ({mem_available} MB свободно)")
                
                disk = system_metrics.get('disk', {})
                disk_percent = disk.get('percent', 0)
                print(f"Диск: {self.format_percentage(disk_percent, 90.0)}")
                
                processes = system_metrics.get('processes', 0)
                print(f"Процессы: {processes}")
            
            # API Статус
            self.print_header("🌐 API СТАТУС")
            api_status = self.get_api_status()
            if api_status:
                print(f"Version: {api_status.get('api_version', 'unknown')}")
                print(f"Status: {GREEN}{BOLD}{api_status.get('status', 'unknown').upper()}{RESET}")
            
            # Итог
            print(f"\n{BOLD}Последнее обновление:{RESET} {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"{RED}Ошибка при мониторинге: {e}{RESET}")
            import traceback
            traceback.print_exc()
    
    def continuous_monitor(self, interval: int = 10):
        """Непрерывный мониторинг"""
        print(f"\n{BOLD}Режим непрерывного мониторинга (интервал: {interval}s){RESET}")
        print(f"Нажмите Ctrl+C для выхода\n")
        
        try:
            while True:
                self.monitor()
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Мониторинг остановлен{RESET}")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flask Auth App Monitor')
    parser.add_argument('--url', default='http://127.0.0.1:5000', help='Application URL')
    parser.add_argument('--continuous', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=10, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    monitor = AppMonitor(args.url)
    
    if args.continuous:
        monitor.continuous_monitor(args.interval)
    else:
        monitor.monitor()


if __name__ == '__main__':
    main()
