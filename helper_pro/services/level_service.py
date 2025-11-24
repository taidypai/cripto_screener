import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)

class LevelService:
    def __init__(self):
        self.levels_file = "user_levels.json"
        self.user_levels = self._load_levels()

    def _load_levels(self) -> Dict:
        """Загрузка уровней из файла"""
        try:
            if os.path.exists(self.levels_file):
                with open(self.levels_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading levels: {e}")
            return {}

    def _save_levels(self):
        """Сохранение уровней в файл"""
        try:
            with open(self.levels_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_levels, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving levels: {e}")

    def add_level(self, user_id: int, pair: str, price: float):
        """Добавление уровня для пользователя"""
        try:
            user_id_str = str(user_id)
            expiry_time = (datetime.now() + timedelta(days=1)).isoformat()

            if user_id_str not in self.user_levels:
                self.user_levels[user_id_str] = {}

            if pair not in self.user_levels[user_id_str]:
                self.user_levels[user_id_str][pair] = []

            # Добавляем уровень с временем истечения
            level_data = {
                "price": price,
                "added_at": datetime.now().isoformat(),
                "expires_at": expiry_time
            }

            self.user_levels[user_id_str][pair].append(level_data)
            self._save_levels()
            logger.info(f"Added level {price} for pair {pair} to user {user_id}")

        except Exception as e:
            logger.error(f"Error adding level: {e}")

    def get_user_levels(self, user_id: int) -> Dict:
        """Получение уровней пользователя"""
        try:
            user_id_str = str(user_id)
            self._clean_expired_levels(user_id_str)

            if user_id_str in self.user_levels:
                return self.user_levels[user_id_str]
            return {}
        except Exception as e:
            logger.error(f"Error getting user levels: {e}")
            return {}

    def get_active_levels_for_pair(self, pair: str) -> List[float]:
        """Получение активных уровней для конкретной пары от всех пользователей"""
        try:
            active_levels = []
            current_time = datetime.now()

            for user_id_str, user_data in self.user_levels.items():
                if pair in user_data:
                    for level in user_data[pair]:
                        try:
                            expires_at = datetime.fromisoformat(level["expires_at"])
                            if expires_at > current_time:
                                active_levels.append(level["price"])
                        except Exception as e:
                            logger.error(f"Error parsing expiry time: {e}")

            # Убираем дубликаты и сортируем
            active_levels = sorted(list(set(active_levels)))
            logger.info(f"Found {len(active_levels)} active levels for {pair}: {active_levels}")
            return active_levels

        except Exception as e:
            logger.error(f"Error getting active levels for {pair}: {e}")
            return []

    def check_price_touches_level(self, pair: str, low_price: float, high_price: float, tolerance_percent: float = 0.1) -> bool:
        """Проверяет, коснулась ли цена какого-либо уровня в диапазоне low-high"""
        try:
            active_levels = self.get_active_levels_for_pair(pair)

            for level in active_levels:
                # Проверяем, находится ли уровень в диапазоне low-high свечи
                if low_price <= level <= high_price:
                    logger.info(f"✅ Price touched level {level} for {pair} (range: {low_price}-{high_price})")
                    return True

                # Проверяем касание с допуском (если цена почти дошла до уровня)
                tolerance = level * tolerance_percent / 100
                if abs(low_price - level) <= tolerance or abs(high_price - level) <= tolerance:
                    logger.info(f"✅ Price nearly touched level {level} for {pair} (within {tolerance_percent}% tolerance)")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking price touches level for {pair}: {e}")
            return False

    def _clean_expired_levels(self, user_id_str: str):
        """Очистка просроченных уровней"""
        try:
            if user_id_str not in self.user_levels:
                return

            current_time = datetime.now()
            pairs_to_remove = []

            for pair, levels in self.user_levels[user_id_str].items():
                valid_levels = []
                for level in levels:
                    try:
                        expires_at = datetime.fromisoformat(level["expires_at"])
                        if expires_at > current_time:
                            valid_levels.append(level)
                    except Exception as e:
                        logger.error(f"Error parsing expiry time: {e}")

                if valid_levels:
                    self.user_levels[user_id_str][pair] = valid_levels
                else:
                    pairs_to_remove.append(pair)

            # Удаляем пары без уровней
            for pair in pairs_to_remove:
                del self.user_levels[user_id_str][pair]

            # Удаляем пользователя если нет пар
            if not self.user_levels[user_id_str]:
                del self.user_levels[user_id_str]

            self._save_levels()

        except Exception as e:
            logger.error(f"Error cleaning expired levels: {e}")

# Глобальный экземпляр сервиса
level_service = LevelService()