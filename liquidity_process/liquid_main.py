import asyncio
import sys
sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main\liquidity_process")
import detect_liquid

async def process_timeframe(tf):
    """Обработка одного таймфрейма"""
    detect = detect_liquid.Detector_liquid(tf)
    result = await detect.start_detection()
    print(f"Таймфрейм {tf} завершен: {result}")
    return result

async def liquidity_main():
    timeframes = ['5m','15m', '1h', '4h']

    # Создаем задачи для всех таймфреймов
    tasks = []
    for tf in timeframes:
        task = asyncio.create_task(process_timeframe(tf))
        tasks.append(task)

    # Ожидаем завершения всех задач
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Обрабатываем результаты
    for tf, result in zip(timeframes, results):
        if isinstance(result, Exception):
            print(f"Ошибка в таймфрейме {tf}: {result}")
        else:
            print(f"Таймфрейм {tf} - результат: {result}")

    return results

# Запуск
if __name__ == "__main__":
    results = asyncio.run(liquidity_main())
    print("Все задачи завершены:", results)