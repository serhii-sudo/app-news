# 📰 APP-NEWS — Руководство по тестированию в Postman

> **Base URL:** `http://localhost:8000`

---

## 🗂 Структура API

| Префикс | Приложение |
|---|---|
| `/api/v1/auth/` | `accounts` — авторизация, профиль |
| `/api/v1/posts/` | `main` — посты, категории |

---

## 🔐 Настройка Postman — JWT авторизация

### Как передавать токен

После логина/регистрации вы получите `access` токен.  
Для защищённых эндпоинтов добавляйте его в запрос.

**Самый удобный способ через UI Postman:**
1. Откройте вкладку **Authorization** (находится под строкой ввода URL).
2. В выпадающем списке **Type** выберите **Bearer Token**.
3. В поле **Token** вставьте ваш `access_token`.
   *Postman сам добавит нужный заголовок `Authorization: Bearer ...` к запросу.*

**Ручной способ (через Headers):**
```
Headers:
  Authorization: Bearer <ваш_access_token>
```

**С использованием переменных:**
Создайте переменную окружения `{{access_token}}` и укажите её в поле Token или в Header:
```
Authorization: Bearer {{access_token}}
```

---

## 👤 Модуль `accounts` — `/api/v1/auth/`

---

### 1. Регистрация пользователя

| | |
|---|---|
| **Метод** | `POST` |
| **URL** | `http://localhost:8000/api/v1/auth/register/` |
| **Auth** | Не нужна |

**Body (JSON):**
```json
{
    "username": "john",
    "email": "john@example.com",
    "password": "MyPass123!",
    "password_confirm": "MyPass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Успешный ответ (201):**
```json
{
    "user": {
        "id": 1,
        "username": "john",
        "email": "john@example.com",
        "full_name": "John Doe",
        ...
    },
    "refresh": "eyJ...",
    "access": "eyJ...",
    "message": "User registered successfully"
}
```

> 💡 Скопируйте `access` и `refresh` токены — они нужны для следующих запросов.

**Частые ошибки:**
- `password_confirm` не совпадает → 400
- Email уже зарегистрирован → 400
- Слабый пароль → 400 (минимум 8 символов, нельзя только цифры)

---

### 2. Вход (Login)

| | |
|---|---|
| **Метод** | `POST` |
| **URL** | `http://localhost:8000/api/v1/auth/login/` |
| **Auth** | Не нужна |

**Body (JSON):**
```json
{
    "email": "john@example.com",
    "password": "MyPass123!"
}
```

**Успешный ответ (200):**
```json
{
    "user": { ... },
    "refresh": "eyJ...",
    "access": "eyJ...",
    "message": "User login successfully"
}
```

> 💡 **Логин производится по email**, не по username!

---

### 3. Обновление access-токена

| | |
|---|---|
| **Метод** | `POST` |
| **URL** | `http://localhost:8000/api/v1/auth/token/refresh/` |
| **Auth** | Не нужна |

**Body (JSON):**
```json
{
    "refresh": "eyJ..."
}
```

**Успешный ответ (200):**
```json
{
    "access": "eyJ..."
}
```

> Access-токен живёт недолго (обычно 5 минут). Как истечёт — обновляй через этот эндпоинт.

---

### 4. Профиль текущего пользователя (GET)

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/auth/profile/` |
| **Auth** | `Bearer <access_token>` |

**Успешный ответ (200):**
```json
{
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "avatar": null,
    "bio": "",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
    "posts_count": 3,
    "comments_count": 0
}
```

---

### 5. Обновление профиля (PATCH)

| | |
|---|---|
| **Метод** | `PATCH` |
| **URL** | `http://localhost:8000/api/v1/auth/profile/` |
| **Auth** | `Bearer <access_token>` |

**Body (JSON):**
```json
{
    "first_name": "Иван",
    "last_name": "Петров",
    "bio": "Пишу о технологиях"
}
```

> Обновлять можно частично (PATCH). Поля: `first_name`, `last_name`, `avatar`, `bio`.

---

### 6. Смена пароля

| | |
|---|---|
| **Метод** | `PUT` |
| **URL** | `http://localhost:8000/api/v1/auth/change-password/` |
| **Auth** | `Bearer <access_token>` |

**Body (JSON):**
```json
{
    "old_password": "MyPass123!",
    "new_password": "NewPass456!",
    "new_password_confirm": "NewPass456!"
}
```

**Успешный ответ (200):**
```json
{
    "message": "Password changed successfully"
}
```

---

### 7. Выход (Logout)

| | |
|---|---|
| **Метод** | `POST` |
| **URL** | `http://localhost:8000/api/v1/auth/logout/` |
| **Auth** | `Bearer <access_token>` |

**Body (JSON):**
```json
{
    "refresh_token": "eyJ..."
}
```

**Успешный ответ (200):**
```json
{
    "message": "Logout successful"
}
```

> Refresh-токен попадает в чёрный список и больше не работает. Нужно заново логиниться.

---

## 📁 Модуль `main` — `/api/v1/posts/`

---

### КАТЕГОРИИ

---

### 8. Список категорий

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/categories/` |
| **Auth** | Не нужна |

**Query параметры (опционально):**
| Параметр | Пример | Описание |
|---|---|---|
| `search` | `?search=спорт` | Поиск по name, description |
| `ordering` | `?ordering=name` или `?ordering=-name` | Сортировка |

**Успешный ответ (200):**
```json
[
    {
        "id": 1,
        "name": "Технологии",
        "slug": "tekhnologii",
        "description": "Статьи о технологиях",
        "posts_count": 5,
        "created_at": "2026-01-01T00:00:00Z"
    }
]
```

---

### 9. Создать категорию

| | |
|---|---|
| **Метод** | `POST` |
| **URL** | `http://localhost:8000/api/v1/posts/categories/` |
| **Auth** | Вкладка **Authorization** -> Bearer Token |

**Body (JSON) — Вкладка Body -> raw -> JSON:**
```json
{
    "name": "Спорт",
    "description": "Статьи о спорте"
}
```

**Успешный ответ (201):**
```json
{
    "id": 2,
    "name": "Спорт",
    "slug": "sport",
    "description": "Статьи о спорте",
    "posts_count": 0,
    "created_at": "..."
}
```

> `slug` генерируется автоматически из `name`.

---

### 10. Детали категории (GET / PATCH / DELETE)

| | |
|---|---|
| **GET** | `http://localhost:8000/api/v1/posts/categories/sport/` |
| **PATCH** | То же, с телом и токеном |
| **DELETE** | То же, с токеном |
| **Auth** | GET — любой, PATCH/DELETE — нужен токен |

> `sport` — это slug категории (не id).

---

### 11. Посты определённой категории

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/categories/sport/posts/` |
| **Auth** | Не нужна |

**Успешный ответ (200):**
```json
{
    "category": { "id": 2, "name": "Спорт", "slug": "sport", ... },
    "posts": [ ... ]
}
```

---

### ПОСТЫ

---

### 12. Список всех постов

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/` |
| **Auth** | Не нужна (но авторизованные видят свои черновики) |

**Query параметры:**
| Параметр | Пример | Описание |
|---|---|---|
| `search` | `?search=django` | Поиск по title, content |
| `ordering` | `?ordering=-views_count` | Сортировка |
| `category` | `?category=1` | Фильтр по id категории |
| `author` | `?author=1` | Фильтр по id автора |
| `status` | `?status=published` | Фильтр по статусу (`draft`/`published`) |

---

### 13. Создать пост

| | |
|---|---|
| **Метод** | `POST` |
| **URL** | `http://localhost:8000/api/v1/posts/` |
| **Auth** | Вкладка **Authorization** -> Bearer Token |

**Body (JSON) — Вкладка Body -> raw -> JSON:**
```json
{
    "title": "Мой первый пост",
    "content": "Содержимое поста...",
    "category": 1,
    "status": "published"
}
```

> `author` не нужно передавать — берётся из токена.  
> `slug` генерируется из `title`.  
> `status` может быть `draft` (черновик) или `published` (опубликован).

---

### 14. Детали поста (GET / PATCH / DELETE)

| | |
|---|---|
| **GET** | `http://localhost:8000/api/v1/posts/moi-pervyi-post/` |
| **PATCH** | То же + `Bearer <token>` |
| **DELETE** | То же + `Bearer <token>` |

> URL строится по `slug` поста.  
> Редактировать/удалять может только **автор** поста.  
> При GET — автоматически увеличивается счётчик просмотров `views_count`.

**Тело для PATCH:**
```json
{
    "title": "Обновлённый заголовок",
    "content": "Новый текст"
}
```

---

### 15. Мои посты

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/my-posts/` |
| **Auth** | `Bearer <access_token>` |

Возвращает все посты текущего пользователя (включая черновики).

**Query параметры:**
| Параметр | Пример | Описание |
|---|---|---|
| `status` | `?status=draft` | Только черновики |
| `category` | `?category=1` | По категории |
| `search` | `?search=заголовок` | Поиск |

---

### 16. Популярные посты (топ 10)

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/popular/` |
| **Auth** | Не нужна |

Возвращает 10 постов с наибольшим `views_count`.

---

### 17. Последние посты (топ 10)

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/recent/` |
| **Auth** | Не нужна |

Возвращает 10 последних опубликованных постов.

---

### 18. Рекомендуемые посты (для главной страницы)

| | |
|---|---|
| **Метод** | `GET` |
| **URL** | `http://localhost:8000/api/v1/posts/featured/` |
| **Auth** | Не нужна |

**Ответ:**
```json
{
    "popular_posts": [ ... ]
}
```

---

## ⚠️ Закомментированные эндпоинты (не работают — требуют приложение `subscribe`)

Следующий функционал **существует в коде, но закомментирован**, так как требует ещё не реализованного приложения `subscribe`:

| Эндпоинт | Описание |
|---|---|
| `GET /api/v1/posts/pinned/` | Список только закреплённых постов |
| `POST /api/v1/posts/<slug>/pin/` | Закрепить / открепить пост |

Они будут доступны после реализации `apps/subscribe` с моделями `Subscription` и `PinnedPost`.

---

## 🔄 Типичный сценарий тестирования

```
1. POST /api/v1/auth/register/    → получить токены
2. POST /api/v1/auth/login/       → (или залогиниться)
3. POST /api/v1/posts/categories/ → создать категорию (нужен токен)
4. POST /api/v1/posts/            → создать пост
5. GET  /api/v1/posts/            → посмотреть список
6. GET  /api/v1/posts/<slug>/     → открыть конкретный пост (views_count++)
7. PATCH /api/v1/posts/<slug>/    → обновить пост
8. GET  /api/v1/posts/my-posts/   → посмотреть свои посты
9. POST /api/v1/auth/logout/      → выйти
```

---

## 🛠 Полезные советы для Postman

1. **Создай Environment** с переменными:
   - `base_url` = `http://localhost:8000`
   - `access_token` — обновляй после каждого логина
   - `refresh_token` — для обновления access

2. **Автоматическое сохранение токенов** — добавь в Tests вкладку после login:
   ```javascript
   const data = pm.response.json();
   pm.environment.set("access_token", data.access);
   pm.environment.set("refresh_token", data.refresh);
   ```

3. **Content-Type** — всегда ставь `Content-Type: application/json` для POST/PATCH запросов.

4. **401 Unauthorized** — значит токен истёк или не передан. Сделай запрос на `/token/refresh/`.
