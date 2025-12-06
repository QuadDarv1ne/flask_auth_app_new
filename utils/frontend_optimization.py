"""
Frontend Optimization - Asset bundling, lazy loading, critical path
"""
import json
import hashlib
from typing import Dict, List, Set
import logging

logger = logging.getLogger('flask_auth_app.frontend_optimization')


class CriticalPathAnalysis:
    """Анализ критического пути загрузки"""
    
    def __init__(self):
        self.critical_resources = {
            'html': [],
            'css': [],
            'js': [],
            'fonts': []
        }
        self.total_size = 0
    
    def add_resource(self, resource_type: str, filename: str, size: int):
        """Добавить ресурс"""
        if resource_type in self.critical_resources:
            self.critical_resources[resource_type].append({
                'name': filename,
                'size': size
            })
            self.total_size += size
    
    def get_optimization_recommendations(self) -> List[str]:
        """Получить рекомендации по оптимизации"""
        recommendations = []
        
        # Анализируем размеры
        css_size = sum(r['size'] for r in self.critical_resources['css'])
        js_size = sum(r['size'] for r in self.critical_resources['js'])
        
        if css_size > 100 * 1024:
            recommendations.append("CSS файлы превышают 100KB - рассмотрите минификацию")
        
        if js_size > 300 * 1024:
            recommendations.append("JS файлы превышают 300KB - рассмотрите code splitting")
        
        if len(self.critical_resources['fonts']) > 3:
            recommendations.append("Слишком много шрифтов - ограничьте до 2-3")
        
        return recommendations


class AssetOptimization:
    """Оптимизация ассетов"""
    
    @staticmethod
    def generate_hash(content: str) -> str:
        """Генерировать хеш контента для cache busting"""
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    @staticmethod
    def inline_critical_css(critical_css: str) -> str:
        """Инлайнить критический CSS"""
        return f"<style>{critical_css}</style>"
    
    @staticmethod
    def defer_script(src: str, async_load: bool = True) -> str:
        """Отложить загрузку скрипта"""
        if async_load:
            return f'<script src="{src}" async></script>'
        else:
            return f'<script src="{src}" defer></script>'
    
    @staticmethod
    def lazy_load_image(src: str, alt: str = "") -> str:
        """Ленивая загрузка изображения"""
        return f'<img src="data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg"%3E%3C/svg%3E" data-src="{src}" alt="{alt}" loading="lazy">'
    
    @staticmethod
    def generate_asset_manifest(assets: Dict[str, List[str]]) -> str:
        """Генерировать манифест ассетов"""
        manifest = {}
        
        for asset_type, files in assets.items():
            manifest[asset_type] = {
                'files': files,
                'count': len(files)
            }
        
        return json.dumps(manifest, indent=2)


class BundleOptimization:
    """Оптимизация бундлов"""
    
    def __init__(self):
        self.bundles = {}
    
    def create_bundle(
        self,
        name: str,
        files: List[str],
        type: str = 'js',
        target_size: int = None
    ):
        """Создать бундл"""
        bundle = {
            'name': name,
            'files': files,
            'type': type,
            'count': len(files),
            'needs_split': False
        }
        
        # Проверяем размер
        if target_size and len(files) > target_size:
            bundle['needs_split'] = True
        
        self.bundles[name] = bundle
        logger.info(f"Bundle created: {name} with {len(files)} files")
    
    def get_bundle_url(self, bundle_name: str) -> str:
        """Получить URL бундла"""
        if bundle_name not in self.bundles:
            return ""
        
        return f"/static/bundles/{bundle_name}.bundle.js"
    
    def get_all_bundles(self) -> Dict:
        """Получить все бундлы"""
        return self.bundles
    
    def needs_splitting(self) -> List[str]:
        """Получить бундлы, которые нужно разделить"""
        return [
            name for name, bundle in self.bundles.items()
            if bundle['needs_split']
        ]


class LazyLoadingStrategy:
    """Стратегия ленивой загрузки"""
    
    STRATEGIES = {
        'intersection_observer': 'IntersectionObserver API',
        'scroll_event': 'Scroll event listener',
        'route_based': 'Load on route change',
        'viewport_based': 'Load when in viewport'
    }
    
    def __init__(self, strategy: str = 'intersection_observer'):
        self.strategy = strategy
    
    def get_script(self) -> str:
        """Получить скрипт для реализации стратегии"""
        if self.strategy == 'intersection_observer':
            return self._get_intersection_observer_script()
        elif self.strategy == 'scroll_event':
            return self._get_scroll_event_script()
        elif self.strategy == 'route_based':
            return self._get_route_based_script()
        else:
            return ""
    
    def _get_intersection_observer_script(self) -> str:
        """Скрипт для IntersectionObserver"""
        return """
<script>
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.add('loaded');
            observer.unobserve(img);
        }
    });
});

document.querySelectorAll('img[data-src]').forEach(img => imageObserver.observe(img));
</script>
"""
    
    def _get_scroll_event_script(self) -> str:
        """Скрипт для scroll события"""
        return """
<script>
let lazyImages = document.querySelectorAll('img[data-src]');

function lazyLoad() {
    lazyImages.forEach(img => {
        if (img.getBoundingClientRect().top <= window.innerHeight) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        }
    });
    lazyImages = document.querySelectorAll('img[data-src]');
    if (lazyImages.length === 0) {
        document.removeEventListener('scroll', lazyLoad);
    }
}

window.addEventListener('scroll', lazyLoad);
lazyLoad();
</script>
"""
    
    def _get_route_based_script(self) -> str:
        """Скрипт для загрузки по маршрутам"""
        return """
<script>
window.addEventListener('load', () => {
    // Load non-critical resources after page load
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/css/secondary.css';
    document.head.appendChild(link);
    
    const script = document.createElement('script');
    script.src = '/static/js/secondary.js';
    document.body.appendChild(script);
});
</script>
"""


class PrefetchingStrategy:
    """Стратегия предзагрузки ресурсов"""
    
    @staticmethod
    def prefetch_link(href: str, rel: str = 'prefetch') -> str:
        """Генерировать prefetch тег"""
        return f'<link rel="{rel}" href="{href}">'
    
    @staticmethod
    def prefetch_dns(domain: str) -> str:
        """DNS prefetch"""
        return f'<link rel="dns-prefetch" href="//{domain}">'
    
    @staticmethod
    def preconnect(domain: str) -> str:
        """Preconnect к серверу"""
        return f'<link rel="preconnect" href="//{domain}">'
    
    @staticmethod
    def preload(href: str, as_type: str) -> str:
        """Preload критических ресурсов"""
        return f'<link rel="preload" href="{href}" as="{as_type}">'
    
    @staticmethod
    def generate_prefetch_headers(resources: List[Dict]) -> List[str]:
        """Генерировать Link заголовки для prefetch"""
        headers = []
        
        for resource in resources:
            if resource['type'] == 'dns':
                headers.append(PrefetchingStrategy.prefetch_dns(resource['domain']))
            elif resource['type'] == 'preconnect':
                headers.append(PrefetchingStrategy.preconnect(resource['domain']))
            elif resource['type'] == 'preload':
                headers.append(
                    PrefetchingStrategy.preload(resource['href'], resource['as'])
                )
            elif resource['type'] == 'prefetch':
                headers.append(PrefetchingStrategy.prefetch_link(resource['href']))
        
        return headers


class PerformanceMetrics:
    """Метрики производительности фронтенда"""
    
    CORE_WEB_VITALS = {
        'LCP': {'target': 2.5, 'unit': 's'},  # Largest Contentful Paint
        'FID': {'target': 0.1, 'unit': 's'},  # First Input Delay
        'CLS': {'target': 0.1, 'unit': ''},   # Cumulative Layout Shift
        'TTFB': {'target': 0.6, 'unit': 's'}, # Time to First Byte
        'FCP': {'target': 1.8, 'unit': 's'},  # First Contentful Paint
    }
    
    @staticmethod
    def get_performance_script() -> str:
        """Получить скрипт для сбора метрик производительности"""
        return """
<script>
// Core Web Vitals
window.addEventListener('load', () => {
    // LCP - Largest Contentful Paint
    const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        console.log('LCP:', lastEntry.renderTime || lastEntry.loadTime);
    });
    observer.observe({entryTypes: ['largest-contentful-paint']});
    
    // FID - First Input Delay (via web-vitals library)
    // CLS - Cumulative Layout Shift
    const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
                console.log('CLS:', entry.value);
            }
        }
    });
    clsObserver.observe({type: 'layout-shift', buffered: true});
});

// TTFB - Time to First Byte
const ttfb = performance.timing.responseStart - performance.timing.navigationStart;
console.log('TTFB:', ttfb);

// FCP - First Contentful Paint
const fcp = performance.getEntriesByName('first-contentful-paint')[0];
console.log('FCP:', fcp?.startTime);
</script>
"""
    
    @staticmethod
    def get_audit_recommendations() -> Dict[str, List[str]]:
        """Получить рекомендации по аудиту"""
        return {
            'LCP': [
                'Минимизируйте критические ресурсы',
                'Используйте CDN',
                'Загружайте шрифты асинхронно',
                'Кэшируйте на уровне браузера'
            ],
            'FID': [
                'Разделите длинные задачи JavaScript',
                'Используйте Web Workers',
                'Оптимизируйте код JavaScript'
            ],
            'CLS': [
                'Установите размеры для изображений и видео',
                'Избегайте внедрения контента в начало DOM',
                'Используйте transform для анимаций'
            ]
        }
