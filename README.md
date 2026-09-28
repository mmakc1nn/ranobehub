# Читалка вслух (Silero TTS)

Веб-читалка: вставляешь текст, выбираешь голос — он читает его вслух через
[Silero TTS](https://github.com/snakers4/silero-models) (PyTorch, работает
локально/офлайн после первой загрузки модели).

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Открой http://localhost:8000

При первом запросе `/api/voices` или `/api/speak` для языка модель Silero
скачается автоматически (через `torch.hub`, нужен интернет; занимает
десятки-сотни МБ) и закэшируется в `~/.cache/torch/hub`. Дальше всё работает
офлайн.

## Как это устроено

- `app/tts.py` — загрузка модели Silero, кэш моделей по языку, разбиение
  длинного текста на куски по предложениям (у Silero есть ограничение на
  длину одного вызова) и склейка результата в один WAV.
- `app/main.py` — FastAPI: `GET /api/languages`, `GET /api/voices`,
  `POST /api/speak`, плюс раздача статики из `app/static`.
- `app/static/` — страница с textarea, выбором языка/голоса, регулятором
  скорости воспроизведения и аудиоплеером.

## Голоса

Список голосов подтягивается динамически с самой модели (`model.speakers`),
ничего не захардкожено. Из коробки настроены языки:

- `ru` — `v4_ru` (голоса: aidar, baya, kseniya, xenia, eugene, random)
- `en` — `v3_en`

Добавить язык — дописать пару `"код": "id_пакета"` в `LANGUAGE_MODELS` в
`app/tts.py` (список пакетов — в `models.yml` репозитория
[snakers4/silero-models](https://github.com/snakers4/silero-models)).

## Ограничения MVP

- Один запрос `/api/speak` ограничен 20 000 символами (см.
  `tts.MAX_TEXT_CHARS`) — этого хватает на главу-две; для целой книги вызывай
  API по частям.
- Синтез идёт синхронно на CPU: длинный текст может занять заметное время
  (GPU не задействован, но можно добавить `.to("cuda")` при наличии).
