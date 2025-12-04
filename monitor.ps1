# Скрипт мониторинга Flask Auth App
# Запускает приложение и отображает статистику в реальном времени

Write-Host "="*70 -ForegroundColor Cyan
Write-Host "🔍 Мониторинг Flask Auth App" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# Функция для красивого вывода
function Show-Status {
    param(
        [string]$Label,
        [string]$Value,
        [string]$Color = "White"
    )
    Write-Host "$Label`: " -NoNewline -ForegroundColor Yellow
    Write-Host $Value -ForegroundColor $Color
}

# Проверка запущен ли сервер
$serverRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $serverRunning = $true
    }
} catch {
    $serverRunning = $false
}

Write-Host "📊 Статус системы" -ForegroundColor Cyan
Write-Host "-"*70

if ($serverRunning) {
    Show-Status "Сервер" "✅ Работает" "Green"
    Show-Status "URL" "http://localhost:5000" "Cyan"
} else {
    Show-Status "Сервер" "❌ Не запущен" "Red"
}

# Проверка файлов проекта
$filesExist = @{
    "app.py" = Test-Path "app.py"
    "config.py" = Test-Path "config.py"
    "models.py" = Test-Path "models.py"
    "forms.py" = Test-Path "forms.py"
    "requirements.txt" = Test-Path "requirements.txt"
}

Write-Host ""
Write-Host "📁 Файлы проекта" -ForegroundColor Cyan
Write-Host "-"*70

foreach ($file in $filesExist.Keys | Sort-Object) {
    $status = if ($filesExist[$file]) { "✅" } else { "❌" }
    Show-Status $file $status $(if ($filesExist[$file]) { "Green" } else { "Red" })
}

# Проверка логов
Write-Host ""
Write-Host "📝 Логирование" -ForegroundColor Cyan
Write-Host "-"*70

if (Test-Path "logs/flask_auth.log") {
    $logSize = (Get-Item "logs/flask_auth.log").Length
    $logLines = (Get-Content "logs/flask_auth.log").Count
    Show-Status "Лог-файл" "✅ Существует" "Green"
    Show-Status "Размер" "$([math]::Round($logSize/1KB, 2)) KB" "White"
    Show-Status "Строк" "$logLines" "White"
    
    # Последние записи
    Write-Host ""
    Write-Host "📋 Последние 5 записей в логе:" -ForegroundColor Yellow
    Get-Content "logs/flask_auth.log" -Tail 5 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
} else {
    Show-Status "Лог-файл" "⚠️ Не создан (debug режим)" "Yellow"
}

# Проверка базы данных
Write-Host ""
Write-Host "💾 База данных" -ForegroundColor Cyan
Write-Host "-"*70

if (Test-Path "instance/users.db") {
    $dbSize = (Get-Item "instance/users.db").Length
    Show-Status "БД файл" "✅ Существует" "Green"
    Show-Status "Размер" "$([math]::Round($dbSize/1KB, 2)) KB" "White"
} else {
    Show-Status "БД файл" "⚠️ Не создана" "Yellow"
}

# Тесты
Write-Host ""
Write-Host "🧪 Тестирование" -ForegroundColor Cyan
Write-Host "-"*70

if (Test-Path "tests") {
    $testFiles = (Get-ChildItem -Path "tests" -Filter "test_*.py").Count
    Show-Status "Тест-файлов" "$testFiles" "Green"
    
    # Запуск быстрой проверки
    Write-Host ""
    Write-Host "▶️ Запуск быстрой проверки тестов..." -ForegroundColor Yellow
    $testResult = python -m pytest tests/ -q --tb=no 2>&1
    if ($LASTEXITCODE -eq 0) {
        Show-Status "Результат" "✅ Все тесты пройдены" "Green"
    } else {
        Show-Status "Результат" "❌ Есть ошибки" "Red"
    }
}

# Информация о процессах
Write-Host ""
Write-Host "⚙️ Процессы Python" -ForegroundColor Cyan
Write-Host "-"*70

$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Show-Status "Python процессов" "$($pythonProcesses.Count)" "Green"
    foreach ($proc in $pythonProcesses) {
        $memory = [math]::Round($proc.WorkingSet64 / 1MB, 2)
        Write-Host "  PID: $($proc.Id) | Память: $memory MB" -ForegroundColor Gray
    }
} else {
    Show-Status "Python процессов" "0" "Yellow"
}

# Советы
Write-Host ""
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "💡 Полезные команды:" -ForegroundColor Yellow
Write-Host "  - Просмотр логов:     Get-Content logs/flask_auth.log -Tail 20 -Wait" -ForegroundColor Gray
Write-Host "  - Запуск тестов:      python -m pytest tests/ -v" -ForegroundColor Gray
Write-Host "  - Покрытие кода:      python -m pytest tests/ --cov=. --cov-report=html" -ForegroundColor Gray
Write-Host "  - Остановить сервер:  Ctrl+C в терминале сервера" -ForegroundColor Gray
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# Живой мониторинг (опционально)
$monitor = Read-Host "Включить живой мониторинг запросов? (y/n)"
if ($monitor -eq 'y') {
    Write-Host ""
    Write-Host "🔴 LIVE: Мониторинг запросов (Ctrl+C для выхода)" -ForegroundColor Red
    Write-Host "-"*70
    
    if (Test-Path "logs/flask_auth.log") {
        Get-Content "logs/flask_auth.log" -Wait -Tail 0 | ForEach-Object {
            $timestamp = Get-Date -Format "HH:mm:ss"
            Write-Host "[$timestamp] $_" -ForegroundColor Cyan
        }
    } else {
        Write-Host "Лог-файл не найден. Запросы будут отображаться в консоли сервера." -ForegroundColor Yellow
    }
}
