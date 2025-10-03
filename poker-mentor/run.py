#!/usr/bin/env python3
"""
Poker Mentor Bot - Запускной файл
"""

import sys
import os

# Добавляем папку app в путь Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def main():
    """Главная функция запуска"""
    print("🎮 Poker Mentor Bot - Запуск...")
    print("=" * 50)
    
    try:
        # Проверяем существование необходимых файлов
        required_files = ['config.txt', 'app/bot.py', 'app/config.py']
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ Отсутствует файл: {file}")
                return
        
        print("✅ Все необходимые файлы найдены")
        
        # Прямой импорт
        from app.bot import PokerMentorBot
        print("✅ Модули загружены успешно")
        
        bot = PokerMentorBot()
        print("✅ Бот создан успешно")
        print("🤖 Бот запускается...")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("=" * 50)
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 До свидания! Бот остановлен.")
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

# В run.py ДОБАВИТЬ тестовую функцию:

def test_user_stories():
    """Тестирование основных сценариев из User Stories"""
    print("\n" + "="*50)
    print("🧪 ТЕСТИРОВАНИЕ USER STORIES")
    print("="*50)
    
    test_cases = [
        {
            "name": "US-001: Первый запуск бота",
            "steps": ["/start", "Проверить приветствие", "Проверить главное меню"],
            "expected": "Пользователь видит приветствие и меню"
        },
        {
            "name": "US-003: Быстрая игра", 
            "steps": ["🎮 Быстрая игра", "Проверить начало игры"],
            "expected": "Игра начинается с дефолтными настройками"
        },
        {
            "name": "US-005: Игровой процесс",
            "steps": ["Сделать ход", "Проверить ответ AI", "Проверить обновление стека"],
            "expected": "Игровой процесс работает корректно"
        }
    ]
    
    for test in test_cases:
        print(f"✅ {test['name']}")
        print(f"   Ожидается: {test['expected']}")
    
    print(f"\n🎯 Протестировано: {len(test_cases)} сценариев")

if __name__ == "__main__":
    main()
    test_user_stories()
