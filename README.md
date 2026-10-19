# Обещали.

Сайт-архив: публичные слова чиновников — и что было дальше.

## Как устроено
- `stories.json` — все истории (единственное место, где живёт контент).
- `template.html` — дизайн и логика сайта.
- `site.config.json` — `site` (адрес сайта, https://…, без слэша в конце) и `contact` (ссылка для «Написать автору», например `mailto:…` или `https://t.me/…`).
- `build.py` — собирает всё из этих трёх файлов.
- `og.py` + `og_fonts/` — картинки для превью в мессенджерах.
- `validate.py` — проверка `stories.json`.

## Как обновить
1. Правишь `stories.json` (и при необходимости `site.config.json`).
2. `python3 validate.py` — должно быть «0 ошибок».
3. `python3 build.py` — пересоберёт `index.html`, `s/<id>/index.html` и `og/*.png`
   (`python3 build.py --no-og` — без картинок, быстрее).
4. Коммит и пуш всей папки.

Нужны: Python 3, `pip install playwright && playwright install chromium` (только для картинок).

## Ссылки
- Общий: `/`  · на историю: `/#id`  · для шеринга: `/s/<id>/` (с превью).
