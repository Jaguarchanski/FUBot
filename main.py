from funding_sources import get_all_funding
import time

if __name__ == "__main__":
    print("🚀 Funding monitor started")

    while True:
        data = get_all_funding()

        print(f"Total funding entries: {len(data)}")

        # ТУТ ДАЛІ БУДЕ TELEGRAM
        # поки просто перевіряємо що ВСЕ ПРАЦЮЄ

        time.sleep(60)
