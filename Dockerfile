# Використовуємо легку версію Python
FROM python:3.10-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо requirements і встановлюємо залежності
# --no-cache-dir зменшує розмір імеджа, не зберігаючи кеш pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту файлів (скрипт і ключ)
COPY . .

# Команда, яка запуститься при старті контейнера
CMD ["python", "main.py"]