# Flask Auth App - API Документация

## Обзор

Flask Auth App предоставляет RESTful API для управления аутентификацией, профилями пользователей и двухфакторной аутентификацией.

## Базовая информация

- **Base URL:** `http://localhost:5000`
- **Content-Type:** `application/json`
- **Authentication:** JWT токен в заголовке `Authorization: Bearer <token>`

## Эндпоинты

### Аутентификация

#### Регистрация пользователя
```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Ответ успеха (201):**
```json
{
  "message": "Регистрация успешна",
  "user_id": 1,
  "username": "john_doe"
}
```

**Ошибки:**
- 400 - Некорректные данные
- 409 - Пользователь уже существует

---

#### Вход в систему
```http
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Ответ успеха (200):**
```json
{
  "message": "Вход успешен",
  "user_id": 1,
  "username": "john_doe",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

#### Выход из системы
```http
POST /auth/logout
Authorization: Bearer <token>
```

**Ответ успеха (200):**
```json
{
  "message": "Вы успешно вышли"
}
```

---

### Профиль пользователя

#### Получение профиля
```http
GET /api/profile
Authorization: Bearer <token>
```

**Ответ успеха (200):**
```json
{
  "user_id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2025-12-05T10:30:00",
  "last_login": "2025-12-05T15:45:00",
  "two_factor_enabled": false
}
```

---

#### Обновление профиля
```http
PUT /api/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "john_doe_new",
  "email": "newemail@example.com"
}
```

**Ответ успеха (200):**
```json
{
  "message": "Профиль обновлен",
  "profile": {
    "username": "john_doe_new",
    "email": "newemail@example.com"
  }
}
```

---

#### Смена пароля
```http
POST /api/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Ответ успеха (200):**
```json
{
  "message": "Пароль успешно изменен"
}
```

---

### Двухфакторная аутентификация (2FA)

#### Включение 2FA
```http
POST /api/2fa/setup
Authorization: Bearer <token>
```

**Ответ успеха (200):**
```json
{
  "qr_code": "data:image/png;base64,iVBORw0K...",
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "message": "Отсканируйте QR-код с помощью приложения аутентификатора"
}
```

---

#### Подтверждение 2FA
```http
POST /api/2fa/confirm
Authorization: Bearer <token>
Content-Type: application/json

{
  "token": "123456"
}
```

**Ответ успеха (200):**
```json
{
  "message": "2FA успешно включена"
}
```

---

#### Отключение 2FA
```http
DELETE /api/2fa/disable
Authorization: Bearer <token>
Content-Type: application/json

{
  "password": "CurrentPassword123!"
}
```

**Ответ успеха (200):**
```json
{
  "message": "2FA успешно отключена"
}
```

---

### Health & Metrics

#### Проверка статуса приложения
```http
GET /health
```

**Ответ успеха (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-05T15:45:00",
  "version": "1.0.0"
}
```

---

#### Метрики Prometheus
```http
GET /metrics
```

**Ответ:** Метрики в формате Prometheus

---

## Коды ошибок

| Код | Описание |
|-----|---------|
| 200 | OK - Успешный запрос |
| 201 | Created - Ресурс создан |
| 400 | Bad Request - Некорректные данные |
| 401 | Unauthorized - Требуется аутентификация |
| 403 | Forbidden - Доступ запрещен |
| 404 | Not Found - Ресурс не найден |
| 409 | Conflict - Конфликт (например, пользователь уже существует) |
| 500 | Internal Server Error - Ошибка сервера |

---

## Примеры использования

### cURL

#### Регистрация
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

#### Вход
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

#### Получение профиля
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:5000"

# Регистрация
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
})

# Вход
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "john@example.com",
    "password": "SecurePassword123!"
})
token = response.json()["token"]

# Получение профиля
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:5000";

// Регистрация
fetch(`${BASE_URL}/auth/register`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'john_doe',
    email: 'john@example.com',
    password: 'SecurePassword123!'
  })
})
.then(r => r.json())
.then(d => console.log(d));

// Вход
fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'john@example.com',
    password: 'SecurePassword123!'
  })
})
.then(r => r.json())
.then(d => {
  const token = d.token;
  
  // Получение профиля
  return fetch(`${BASE_URL}/api/profile`, {
    headers: {'Authorization': `Bearer ${token}`}
  });
})
.then(r => r.json())
.then(d => console.log(d));
```

---

## Rate Limiting

API ограничивает количество запросов для предотвращения злоупотреблений:

- **Аутентификация:** 5 запросов в минуту
- **Профиль:** 30 запросов в минуту
- **2FA:** 10 запросов в минуту

---

## Безопасность

- Все пароли хешируются с использованием PBKDF2
- JWT токены имеют TTL 24 часа
- HTTPS обязателен в production
- CORS ограничивается доверенными источниками
- CSRF защита для всех изменяющих операций

---

## Версионирование

API использует версионирование в пути: `/api/v1/...`

Текущая версия: **v1**

---

## Поддержка

Для технической поддержки: [support@flaskauth.local](mailto:support@flaskauth.local)

Документация: [https://docs.flaskauth.local](https://docs.flaskauth.local)
