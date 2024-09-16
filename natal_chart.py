# natal_chart.py

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from astropy.time import Time
from astropy.coordinates import solar_system_ephemeris
import astropy.units as u
from astroquery.jplhorizons import Horizons
import numpy as np
from geopy.geocoders import Nominatim
import datetime
import pytz
from timezonefinder import TimezoneFinder
import re
from natal_chart_plot import draw_natal_chart
import os

# Определяем этапы разговора как строки
DATE, TIME, PLACE, CONFIRMATION = 'DATE', 'TIME', 'PLACE', 'CONFIRMATION'

async def start_natal_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите вашу дату рождения в формате ДД.ММ.ГГГГ:")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text

    # Проверка формата даты
    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
    if not re.match(date_pattern, date_text):
        await update.message.reply_text("Некорректный формат даты. Используйте ДД.ММ.ГГГГ.")
        return DATE

    # Проверка даты на реальность
    day, month, year = map(int, date_text.split('.'))
    try:
        birth_date = datetime.date(year, month, day)
    except ValueError:
        await update.message.reply_text("Некорректная дата. Пожалуйста, введите существующую дату.")
        return DATE

    today = datetime.date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    if birth_date > today:
        await update.message.reply_text("Дата рождения не может быть в будущем. Пожалуйста, введите корректную дату.")
        return DATE
    elif age > 120:
        await update.message.reply_text("Пожалуйста, введите корректную дату рождения (меньше 120 лет назад).")
        return DATE

    context.user_data['date'] = date_text
    await update.message.reply_text("Введите время вашего рождения в формате ЧЧ:ММ:")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_text = update.message.text

    # Проверка формата времени
    time_pattern = r'\d{2}:\d{2}'
    if not re.match(time_pattern, time_text):
        await update.message.reply_text("Некорректный формат времени. Используйте ЧЧ:ММ.")
        return TIME

    context.user_data['time'] = time_text
    await update.message.reply_text("Введите место вашего рождения:")
    return PLACE

async def get_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['place'] = update.message.text

    # Подтверждение данных
    confirmation_text = (
        f"Пожалуйста, подтвердите введённые данные:\n"
        f"Дата рождения: {context.user_data['date']}\n"
        f"Время рождения: {context.user_data['time']}\n"
        f"Место рождения: {context.user_data['place']}\n\n"
        "Верны ли эти данные? (да/нет)"
    )
    await update.message.reply_text(confirmation_text)
    return CONFIRMATION

async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text.strip().lower()
    if confirmation in ['да', 'yes', 'верно']:
        await update.message.reply_text("Спасибо! Идет расчет вашей натальной карты...")

        # Вызываем функцию для расчета натальной карты
        result = calculate_natal_chart(context.user_data, update.effective_user.id)

        if result is None:
            await update.message.reply_text("Произошла ошибка при расчете натальной карты.")
            return ConversationHandler.END

        # Отправляем текстовый результат
        await update.message.reply_text(f"Ваша натальная карта:\n{result}")

        # Отправляем изображение натальной карты
        filename = f'natal_chart_{update.effective_user.id}.png'
        with open(filename, 'rb') as photo:
            await update.message.reply_photo(photo)

        # Удаляем файл после отправки
        os.remove(filename)

        # Создание Inline-кнопок
        keyboard = [
            [InlineKeyboardButton("Получить расшифровку", callback_data='get_interpretation')],
            [InlineKeyboardButton("Обратно в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение с кнопками
        await update.message.reply_text(
            "Это ваша натальная карта. Вы можете получить расшифровку, нажав на кнопку 'Получить расшифровку'.",
            reply_markup=reply_markup
        )

        return ConversationHandler.END
    elif confirmation in ['нет', 'no', 'неверно']:
        await update.message.reply_text("Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ:")
        return DATE
    else:
        await update.message.reply_text("Пожалуйста, ответьте 'да' или 'нет'.")
        return CONFIRMATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def calculate_natal_chart(data, user_id):
    try:
        # Парсим дату и время
        day, month, year = map(int, data['date'].split('.'))
        hour, minute = map(int, data['time'].split(':'))
        place = data['place']

        # Получаем координаты места рождения
        geolocator = Nominatim(user_agent="natal_chart_bot")
        location = geolocator.geocode(place)
        if not location:
            return "Место рождения не найдено. Пожалуйста, проверьте правильность ввода."

        lat = location.latitude
        lon = location.longitude

        # Определяем часовой пояс места рождения
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
        if not timezone_str:
            timezone_str = 'UTC'  # Если не удалось определить, используем UTC

        timezone = pytz.timezone(timezone_str)

        # Создаем объект datetime с учетом часового пояса
        naive_datetime = datetime.datetime(year, month, day, hour, minute)
        local_datetime = timezone.localize(naive_datetime)

        # Преобразуем в UTC для расчетов
        utc_datetime = local_datetime.astimezone(pytz.utc)

        # Создаем объект времени для astropy
        time = Time(utc_datetime)

        # Список планет для расчета (используем числовые идентификаторы)
        planets = {
            'Солнце': 10,
            'Луна': 301,
            'Меркурий': 199,
            'Венера': 299,
            'Марс': 499,
            'Юпитер': 599,
            'Сатурн': 699,
            'Уран': 799,
            'Нептун': 899,
            'Плутон': 999,
        }

        result = "Позиции планет:\n"

        # Словарь для хранения позиций планет в градусах
        planet_positions_degrees = {}

        # Устанавливаем эфемериды
        solar_system_ephemeris.set('builtin')

        for planet_name, planet_id in planets.items():
            # Получаем эфемериды планеты
            obj = Horizons(id=planet_id,
                           location={'lon': lon, 'lat': lat, 'elevation': 0},
                           epochs=time.jd)
            eph = obj.ephemerides()

            # Проверяем, есть ли данные
            if len(eph) == 0:
                result += f"{planet_name}: данные недоступны\n"
                continue

            lon_planet = eph['EclLon'][0]

            # Проверяем, является ли значение замаскированным
            if np.ma.is_masked(lon_planet):
                result += f"{planet_name}: данные недоступны\n"
                continue

            # Сохраняем фактическую долготу планеты
            planet_positions_degrees[planet_name] = lon_planet

            # Определяем знак Зодиака
            sign_index = int(lon_planet // 30) % 12
            sign_degree = lon_planet % 30
            zodiac_signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева',
                            'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
            sign_name = zodiac_signs[sign_index]

            result += f"{planet_name}: {sign_name} {sign_degree:.2f}°\n"

        # Генерируем имя файла на основе user_id
        filename = f'natal_chart_{user_id}.png'
        draw_natal_chart(planet_positions_degrees, filename=filename)

        return result

    except Exception as e:
        print(f"Ошибка при расчете натальной карты: {e}")
        return None
