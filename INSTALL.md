# 🎙️ Установка Video Transcriber

## Быстрая установка (рекомендуется)

### 1. Клонируйте репозиторий
```bash
git clone <ваш-репозиторий>
cd ris-transcriber
```

### 2. Запустите установщик
```bash
./install.sh
```

После этого вы сможете использовать команду `transcribe-video` из любой директории!

## Использование

### Простой запуск
```bash
transcribe-video https://youtube.com/watch?v=jNQXAC9IVRw
```

### С выбором модели
```bash
# Быстрая транскрипция (модель tiny)
transcribe-video -m tiny https://youtube.com/watch?v=...

# Качественная транскрипция (модель large)
transcribe-video -m large https://youtube.com/watch?v=...
```

### С указанием имени файла
```bash
transcribe-video https://youtube.com/watch?v=... "Моя лекция"
```

### Доступные модели
- `tiny` - очень быстро, базовое качество (39 MB)
- `base` - быстро, неплохое качество (74 MB)
- `small` - хороший баланс скорости и качества (244 MB) ⭐ по умолчанию
- `medium` - качественно, но медленнее (769 MB)
- `large` - максимальное качество (1.5 GB)

## Первый запуск

При первом запуске скрипт автоматически:
1. Создаст виртуальное окружение
2. Установит все зависимости
3. Загрузит выбранную модель Whisper

⏱️ Это может занять 5-10 минут.

## Ручная установка (альтернатива)

### 1. Без установки в систему
```bash
# Из директории проекта
./transcribe-video https://youtube.com/watch?v=...
```

### 2. Добавление в PATH вручную

Добавьте в `~/.bashrc` или `~/.zshrc`:
```bash
export PATH="$PATH:/путь/к/ris-transcriber"
```

Затем:
```bash
source ~/.bashrc  # или ~/.zshrc
```

## Требования

- Python 3.8+
- ffmpeg
- 8 GB RAM (для модели large)
- Интернет для загрузки видео

### Установка ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Скачайте с [ffmpeg.org](https://ffmpeg.org/download.html)

## Удаление

```bash
sudo rm /usr/local/bin/transcribe-video
```

## Решение проблем

### "Permission denied"
```bash
chmod +x transcribe-video
chmod +x install.sh
```

### "ffmpeg not found"
Установите ffmpeg согласно инструкции выше.

### "Python not found"
Убедитесь, что Python 3 установлен:
```bash
python3 --version
```