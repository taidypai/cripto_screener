import requests
import sys

sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
import config

BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
CHAT_ID = config.TELEGRAM_CHAT_ID

def send_tg_message(message_text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message_text}

    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print(f" Сообщение отправлено в Telegram!")
            return True
        else:
            print(f" Ошибка Telegram {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f" Ошибка подключения к Telegram: {e}")
        return False

# def send_message_main():
#     message = input('Введите текст сообщения: ')
#     send_telegram_message(message)

# if __name__ == "__main__":
#    send_message_main()