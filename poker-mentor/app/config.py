import os
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_file="config.txt"):
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            if not os.path.exists(self.config_file):
                self._create_default_config()
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    # Разбираем ключ=значение
                    if '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
            
            logger.info(f"Конфигурация загружена из {self.config_file}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Создание файла конфигурации по умолчанию"""
        default_config = """# Конфигурация Poker Mentor Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Настройки базы данных
DATABASE_URL=sqlite:///poker_mentor.db

# Настройки игры
DEFAULT_STAKE=1/2
DEFAULT_GAME_TYPE=cash
"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(default_config)
            logger.info(f"Создан файл конфигурации: {self.config_file}")
            print(f"📁 Создан файл конфигурации: {self.config_file}")
            print("🔧 Пожалуйста, установите ваш TELEGRAM_BOT_TOKEN в этом файле")
        except Exception as e:
            logger.error(f"Ошибка создания конфигурации: {e}")
    
    def get(self, key, default=None):
        """Получить значение конфигурации"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Установить значение конфигурации"""
        self.config[key] = value
        self._save_config()
    
    def _save_config(self):
        """Сохранить конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write("# Конфигурация Poker Mentor Bot\n")
                for key, value in self.config.items():
                    f.write(f"{key}={value}\n")
            logger.info(f"Конфигурация сохранена в {self.config_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def validate(self):
        """Проверка обязательных настроек"""
        required_keys = ['TELEGRAM_BOT_TOKEN']
        missing_keys = []
        
        for key in required_keys:
            if not self.get(key) or self.get(key) == 'your_bot_token_here':
                missing_keys.append(key)
        
        if missing_keys:
            error_msg = f"Отсутствуют обязательные настройки: {', '.join(missing_keys)}"
            logger.error(error_msg)
            return False, error_msg
        
        return True, "Конфигурация валидна"
        
# В config.py ДОБАВИТЬ:

    def setup_logging():
        """Настройка расширенного логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('poker_mentor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

# Глобальный объект конфигурации
config = Config()