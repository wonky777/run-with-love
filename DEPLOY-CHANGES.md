# Как задеплоить изменения (пошагово)

Здесь — что и куда залить, чтобы правки попали на сайт. Два репозитория:

- **Бэкенд** — `github.com/wonky777/run-with-love` (Django: API + админка + готовая
  сборка фронта в `static_site/`). Именно его деплоит Railway.
- **Фронтенд** — `github.com/ProgerFox/run_with_love` (исходники React/TypeScript).
  Из него собирается `static_site/`. Сам по себе на сайт не деплоится.

> Готовая свежая сборка фронта **уже лежит** в `static_site/`, поэтому для
> публикации всех изменений достаточно задеплоить бэкенд (шаг 2). Фронт-репозиторий
> (шаг 3) пушим, чтобы исходники не потерялись и чтобы можно было пересобирать позже.

---

## 0. Сначала: ошибка `403 denied to amr777-star`

Она значит, что git залогинен под аккаунтом `amr777-star`, а у него нет прав на
эти репозитории. Репозитории твои (под `wonky777` / `ProgerFox`) — нужно, чтобы git
пушил под нужным аккаунтом. Самый надёжный способ на Windows — Personal Access Token:

1. Зайди на GitHub под аккаунтом-владельцем (например, `wonky777`).
2. **Settings → Developer settings → Personal access tokens → Tokens (classic) →
   Generate new token (classic)**. Поставь галочку **repo**. Скопируй токен.
3. Очисти старые сохранённые данные входа в Windows: **Панель управления →
   Учётные данные → Диспетчер учётных данных → Учётные данные Windows** — удали
   строки с `git:https://github.com`.
4. При следующем `git push` Windows спросит логин/пароль:
   - логин — имя владельца репозитория (`wonky777`),
   - пароль — **вставь токен** (не обычный пароль).

(Если у фронт-репозитория владелец `ProgerFox` — для него повторишь то же под этим
аккаунтом, либо добавишь второй аккаунт в коллабораторы.)

---

## 1. Бэкенд: первый коммит (репозиторий ещё не инициализирован)

Папка `C:\run-with-love\backend\backend` = содержимое репозитория `wonky777/run-with-love`
(там лежит `manage.py`). В терминале:

```bat
cd C:\run-with-love\backend\backend
git init -b master
git remote add origin https://github.com/wonky777/run-with-love.git
git fetch origin
git reset --mixed origin/master
git add -A
git status
git commit -m "Фиксы: ЧПУ, отдача медиа, отчёты, автоимпорт ВК, удобная админка, кнопки фронта"
git push origin master
```

`git status` должен показать изменённые/новые/удалённые файлы (модель отчётов,
`vk_api.py`, миграция `0003_report`, обновлённый `static_site` и т.д.).

---

## 2. Деплой бэкенда на Railway

Railway сам пересоберёт сервис после `git push` (в проекте есть `Procfile`,
который на каждом деплое прогоняет миграции и `collectstatic`). То есть новая
модель «Отчёты» применится автоматически.

Если сервис ещё не создан — `railway.app → New Project → Deploy from GitHub repo`,
выбери репозиторий, при необходимости укажи **Root Directory = backend/backend**.

### Переменные окружения (Variables)

```
DJANGO_SECRET_KEY = <длинная случайная строка>
DJANGO_DEBUG = 0
DJANGO_ALLOWED_HOSTS = *
CSRF_TRUSTED_ORIGINS = https://*.up.railway.app
DJANGO_SUPERUSER_USERNAME = admin
DJANGO_SUPERUSER_EMAIL = admin@example.com
DJANGO_SUPERUSER_PASSWORD = <пароль админки>

# Чтобы данные и фото не пропадали при редеплое (см. ниже про Volume):
SQLITE_PATH = /app/data/db.sqlite3
MEDIA_ROOT = /app/data/media

# Автоимпорт новостей из ВКонтакте (необязательно, см. раздел 4):
VK_ACCESS_TOKEN = <токен ВК>
VK_GROUP_DOMAIN = runwithlove
```

### Volume (чтобы база и фото сохранялись)

Файловая система Railway временная. Чтобы SQLite и загруженные картинки не
сбрасывались при деплое:

1. Сервис → **Volumes → Add Volume**, mount path: `/app/data`.
2. Переменные `SQLITE_PATH = /app/data/db.sqlite3` и `MEDIA_ROOT = /app/data/media`
   (уже в списке выше).

После деплоя: сайт — `https://<твой>.up.railway.app/`, админка — `…/admin/`.

---

## 3. Фронтенд: запушить исходники и (при будущих правках) пересобрать

Полный обновлённый исходник лежит в `C:\run-with-love\frontend\run_with_love`.
Залей его в `github.com/ProgerFox/run_with_love`:

```bat
cd C:\run-with-love\frontend\run_with_love
git init -b master
git remote add origin https://github.com/ProgerFox/run_with_love.git
git fetch origin
git reset --mixed origin/master
git add -A
git commit -m "API-интеграция, разделы О нас/Команда/Отчёты, рабочие кнопки"
git push origin master
```

### Как пересобрать фронт в будущем (когда поменяешь дизайн/тексты)

```bat
cd C:\run-with-love\frontend\run_with_love
npm install
npm run build
```

Затем содержимое получившейся папки `dist/` скопируй в бэкенд, заменив старое:
`dist\index.html`, `dist\favicon.svg`, `dist\icons.svg` → в `backend\backend\static_site\`,
а `dist\assets\*` → в `backend\backend\static_site\assets\` (старые файлы из
`assets` удали). После этого закоммить и запушь бэкенд (шаг 1) — сайт обновится.

> Локально проверить фронт с живым бэкендом: создай в папке фронта файл `.env`
> со строкой `VITE_API_URL=http://127.0.0.1:8000`, запусти бэкенд
> (`python manage.py runserver`) и фронт (`npm run dev`).

---

## 4. Токен ВКонтакте: где взять и куда вставить

Нужен, только если хочешь **автоматический** импорт новостей из сообщества
`vk.com/runwithlove` (ручное создание новостей работает и без него).

### Где получить токен (ключ доступа сообщества)

1. Открой своё сообщество ВК → **Управление**.
2. **Работа с API → Ключи доступа → Создать ключ**.
3. Отметь право **Стена** (доступ к стене сообщества). Создай — получишь длинную
   строку вида `vk1.a.XXXXXXXX...`. Это и есть токен.

(Альтернатива — токен пользователя через Standalone-приложение и Implicit Flow с
правом `wall`; для чтения своей стены проще ключ сообщества выше.)

### Куда вставить токен

- **На Railway (боевой сайт):** сервис → **Variables** →
  `VK_ACCESS_TOKEN = <твой токен>` и `VK_GROUP_DOMAIN = runwithlove`. Сохрани —
  Railway передеплоит.
- **Локально:** в файле `backend\backend\.env` (скопируй из `.env.example`):
  ```
  VK_ACCESS_TOKEN=vk1.a.XXXXXXXX...
  VK_GROUP_DOMAIN=runwithlove
  ```

### Как запускать импорт

- Из админки: раздел **Новости** → кнопка **«Загрузить новости из ВКонтакте»**.
- Из терминала: `python manage.py import_vk` (можно поставить на расписание/cron,
  чтобы новости подтягивались сами). Хранятся последние 10 импортированных постов.

Без токена кнопка/команда просто покажут понятную ошибку «не задан токен», ничего
не сломав.

---

## Короткий чек-лист

1. Починить вход в git (токен владельца репо) — раздел 0.
2. `git push` бэкенда → Railway сам применит миграции и обновит сайт — разделы 1–2.
3. (Желательно) запушить исходники фронта в `ProgerFox/run_with_love` — раздел 3.
4. (Желательно) добавить `VK_ACCESS_TOKEN` для автоимпорта новостей — раздел 4.
5. (Для боевого) подключить Volume, чтобы база и фото не пропадали — раздел 2.
