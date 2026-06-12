# CRM Bot

## Публичные ссылки на подборки

Публичные ссылки на подборки формируются из переменной окружения `PUBLIC_BASE_URL`:

```env
PUBLIC_BASE_URL=https://crm-lider.kz
```

Итоговая ссылка имеет формат `{PUBLIC_BASE_URL}/s/{selection.token}`.

Для локального теста можно использовать ngrok или Cloudflare Tunnel и указать выданный публичный URL в `PUBLIC_BASE_URL`.
Для продакшена нужно указать настоящий домен или публичный адрес сервера.

Если `PUBLIC_BASE_URL` не задан, используется fallback `http://localhost:8000` только для локальной разработки.
