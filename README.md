# SAP MM + SD Trainer

Интерактивный тренажёр по SAP Materials Management (управление материальными потоками) и Sales and Distribution (сбыт): **500 вопросов**, **25 тестов по 20 вопросов**.

## Использование

Откройте [сайт тренажёра](https://mantorry.github.io/sap-mm-sd-trainer/). Верные ответы открываются после завершения блока. Результаты сохраняются в браузере каждого участника — централизованного сбора данных нет.

## Разработка

- `index.html` — автономный HTML-файл приложения и банка вопросов.
- `scripts/validate.mjs` — проверка количества, структуры вопросов и синтаксиса JavaScript.
- `.github/workflows/pages.yml` — автоматическая проверка и публикация на GitHub Pages.

Чтобы проверить локально:
```bash
node scripts/validate.mjs
```
Для обновлений создавайте ветку `feature/...` или `fix/...`, затем Pull Request в `main`. После успешной проверки и слияния `main` GitHub Actions публикует новую версию.

## Версии

Используем [Semantic Versioning](https://semver.org/lang/ru/): `MAJOR.MINOR.PATCH`.
- PATCH — исправления ошибок.
- MINOR — новые вопросы и функции, совместимые с существующей версией.
- MAJOR — изменения формата данных или сохраненного прогресса.

См. [CHANGELOG.md](CHANGELOG.md).
