# natal_chart_plot.py

import matplotlib.pyplot as plt
import numpy as np

def calculate_aspects(planet_positions, orb=6):
    """
    Вычисляет аспекты между планетами.
    
    Параметры:
    - planet_positions: словарь, где ключи — названия планет, значения — эклиптическая долгота в градусах.
    - orb: допустимая погрешность для аспекта (в градусах).
    
    Возвращает:
    - Список аспектов в виде кортежей (планета1, планета2, аспект).
    """
    aspects_list = []
    aspect_angles = {
        0: 'Соединение',
        45: 'Полуквадрат',
        60: 'Секстиль',
        90: 'Квадрат',
        120: 'Трин',
        135: 'Полутрин',
        150: 'Квинкункс',
        180: 'Оппозиция'
    }

    planet_names = list(planet_positions.keys())
    num_planets = len(planet_names)

    for i in range(num_planets):
        for j in range(i + 1, num_planets):
            p1 = planet_positions[planet_names[i]]
            p2 = planet_positions[planet_names[j]]
            angle = abs(p1 - p2) % 360
            if angle > 180:
                angle = 360 - angle  # Всегда выбираем меньший угол

            for aspect_angle, aspect_name in aspect_angles.items():
                if abs(angle - aspect_angle) <= orb:
                    aspects_list.append((planet_names[i], planet_names[j], aspect_name))
                    break

    return aspects_list

def draw_natal_chart(planet_positions, filename='natal_chart.png'):
    """
    Рисует натальную карту на основе позиций планет и аспектов.
    
    Параметры:
    - planet_positions: словарь, где ключи — названия планет, значения — эклиптическая долгота в градусах.
    - filename: имя файла для сохранения изображения.
    """
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_aspect('equal')
    ax.axis('off')

    # Рисуем внешний круг (зодиакальный круг)
    circle = plt.Circle((0, 0), 1, color='black', fill=False)
    ax.add_artist(circle)

    # Знаки Зодиака
    zodiac_signs = ['♈︎', '♉︎', '♊︎', '♋︎', '♌︎', '♍︎',
                    '♎︎', '♏︎', '♐︎', '♑︎', '♒︎', '♓︎']

    # Рисуем знаки Зодиака
    for i in range(12):
        angle = np.deg2rad((i * 30) - 75)  # Смещение для корректного отображения
        x = 0.85 * np.cos(angle)
        y = 0.85 * np.sin(angle)
        ax.text(x, y, zodiac_signs[i], fontsize=16, ha='center', va='center')

    # Линии разделения знаков (каждые 30 градусов)
    for angle_deg in range(0, 360, 30):
        angle_rad = np.deg2rad(angle_deg - 90)
        x = np.cos(angle_rad)
        y = np.sin(angle_rad)
        ax.plot([0, x], [0, y], color='grey', linestyle='--')

    # Символы планет
    planet_symbols = {
        'Солнце': '☉',
        'Луна': '☽',
        'Меркурий': '☿',
        'Венера': '♀',
        'Марс': '♂',
        'Юпитер': '♃',
        'Сатурн': '♄',
        'Уран': '♅',
        'Нептун': '♆',
        'Плутон': '♇',
    }

    # Рисуем планеты
    planet_coords = {}
    for planet, lon in planet_positions.items():
        angle_rad = np.deg2rad(lon - 90)  # Смещаем так, чтобы 0 градусов было сверху
        x = 0.7 * np.cos(angle_rad)
        y = 0.7 * np.sin(angle_rad)
        symbol = planet_symbols.get(planet, planet)
        ax.text(x, y, symbol, fontsize=14, ha='center', va='center')
        planet_coords[planet] = (x, y)

    # Вычисляем аспекты
    aspects = calculate_aspects(planet_positions)

    # Рисуем аспекты
    for planet1, planet2, aspect_name in aspects:
        x1, y1 = planet_coords[planet1]
        x2, y2 = planet_coords[planet2]

        # Разные аспекты разными стилями (можно изменить под свои нужды)
        if aspect_name == 'Соединение':
            ax.plot([x1, x2], [y1, y2], color='blue', linestyle='-', linewidth=1.5)
        elif aspect_name == 'Секстиль':
            ax.plot([x1, x2], [y1, y2], color='green', linestyle='--', linewidth=1.5)
        elif aspect_name == 'Квадрат':
            ax.plot([x1, x2], [y1, y2], color='red', linestyle='-', linewidth=1.5)
        elif aspect_name == 'Трин':
            ax.plot([x1, x2], [y1, y2], color='green', linestyle='-', linewidth=1.5)
        elif aspect_name == 'Оппозиция':
            ax.plot([x1, x2], [y1, y2], color='red', linestyle='--', linewidth=1.5)
        elif aspect_name == 'Полуквадрат':
            ax.plot([x1, x2], [y1, y2], color='orange', linestyle='--', linewidth=1.5)
        elif aspect_name == 'Полутрин':
            ax.plot([x1, x2], [y1, y2], color='purple', linestyle='-', linewidth=1.5)
        elif aspect_name == 'Квинкункс':
            ax.plot([x1, x2], [y1, y2], color='cyan', linestyle='-', linewidth=1.5)

    # Сохраняем изображение
    plt.savefig(filename, bbox_inches='tight')
    plt.close()
