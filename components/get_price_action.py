def get_price():
    with open('C:\QUIK_DATA\price.txt', 'r') as price_file:
        content = price_file.read()
        try:
            # Удаляем лишние пробелы и разбиваем по точке с запятой
            pairs = content.strip().split(';')

            result = {}
            for pair in pairs:
                # Разбиваем каждую пару по слешу
                if ':' in pair:
                    key, value = pair.strip().split(':')
                    # Преобразуем значение в float
                    result[key] = float(value)

            return result

        except Exception as e:
            print(f"Ошибка при парсинге строки: {e}")
            return {}