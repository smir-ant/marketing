import requests
from bs4 import BeautifulSoup
import json
from django.core.management.base import BaseCommand

import os
from dotenv import load_dotenv
load_dotenv()

class Command(BaseCommand):
    help = "Получает выдачу Yandex через сервис xmlriver, парсит результаты и сохраняет их в JSON-файл."

    def handle(self, *args, **kwargs):
        BASE_URL = (
            "http://xmlriver.com/search_yandex/xml?raw=page"
            "&lr=1&device=desktop&query=кредит+наличными+быстро"
            f"&user={os.getenv("USER_ID")}&key={os.getenv("KEY")}"
        )
        self.stdout.write("Отправка запроса к xmlriver...")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            raw_html = response.text
            soup = BeautifulSoup(raw_html, "lxml")


            # HTML для анализа
            # with open("output.html", "w", encoding="utf-8") as file:
            #     file.write(soup.prettify())

            # Выбираем элементы с классами .serp-item и .serp-item_card
            serp_items = soup.select('.serp-item.serp-item_card')

            data_fast_1_count = 0
            data_fast_2_count = 0
            results = []

            # заметил закономерность, что вроде как с рекламой имеют data-fast=2, 
            # а органические data-fast=1
            for item in serp_items:
                data_fast = item.get('data-fast')
                if data_fast == "1":
                    data_fast_1_count += 1
                    result_type = "органика"
                elif data_fast == "2":
                    data_fast_2_count += 1
                    result_type = "реклама"
                else:
                    result_type = "неизвестно"

                # Извлекаем заголовок из тега h2 (объединяем текст из вложенных тегов)
                h2_tag = item.find('h2')
                title = ' '.join(h2_tag.stripped_strings) if h2_tag else 'Без заголовка'

                # Извлекаем ссылку из тега a с классом "Link" и отсеиваем пустые-некорретные ссылки
                link_tag = item.find('a', class_='Link')
                if link_tag == "" or title == "Без заголовка":
                    continue 
                else:
                    url = link_tag.get('href')
                results.append({
                    "title": title,
                    "url": url,
                    "type": result_type
                })

            self.stdout.write(f'Количество элементов с data-fast="1": {data_fast_1_count}')
            self.stdout.write(f'Количество элементов с data-fast="2": {data_fast_2_count}')

            # Сохраняем результаты в JSON-файл
            with open("results.json", "w", encoding="utf-8") as json_file:
                json.dump(results, json_file, ensure_ascii=False, indent=4)

            self.stdout.write(self.style.SUCCESS("Результаты успешно сохранены в файл results.json"))
        else:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при выполнении запроса. Статус-код: {response.status_code}"
            ))
