import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, time

from google.oauth2 import service_account
from googleapiclient.discovery import build

TARGET_GROUP = "5.2"
API_URL = "https://api.loe.lviv.ua/api/menus?page=1&type=photo-grafic"
CALENDAR_ID = '66da222ba4635d7736127ef5f53eaea1055ee9f86070563fb6f3f157eab67ae6@group.calendar.google.com' # Вставте правильний ID
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

EVENT_MARKER = "🔦" 

def get_calendar_service():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Помилка авторизації: {e}")
        exit()

def clear_events_for_date(service, date_obj):
    """
    Видаляє всі події бота за вказану дату, щоб уникнути дублікатів 
    або застарілих даних.
    """
    start_of_day = datetime.combine(date_obj, time.min).isoformat() + 'Z'
    end_of_day = datetime.combine(date_obj, time.max).isoformat() + 'Z'

    print(f"   🧹 Очищення старих записів на {date_obj}...")
    
    events_result = service.events().list(
        calendarId=CALENDAR_ID, 
        timeMin=start_of_day, 
        timeMax=end_of_day, 
        singleEvents=True
    ).execute()
    
    events = events_result.get('items', [])
    
    deleted_count = 0
    for event in events:
        # ПЕРЕВІРКА БЕЗПЕКИ: Видаляємо тільки події, які мають наш маркер (🔦)
        # Це захистить ваші особисті події, якщо ви використовуєте особистий календар.
        if EVENT_MARKER in event.get('summary', ''):
            try:
                service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
                deleted_count += 1
            except Exception as e:
                print(f"      Помилка видалення події: {e}")

    if deleted_count > 0:
        print(f"      🗑️ Видалено {deleted_count} застарілих подій.")
    else:
        print(f"      ✨ Старих подій бота не знайдено.")

def parse_and_update():
    print("🔄 Отримання даних з API...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()

        try:
            menu_items = data["hydra:member"][0]["menuItems"]
        except (KeyError, IndexError, TypeError):
            print("❌ Некоректна структура JSON.")
            return
        
        service = get_calendar_service()

        for item in menu_items:
            name = item.get('name')
            raw_html = item.get('rawHtml')

            if not raw_html:
                continue

            if name == "Today":
                print("\n📅 --- СЬОГОДНІ ---")
                target_date = datetime.now().date()
                # Спершу видаляємо старе
                clear_events_for_date(service, target_date)
                # Потім додаємо нове (якщо є)
                process_html_schedule(service, raw_html, target_date)
            
            elif name == "Tomorrow":
                print("\n📅 --- ЗАВТРА ---")
                target_date = datetime.now().date() + timedelta(days=1)
                clear_events_for_date(service, target_date)
                process_html_schedule(service, raw_html, target_date)

    except Exception as e:
        print(f"❌ Загальна помилка: {e}")

def process_html_schedule(service, html_content, date_obj):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p')
    
    found_group = False
    
    for p in paragraphs:
        text = p.get_text().strip()
        
        if text.startswith(f"Група {TARGET_GROUP}"):
            found_group = True
            print(f"   🔎 Знайдено рядок: {text}")

            if "Електроенергія є" in text:
                print(f"   ✅ Світло буде! Нових подій не створюємо.")
            else:
                times = re.findall(r"(\d{1,2}:\d{2})", text)
                
                if len(times) >= 2:
                    for i in range(0, len(times), 2):
                        if i + 1 < len(times):
                            start_t = times[i]
                            end_t = times[i+1]
                            create_calendar_event(service, date_obj, start_t, end_t)
                else:
                    print("   ⚠️ Час не розпізнано.")
            return

    if not found_group:
        print(f"   ⚠️ Інфо про групу {TARGET_GROUP} не знайдено (календар на цей день очищено).")

def create_calendar_event(service, date_obj, start_time, end_time):
    date_str = date_obj.strftime("%Y-%m-%d")
    start_iso = f"{date_str}T{start_time}:00"
    end_iso = f"{date_str}T{end_time}:00"
    
    event_body = {
        'summary': f'{EVENT_MARKER} Відключення ({start_time}-{end_time})',
        'description': f'Група {TARGET_GROUP}. Графік за {date_str}.',
        'start': {
            'dateTime': start_iso,
            'timeZone': 'Europe/Kyiv',
        },
        'end': {
            'dateTime': end_iso,
            'timeZone': 'Europe/Kyiv',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': 30}],
        },
    }

    try:
        service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
        print(f"   💾 Створено: {start_time} - {end_time}")
    except Exception as e:
        print(f"   ❌ Помилка створення: {e}")

if __name__ == '__main__':
    parse_and_update()