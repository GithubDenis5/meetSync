# MeetSync — План развития фич

## Приоритет 0 — Стабилизация продакшена (сейчас)

Эти фичи нужно сделать прямо сейчас — они закрывают дыры, обнаруженные при деплое.

---

### 1. Prometheus /metrics для всех сервисов

**Проблема:** Prometheus скрейпит все 11 микросервисов по `/metrics`, но большинство отдают 404. Метрик нет.

**Что сделать:**
- Создать `shared/metrics.py` — единый модуль с стандартными метриками:
  - `http_requests_total` — счётчик запросов (method, endpoint, status)
  - `http_request_duration_seconds` — гистограмма latency
  - `db_connection_pool_size` — gauge (размер пула соединений)
  - `rabbitmq_connection_status` — 1/0 (подключён/нет)
  - `websocket_connections_active` — для notification-service
- В каждый сервис добавить middleware, которая автоматически увеличивает счётчики
- Добавить эндпоинт `/metrics` (через `prometheus_client`)

**Файлы:** `shared/metrics.py` (новый), каждый `*/app/main.py` (добавить middleware + /metrics)

---

### 2. Единый лог-агрегатор (Loki)

**Проблема:** `docker compose logs -f` неудобен на продакшене. Нет поиска по логам, нет связи между сервисами.

**Что сделать:**
- Добавить Loki + Promtail в docker-compose
- Promtail собирает JSON-логи со всех контейнеров (через Docker plugin)
- Grafana подключает Loki как источник данных
- Каждый сервис логирует structured JSON (уже есть `python-json-logger` — проверить что включён)
- Correlation ID: gateway генерирует UUID для каждого запроса и передаёт его в заголовке `X-Request-ID`. Все сервисы логируют этот ID.

**Файлы:** `docker-compose.yml` (+ loki, promtail), `shared/logging.py` (настроить JSON + correlation ID), `gateway/app/main.py` (middleware для X-Request-ID)

---

### 3. Бэкап PostgreSQL

**Проблема:** База данных не бэкапится. При сбое диска или случайном `docker compose down -v` данные потеряны.

**Что сделать:**
- Добавить контейнер `pg-backup` в docker-compose:
  - Ежедневный `pg_dump` в `/backups/postgres/`
  - Ретенция: 7 ежедневных, 4 недельных, 3 месячных
  - Опционально: S3-синхронизация
- Скрипт восстановления `scripts/restore-db.sh`
- В Makefile: `make backup`, `make restore`

**Файлы:** `docker-compose.yml`, `scripts/backup-db.sh` (новый), `scripts/restore-db.sh` (новый), `Makefile`

---

### 4. Graceful Shutdown + Healthcheck для всех сервисов

**Проблема:** При `docker compose down` сервисы просто убиваются. Нет graceful shutdown. Нет /ready и /live проб.

**Что сделать:**
- В каждый сервис добавить:
  - **/health** — уже есть, проверить что отвечает (DB + RabbitMQ + Redis)
  - **/ready** — готов принимать трафик
  - **/live** — жив ли процесс
- Graceful shutdown: при SIGTERM перестать принимать новые запросы, завершить текущие, закрыть соединения с БД/RabbitMQ
- В RabbitMQClient добавить метод `close()` и вызывать его в lifespan shutdown

**Файлы:** Каждый `*/app/main.py`, `shared/rabbitmq/client.py`

---

## Приоритет 1 — Пользовательские фичи (v1.1)

Эти фичи улучшают UX и покрывают основные сценарии.

---

### 5. Recurring Availability Rules

**Проблема:** Пользователь не может настроить регулярную занятость ("занят по пятницам"). Нужно каждый раз вручную отмечать дни.

**Что сделать:**
- Новая таблица `recurring_rules`:
  ```sql
  recurring_rules (
    id serial,
    user_id int,
    group_id int,
    day_of_week int,      -- 0-6 (пн-вс) или NULL если каждый день
    start_time time,      -- например 09:00
    end_time time,        -- например 18:00
    status free|busy|maybe,  -- статус на этот период
    date_start date,      -- с какой даты действует
    date_end date         -- по какую дату (NULL = бессрочно)
  )
  ```
- Calendar service: при запросе availability смержить explicit даты с recurring правилами
- API: `POST /calendar/recurring-rules`, `GET /calendar/recurring-rules`, `DELETE /calendar/recurring-rules/{id}`
- UI: компонент "Настроить регулярную занятость" с выбором дней недели и времени

**Файлы:** `shared/models/calendar.py` (новая модель), `shared/schemas/calendar.py` (новые схемы), `calendar-service/app/`, `frontend/`

---

### 6. Image Upload (аватарки, идеи, встречи)

**Проблема:** Нельзя загрузить фото. Аватарки — иконки. Идеи и встречи — без картинок.

**Что сделать:**
- Новый эндпоинт `POST /upload` (через gateway)
- Загрузка в Docker volume `/uploads/`
- Оптимизация: pillow resize до 3 размеров (thumbnail 150x150, medium 800x800, original)
- Поддержка: jpeg, png, webp, max 10MB
- Модель `media`:
  ```sql
  media (id, user_id, filename, mimetype, size, path_original, path_thumbnail, path_medium)
  ```
- Привязать media к user avatar, idea photo, meeting location photo
- UI: drag-and-drop в профиле, при создании идеи, при создании встречи

**Файлы:** `shared/models/media.py` (новый), `shared/schemas/media.py` (новый), `gateway/app/` (роут /upload), `frontend/` (upload компоненты)

---

### 7. Email Notifications

**Проблема:** Нет уведомлений по email. Пользователь может пропустить приглашение или голосование.

**Что сделать:**
- Расширить notification-service: добавить email-канал
- На выбор: SendGrid API (рекомендуется — бесплатно 100 писем/день) или SMTP (для своих серверов)
- Шаблоны писем (HTML + plain text):
  - Welcome email с подтверждением
  - "Вас пригласили в группу"
  - "Новое голосование"
  - "Встреча назначена"
  - "Дашборд доступности за неделю" (дайджест)
- Новая опция `.env`: `EMAIL_PROVIDER=sendgrid|smtp`, `EMAIL_API_KEY=...`
- UI: страница "Настройки уведомлений" (email/telegram/веб)

**Файлы:** `notification-service/app/` (email handler), `shared/models/`, `frontend/` (настройки)

---

### 8. Group Dashboard

**Проблема:** Нет аналитики по группе. Кто активен? Сколько встреч провели? Какие идеи популярны?

**Что сделать:**
- Новый эндпоинт `GET /groups/{id}/dashboard`:
  - Участники: список с активностью (last_seen, meetings_attended, ideas_posted)
  - Встречи: количество проведённых, средняя явка, популярные дни/время
  - Идеи: топ по реакциям, топ по категориям
  - Heatmap: "кто когда свободен" — визуализация занятости группы за неделю/месяц
- UI: новая вкладка "Дашборд" в группе

**Файлы:** `group-service/app/`, `frontend/` (новая страница Dashboard с графиками)

---

### 9. Calendar — Drag & Drop

**Проблема:** Отмечать занятость неудобно — нужно нажимать на каждый день и выбирать статус.

**Что сделать:**
- Календарь с drag-to-select: зажимаешь и тащишь по дням — они отмечаются как busy
- Опционально: swipe по часам (как Google Calendar)
- Быстрые кнопки: "Вся неделя свободна", "Весь месяц свободен"
- Цвета: зелёный (free), жёлтый (maybe), красный (busy)

**Файлы:** `frontend/` (компонент календаря)

---

### 10. Backend CLI-скрипты

**Проблема:** Админские действия только через API. Нет быстрых утилит.

**Что сделать:**
- `scripts/admin.py` — CLI с командами:
  - `python scripts/admin.py create-user --email ... --password ... --role admin`
  - `python scripts/admin.py list-services` — проверить health всех сервисов
  - `python scripts/admin.py purge-notifications --days 30` — очистить старые уведомления
  - `python scripts/admin.py migrate --check` — проверить статус миграций
  - `python scripts/admin.py rabbitmq-status` — проверить очереди RabbitMQ

**Файлы:** `scripts/admin.py` (новый)

---

## Приоритет 2 — Среднесрочные фичи (v1.2)

---

### 11. Notifications: групповые чаты в WebSocket

**Проблема:** WebSocket уведомления приходят только конкретному пользователю. Нет группового чата или ленты событий группы.

**Что сделать:**
- WebSocket `ws://host/api/v1/ws/group/{group_id}` — подключиться к ленте группы
- Новые события `GroupMessage`, `GroupEvent` через RabbitMQ
- UI: боковая панель с лентой событий группы (кто что сделал)
- История событий группы: `GET /api/v1/events?group_id=...&limit=50`

**Файлы:** `notification-service/app/`, `group-service/app/`, `frontend/`

---

### 12. Meeting Reschedule с учетом Calendar

**Проблема:** Если встреча не набирает RSVP, организатор вручную меняет дату. Нет "предложить альтернативу".

**Что сделать:**
- `POST /meetings/{id}/suggest-alternatives` — scheduler проверяет календари участников и предлагает 3 ближайших слота, где все свободны
- UI: кнопка "Предложить другие даты" → модалка с вариантами → голосование

**Файлы:** `scheduler-service/app/`, `meeting-service/app/`, `frontend/`

---

### 13. Rate Limiting — per user + per endpoint

**Проблема:** Сейчас rate limit 60 запросов/мин на IP. Авторизованные пользователи должны иметь больший лимит. Auth эндпоинты — меньший.

**Что сделать:**
- Gateway: читаем токен, извлекаем user_id
- Redis: ключ `ratelimit:user:{user_id}:{endpoint_group}`, TTL 60s
- Анонимные: 10 req/min на /auth/login, /auth/register
- Авторизованные: 120 req/min на всё
- Хедеры ответа: `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `X-RateLimit-Limit`
- Retry-After header при превышении

**Файлы:** `gateway/app/` (middleware rate_limit), `shared/rate_limit.py` (новый)

---

### 14. Search (идеи и встречи)

**Проблема:** Нет поиска. В группе с 50+ идеями невозможно найти нужную.

**Что сделать:**
- PostgreSQL tsvector:
  ```sql
  ALTER TABLE ideas ADD COLUMN search_vector tsvector;
  CREATE INDEX idx_ideas_search ON ideas USING GIN(search_vector);
  ```
- Триггер на INSERT/UPDATE: обновляет search_vector из title + description + tags
- Эндпоинт: `GET /ideas/search?q=...&group_id=...`
- Аналогично для meetings
- UI: строка поиска с debounce (300ms), real-time результаты

**Файлы:** `ideas-service/app/` (search эндпоинт), `meeting-service/app/` (search эндпоинт), `shared/models/`, `frontend/`

---

### 15. User Presence (онлайн-статус)

**Проблема:** Не видно, кто из участников группы онлайн.

**Что сделать:**
- WebSocket ping/pong — notification-service отслеживает активные соединения
- Redis: `presence:group:{group_id}` — set of user_ids с TTL (последний ping)
- API: `GET /groups/{id}/online` → список онлайн участников
- UI: зелёная точка рядом с именем онлайн-участника

**Файлы:** `notification-service/app/`, `group-service/app/`, `frontend/`

---

### 16. Telegram: inline-кнопки и кастомные команды

**Проблема:** Telegram бот умеет только `/start` и `/start <code>`. Нет уведомлений с кнопками.

**Что сделать:**
- Inline keyboard:
  - "Подтвердить участие" (RSVP) — приходит в Telegram, нажимаешь Going/Not Going
  - "Посмотреть идеи группы" — inline-список
  - "Проголосовать" — прямо в чате
- Команды: `/mygroups`, `/nextmeeting`, `/ideas`, `/vote`
- Кастомная клавиатура (reply keyboard markup)

**Файлы:** `telegram-service/app/`

---

## Приоритет 3 — Долгосрочные фичи (v2.0+)

---

### 17. Вебхуки для внешних сервисов

**Сценарий:** Slack, Discord, Notion — получать уведомления о событиях группы.

**Что сделать:**
- UI: страница "Интеграции" в настройках группы
- Добавить URL вебхука → привязать к событиям
- Система очередей для отправки (через RabbitMQ)
- Retry с exponential backoff при недоступности вебхука
- Delivery log: статус доставки каждого вебхука

**Файлы:** Новый сервис `webhook-service/`, `docker-compose.yml`, `frontend/`

---

### 18. PWA (Progressive Web App)

**Сценарий:** Установить MeetSync как приложение на телефон. Push-уведомления.

**Что сделать:**
- Service Worker: кэширование статики, offline fallback
- manifest.json: иконки, splash screen, theme color
- Push API: VAPID keys, подписка через notification-service
- Background sync: если офлайн, отправить данные при подключении

**Файлы:** `frontend/`

---

### 19. Activity History / Audit Log

**Сценарий:** Кто и когда что сделал в группе. Аудит действий.

**Что сделать:**
- `event_store` таблица — все события RabbitMQ дублируются в БД
- UI: хронологическая лента группы
- Фильтры: по типу события, по участнику, по дате
- Экспорт лога (CSV/JSON)

**Файлы:** `shared/models/`, `scheduler-service/app/` (consumer для записи событий), `frontend/`

---

### 20. CI/CD (GitHub Actions)

**Сценарий:** push в main → тесты → сборка → деплой.

**Что сделать:**
- Линтер (ruff) — strict mode (сейчас `|| true`)
- Type checker (mypy) — strict mode
- Юнит-тесты для каждого сервиса
- Интеграционные тесты в Docker Compose
- Docker build на каждый push (с кэшированием слоёв)
- Deploy stage: SSH на сервер → git pull → docker compose up -d --build

**Файлы:** `.github/workflows/`

---

### 21. Frontend Unit Tests (Vitest + Playwright)

**Сценарий:** Фронтенд не покрыт тестами. Рефакторинг опасен.

**Что сделать:**
- Vitest для unit-тестов компонентов
- Playwright Component Tests для интерактивных компонентов
- Playwright E2E: ключевые сценарии (регистрация → группа → идея → встреча)

**Файлы:** `frontend/src/__tests__/`, `e2e/`

---

### 22. Инвайты по ссылке (deep link)

**Сценарий:** Поделиться ссылкой на группу: `https://meetsync.app/invite/CODE`

**Что сделать:**
- Фронтенд: страница `/invite/{code}` — показывает название группы, кнопка "Присоединиться"
- Если не авторизован — форма регистрации → редирект на группу
- Telegram: `/start CODE` уже работает

**Файлы:** `frontend/` (роут /invite/{code}), `gateway/app/` (редирект)

---

### 23. Поддержка нескольких часовых поясов

**Проблема:** Все даты в UTC. Если группа из разных часовых поясов — путаница.

**Что сделать:**
- Каждый пользователь выбирает timezone (в профиле)
- Calendar service конвертирует даты в timezone пользователя
- API принимает timezone offset в запросах
- UI: селектор часового пояса при регистрации + автоопределение через браузер

**Файлы:** `shared/models/user.py` (+ timezone), `calendar-service/app/`, `frontend/`

---

### 24. Импорт событий из Google Calendar / iCal

**Сценарий:** У пользователя события в Google Calendar. Вместо того чтобы вручную отмечать занятость, импортировать их.

**Что сделать:**
- OAuth 2.0 flow: фронтенд → gateway → Google OAuth
- Сохранить refresh token
- Фоновый job: раз в час синхронизировать события
- iCal: загрузить .ics файл → распарсить → отметить занятость

**Файлы:** Новый сервис `integration-service/`, `docker-compose.yml`, `frontend/`

---

### 25. Telegram Mini App

**Сценарий:** Открыть MeetSync прямо в Telegram без установки.

**Что сделать:**
- Telegram Mini App — WebView внутри Telegram
- Аутентификация через Telegram (Telegram Login Widget)
- Ограниченный функционал: посмотреть идеи, ответить на RSVP, глянуть календарь

**Файлы:** `frontend/` (Telegram WebApp компоненты), `telegram-service/app/`

---

## Как выбирать приоритет

1. **P0** — блокеры продакшена. Делать сейчас.
2. **P1 — пользовательские фичи.** Одна фича = 1-2 недели для одного разработчика.
3. **P2 — улучшения.** Одна фича = 1 неделя.
4. **P3 — долгосрочные.** Только после стабилизации.

### Быстрый старт на 1 неделю:
| День | Задача |
|------|--------|
| Пн | /metrics для всех сервисов |
| Вт | Loki + Promtail + correlation ID |
| Ср | Backup PostgreSQL |
| Чт | Graceful shutdown + /ready + /live |
| Пт | Recurring availability rules (API) |

### Следующая неделя:
| День | Задача |
|------|--------|
| Пн | Recurring availability rules (UI) |
| Вт | Image upload (API) |
| Ср | Image upload (UI) |
| Чт | Email notifications (API) |
| Пт | Email notifications (UI + SendGrid) |
