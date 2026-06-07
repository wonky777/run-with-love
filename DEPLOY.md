# Как показать сайт по ссылке (на согласование)

Чтобы дать ссылку, сайт должен быть доступен из интернета. Два рабочих пути.

---

## Вариант A. Быстрая ссылка через туннель (5 минут, бесплатно)

Подходит, чтобы быстро показать макет на согласование. Ссылка живёт, пока
у тебя запущены сервер и туннель (компьютер включён).

1. Запусти сайт локально (как в README):
   ```bat
   cd backend
   .venv\Scripts\activate
   python manage.py runserver
   ```
   Проверь, что открывается http://127.0.0.1:8000/

2. В **новом** терминале подними туннель. Самое простое — cloudflared
   (не требует регистрации):
   - скачай cloudflared для Windows:
     https://github.com/cloudflare/cloudflared/releases (файл `cloudflared-windows-amd64.exe`)
   - запусти:
     ```bat
     cloudflared.exe tunnel --url http://127.0.0.1:8000
     ```
   - в консоли появится публичный адрес вида
     `https://random-words.trycloudflare.com` — это и есть ссылка на согласование.

   Альтернатива — ngrok (нужен бесплатный аккаунт + токен):
   ```bat
   ngrok http 8000
   ```

3. Отправляешь полученную `https://...trycloudflare.com` ссылку.
   Сайт и данные открываются сразу (просмотр не требует входа).

Примечания:
- `ALLOWED_HOSTS` в режиме разработки уже = `*`, туннель заработает без правок.
- Вход в админку через туннель: добавь адрес туннеля в `.env`
  `CSRF_TRUSTED_ORIGINS=https://random-words.trycloudflare.com` и перезапусти сервер.
  Для самого согласования (просмотра сайта) это не нужно.
- У `trycloudflare` адрес меняется при каждом запуске — это нормально для разовой демонстрации.

---

## Вариант B. Постоянный хостинг (для боевого сайта)

Постоянная ссылка, работает без твоего компьютера. Нужен VPS (~250 ₽/мес,
как в письме) или бесплатный PaaS.

Кратко для VPS (Ubuntu):
1. Установить Python, склонировать проект, `pip install -r requirements.txt`.
2. В `.env`: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY=...`,
   `DJANGO_ALLOWED_HOSTS=твой-домен-или-ip`,
   `CSRF_TRUSTED_ORIGINS=https://твой-домен`.
3. `python manage.py migrate` и `python manage.py createsuperuser`.
4. Запуск через gunicorn + nginx (nginx раздаёт `static_site/` и `media/`).
5. Домен направить на сервер — получишь постоянную ссылку.

Бесплатные платформы, где можно развернуть Django без своего сервера:
PythonAnywhere, Render, Railway — у каждого свой адрес вида
`https://имя.onrender.com`, который тоже можно отправить на согласование.

---

## Что отправлять

- Сама ссылка на сайт (главная страница).
- Если нужно показать админку — отдельно скажи, я помогу настроить доступ;
  но обычно на согласование шлют только публичную часть.

---

## Вариант B1. Railway (постоянная ссылка, без своего сервера)

Проект уже готов к Railway: есть `Procfile`, `requirements.txt` (с gunicorn и
whitenoise), статика админки отдаётся whitenoise, путь к базе настраивается.

### Шаги

1. Залей папку `backend/` в репозиторий GitHub (именно её содержимое должно быть
   в корне репозитория — там, где лежат `manage.py` и `Procfile`).
   Если в репозитории несколько папок — в настройках сервиса Railway укажи
   **Root Directory = backend**.

2. На railway.app: **New Project → Deploy from GitHub repo** → выбери репозиторий.
   Railway сам поставит зависимости и запустит `Procfile`.

3. В сервисе → вкладка **Variables** добавь переменные:
   ```
   DJANGO_SECRET_KEY = <длинная случайная строка>
   DJANGO_DEBUG = 0
   DJANGO_ALLOWED_HOSTS = *
   CSRF_TRUSTED_ORIGINS = https://*.up.railway.app
   DJANGO_SUPERUSER_USERNAME = admin
   DJANGO_SUPERUSER_EMAIL = admin@example.com
   DJANGO_SUPERUSER_PASSWORD = <пароль администратора>
   ```
   (Логин/пароль создадутся автоматически при первом деплое — это и есть вход в админку.)

4. В сервисе → **Settings → Networking → Generate Domain**. Получишь адрес вида
   `https://run-with-love-production.up.railway.app` — это и есть ссылка на согласование.

5. Готово:
   - сайт: `https://<твой>.up.railway.app/`
   - админка: `https://<твой>.up.railway.app/admin/`

### Чтобы данные не пропадали при редеплое

Файловая система Railway временная — SQLite-база и загруженные картинки
сбрасываются при каждом деплое. Для сохранения:

1. В сервисе → **Volumes → Add Volume**, mount path например `/app/data`.
2. Добавь переменную `SQLITE_PATH = /app/data/db.sqlite3`.
3. (Опц.) Картинки: их тоже стоит хранить на volume. Для согласования макета это
   не критично, для боевого — лучше отдельное хранилище/volume под `media/`.

Для демонстрации заказчику можно обойтись и без volume — просто учитывай, что
после нового деплоя контент нужно будет занести заново (или прогнать `seed_demo`).

### Если не хочешь подключать GitHub

Через Railway CLI из папки `backend/`:
```bat
npm i -g @railway/cli
railway login
railway init
railway up
```
Переменные и домен настраиваются так же, как выше.
