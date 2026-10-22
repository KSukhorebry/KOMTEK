# Сервис терминологии

Небольшой Django-сервис для хранения справочников, версий и элементов с REST API, административной панелью и OpenAPI-документацией.

## Запуск в Docker


```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

## Стек

- Python 3.10+
- Django 5.2
- Django REST Framework
- drf-spectacular
- SQLite


Админка доступна по адресу <http://127.0.0.1:8000/admin/>. Для входа используйте созданного суперпользователя.

## API и документация

- Swagger UI: <http://127.0.0.1:8000/api/docs/>

### `GET /refbooks/`

Возвращает `{ "refbooks": [{ "id": 1, "code": "...", "name": "..." }] }`. Параметр `date` необязателен и должен быть в формате `YYYY-MM-DD`. При его наличии возвращаются только справочники, имеющие версию с `start_date <= date`; справочник не дублируется. Неверная дата возвращает `400`.

```bash
curl 'http://127.0.0.1:8000/refbooks/?date=2026-10-20'
```

### `GET /refbooks/<id>/elements`

Возвращает `{ "elements": [{ "code": "...", "value": "..." }] }`. При переданном `version` выбирается только эта версия внутри заданного справочника. Иначе выбирается версия с самой поздней датой начала, не превышающей текущую локальную дату. Несуществующий справочник, неизвестная версия или отсутствие текущей версии дают `404`; существующая версия без элементов возвращает пустой массив.

```bash
curl 'http://127.0.0.1:8000/refbooks/1/elements?version=1.0'
```

### `GET /refbooks/<id>/check_element`

Обязательные параметры: `code`, `value`. Параметр `version` необязателен; при его отсутствии действует та же логика текущей версии. Совпадение обоих полей возвращает `{ "is_valid": true }`, несовпадение или отсутствие элемента в существующей версии — `{ "is_valid": false }` с HTTP `200`. Пропущенные или некорректные параметры дают `400`, неизвестный справочник или версия — `404`.

```bash
curl --get 'http://127.0.0.1:8000/refbooks/1/check_element' \
  --data-urlencode 'code=J00' \
  --data-urlencode 'value=Острый назофарингит' \
  --data-urlencode 'version=1.0'
```

## Тесты и миграции

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py check
```

Тесты используют отдельную временную SQLite-базу и не обращаются к внешним сервисам.

## Структура

- `config/` — настройки и корневые URL проекта.
- `terminology/models.py` — модели и ограничения БД.
- `terminology/services.py` — выбор текущей версии.
- `terminology/serializers.py` — валидация query-параметров и контракты ответов.
- `terminology/views.py`, `terminology/urls.py` — REST API.
- `terminology/admin.py` — управление данными через Django Admin.
- `terminology/tests/` — API- и constraint-тесты.
- `terminology/migrations/` — схема базы данных.