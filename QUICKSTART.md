# 🚀 Быстрый старт - Video Transcriber

## 1. Установка за 3 команды

```bash
# Склонируйте репозиторий
git clone <ваш-репозиторий>
cd ris-transcriber

# Сделайте исполняемыми (если нужно)
chmod +x transcribe-video install.sh

# Установите в систему (опционально)
./install.sh
```

## 2. Использование

### Базовый запуск
```bash
./transcribe-video https://youtube.com/watch?v=jNQXAC9IVRw
```

### С выбором модели
```bash
# Быстро (модель tiny)
./transcribe-video -m tiny https://youtube.com/watch?v=...

# Качественно (модель large - загрузка 1.5GB)
./transcribe-video -m large https://youtube.com/watch?v=...
```

### С именем файла
```bash
./transcribe-video https://youtube.com/watch?v=... "Моё видео"
```

## 3. Модели Whisper

| Модель | Размер | Скорость | Качество | Рекомендация |
|--------|--------|----------|----------|--------------|
| `tiny` | 39 MB | ⚡⚡⚡ | ⭐⭐ | Тесты |
| `base` | 74 MB | ⚡⚡ | ⭐⭐⭐ | Быстро |
| `small` | 244 MB | ⚡ | ⭐⭐⭐⭐ | По умолчанию |
| `medium` | 769 MB | 🐌 | ⭐⭐⭐⭐⭐ | Качество |
| `large` | 1.5 GB | 🐌🐌 | ⭐⭐⭐⭐⭐⭐ | Максимум |

## 4. Первый запуск

При первом запуске скрипт автоматически:
1. ✅ Создаст виртуальное окружение
2. ✅ Установит все зависимости
3. ✅ Загрузит модель Whisper

**Время установки:** 5-10 минут

## 5. Требования

- **Python 3.8+** - обычно уже установлен
- **ffmpeg** - нужно установить отдельно

### Установка ffmpeg:

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Скачать с [ffmpeg.org](https://ffmpeg.org/download.html)

## 6. Примеры

```bash
# Русское видео с автоназванием файла
./transcribe-video https://youtube.com/watch?v=jbDbXkRQYQ4

# Английское видео, быстрая модель
./transcribe-video -m tiny https://youtube.com/watch?v=jNQXAC9IVRw

# Лекция с качественной моделью
./transcribe-video -m large https://youtube.com/watch?v=... "Лекция по ИИ"
```

## 7. Справка

```bash
./transcribe-video --help
```

## 8. Глобальная установка (опционально)

После `./install.sh` можно использовать из любой папки:

```bash
transcribe-video https://youtube.com/watch?v=...
```

**Удаление:**
```bash
sudo rm /usr/local/bin/transcribe-video
```

---

**Готово! 🎉** Теперь у вас есть мощный транскрайбер видео с чистой архитектурой!