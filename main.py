import logging  # Імпорт бібліотеки для роботи з логуванням
import requests  # Імпорт бібліотеки для здійснення HTTP-запитів
import signal  # Імпорт бібліотеки для обробки сигналів
import sys  # Імпорт бібліотеки для взаємодії з системою
from telegram import Update  # Імпорт класу Update з бібліотеки telegram
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters  # Імпорт класів для створення бота та обробки повідомлень

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Клас для отримання погодних даних
class WeatherFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city: str) -> str:
        url = f"{self.base_url}?q={city}&appid={self.api_key}&units=metric"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Викликає виняток HTTPError для неправильних відповідей
            data = response.json()

            if data.get("cod") != 200:
                return "Місто не знайдено. Будь ласка, перевірте назву міста та спробуйте ще раз."

            description = data['weather'][0]['description']
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']

            return (
                f"Погода у місті {city}:\n"
                f"Опис: {description.capitalize()}\n"
                f"Температура: {temp}°C\n"
                f"Вологість: {humidity}%\n"
                f"Швидкість вітру: {wind_speed} м/с"
            )
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Сталася помилка HTTP: {http_err}")
            return "Вибачте, виникла проблема з отриманням погодних даних. Перевірте правильність написання назви міста."
        except Exception as err:
            logging.error(f"Сталася інша помилка: {err}")
            return "Вибачте, виникла невідома помилка."

# Клас для бота
class WeatherBot:
    def __init__(self, telegram_token: str, weather_fetcher: WeatherFetcher):
        self.telegram_token = telegram_token
        self.weather_fetcher = weather_fetcher
        self.application = ApplicationBuilder().token(self.telegram_token).build()
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("weather", self.weather))
        self.application.add_handler(CommandHandler("stop", self.stop))
        self.application.add_handler(MessageHandler(filters.Text(), self.handle_text_message))

    async def start(self, update: Update, context: CallbackContext) -> None:
        await update.message.reply_text('Привіт! Використовуйте /weather <місто>, щоб отримати погоду.')

    async def weather(self, update: Update, context: CallbackContext) -> None:
        if len(context.args) == 0:
            await update.message.reply_text('Будь ласка, введіть назву міста.')
        else:
            city = ' '.join(context.args)
            weather_info = self.weather_fetcher.get_weather(city)
            await update.message.reply_text(weather_info)

    async def handle_text_message(self, update: Update, context: CallbackContext) -> None:
        # Витягуємо текст повідомлення
        text = update.message.text.strip()
        # Перевіряємо, чи текст є назвою міста
        if text:
            city = text
            weather_info = self.weather_fetcher.get_weather(city)
            await update.message.reply_text(weather_info)

    async def stop(self, update: Update = None, context: CallbackContext = None) -> None:
        if update:
            await update.message.reply_text('Бот зупиняється...')
        logger.info("Зупинка бота.")
        self.application.stop()
        sys.exit(0)

    def run(self) -> None:
        self.application.run_polling()

# Основна частина програми
if __name__ == '__main__':
    WEATHER_API_KEY = 'YOUR_WEATHER_API_KEY'
    TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'

    weather_fetcher = WeatherFetcher(WEATHER_API_KEY)
    weather_bot = WeatherBot(TELEGRAM_TOKEN, weather_fetcher)
    weather_bot.run()