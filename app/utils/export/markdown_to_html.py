import re
import os
import json
from app.client.claude import ClaudeClient
from config import img_html_code
from app.utils.media.text_on_image import TextOnImage


class MarkdownToHTMLConverter:
    def __init__(self):
        self.youtube_iframe = """
        <iframe allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                src="https://www.youtube-nocookie.com/embed/O04RM-KCP68?si=pu2-LwdzHJ8v5NlS"
                title="YouTube video player"
                loading="lazy"
                frameborder="0"
                class="sc-c59b7c5-2 jNytQI">
        </iframe>
        """
        self.path_to_results = 'data/'

    def convert_md_to_html(self, text):
        """Конвертирует Markdown-подобное форматирование в HTML"""
        # Удаляем "Section {num}." из заголовков
        text = re.sub(r'Section \d+\.\s*', '', text)

        # Заменяем **текст** на <h3>текст</h3>
        text = re.sub(r'\*\*(.*?)\*\*', r'<h3>\1</h3>', text)

        # Обрабатываем списки: строки, начинающиеся с "-"
        lines = text.split('\n')
        in_list = False
        in_table = False
        html_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                heading = line.lstrip('#').strip()
                heading = re.sub(r'Section \d+\.\s*', '', heading)
                html_lines.append(f'<h2>{heading}</h2>')
                continue

            # Обработка таблицы
            if '|' in line:
                if '---' not in line and not in_table:
                    if not in_table:
                        html_lines.append('<table border="1">')
                        in_table = True
                    html_lines.append('<tr>')
                    for cell in line.split('|')[1:-1]:
                        html_lines.append(f'<th>{cell.strip()}</th>')
                    html_lines.append('</tr>')
                elif '---' in line:
                    continue
                else:
                    html_lines.append('<tr>')
                    for cell in line.split('|')[1:-1]:
                        html_lines.append(f'<td>{cell.strip()}</td>')
                    html_lines.append('</tr>')
                continue

            if line.startswith('-'):
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[1:].strip()}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                if in_table:
                    html_lines.append('</table>')
                    in_table = False
                if line and not any(c in line for c in ['|', '---']):
                    html_lines.append(f'<p>{line}</p>')

        if in_list:
            html_lines.append('</ul>')
        if in_table:
            html_lines.append('</table>')

        return '\n'.join(html_lines)

    async def get_description_by_filename(self, filename, data):
        data_1 = json.loads(data)
        for item in data_1:
            if item["image"] == filename:
                return item["description"]
        return None  # если файл не найден


    async def _caption_and_image_for_section(self, img_description):
        pass
    
    async def combine_files_to_html(self, output_files, output_path="combined.html", img_description=None):
        """Объединяет файлы в один HTML"""
        client = ClaudeClient()
        used_images = set()
        # text_on_image = TextOnImage()
        html_content = """<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Combined Output</title>
                <style>
                    table { border-collapse: collapse; margin: 15px 0; width: 100%; }
                    th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                    h2 { margin-top: 30px; color: #333; }
                    p { line-height: 1.5; }
                </style>
            </head>
            <body>
            """

        for i, file_path in enumerate(output_files):

            if not os.path.exists(file_path):
                print(f"Файл {file_path} не найден, пропускаем...")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if i == 0:  # Только для первого файла
                lines = content.split('\n')  # Разбиваем текст на строки
                if lines:  # Если есть хотя бы одна строка
                    # Обрабатываем только первую строку
                    first_line = lines[0]
                    if ':' in first_line:
                        # Добавляем # в начало строки после обработки
                        lines[0] = "# " + first_line.split(':', 1)[1].lstrip()
                content = '\n'.join(lines)  # Собираем обратно
                content += "\n\n"
                html_content += self.convert_md_to_html(
                    content) + self.youtube_iframe + "\n<hr>\n"
                continue
            else:
                max_attempts = 5
                attempt = 0
                file_name_answer = None

                while attempt < max_attempts:
                    messages = [
                        {"role": "user", "content": f"Tell me which picture best fits the context: {content}. In response, write only the name of the picture"}
                    ]
                    messages.append(
                        {"role": "user", "content": f"Description of the art and file name {img_description}"}
                    )
                    if file_name_answer is not None:
                        messages.append(
                            {"role": "user", "content": f"Don`t use images with names {used_images}"}
                        )
                    file_name_answer = await client.ask_claude(20, messages)
                    file_name_answer_without_ext = file_name_answer.split('.')[0]

                    if file_name_answer_without_ext not in used_images:
                        used_images.add(file_name_answer_without_ext)
                        break  # нашли уникальное изображение
                    else:
                        print(f"Изображение '{file_name_answer}' уже использовано, пробуем снова...")
                        attempt += 1

                if attempt == max_attempts:
                    print("Не удалось получить уникальное изображение после нескольких попыток.")
                    html_content += self.convert_md_to_html(content) + "\n<hr>\n"
                    continue

                if file_name_answer_without_ext.isdigit():
                    desc = await self.get_description_by_filename(file_name_answer, img_description)
                    messages = [
                        {"role": "user", "content": f"Create a compelling, benefit-focused caption (3-5 words) for this 3D printer product image that will appear on an e-commerce text: {content}. Your caption should: 1. Highlight a key feature or benefit of the product 2. Be technically accurate 3. Start with a Verb. 4. No fluff. 5. Use UPPER CASE formatting consistently Don’t write the text of the e-commerce product page itself. Avoid generic descriptions and ensure your caption would help sell the product by emphasizing its unique advantages or capabilities"}
                    ]
                    desc_answer = await client.ask_claude(100, messages)
                    processor1 = TextOnImage(
                        filename=file_name_answer,
                        text=desc_answer,
                    )
                    new_filename = file_name_answer_without_ext + "_new.jpg"
                    processor1.process(new_filename)
                    html_content += self.convert_md_to_html(
                        content) + img_html_code.format(img=f"img/{new_filename}") + "\n<hr>\n"
                    continue
                else:
                    html_content += self.convert_md_to_html(
                        content) + "\n<hr>\n"
                continue


            # html_content += self.convert_md_to_html(content) + "\n<hr>\n"

        html_content += "</body></html>"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Результат сохранён в файл: {output_path}")

    def _load_json_data(self, file_path):
        """
        Загружает данные из JSON-файла и возвращает их в виде строки

        :param file_path: Путь к JSON-файлу
        :return: Строка с содержимым JSON-файла или None при ошибке
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Читаем содержимое файла как строку
                json_string = file.read()
                # Дополнительная проверка, что это валидный JSON
                # Проверяем, но не используем результат
                json.loads(json_string)
                return json_string
        except FileNotFoundError:
            print(f"Ошибка: Файл {file_path} не найден")
            return None
        except json.JSONDecodeError:
            print(f"Ошибка: Файл {file_path} содержит некорректный JSON")
            return None

    async def _combine_files_to_txt(self, file_paths, output_path, img_description=None):
        """
        Объединяет содержимое нескольких файлов в один текстовый файл
        :param file_paths: список путей к файлам
        :param output_path: путь к выходному файлу
        :param img_description: описание изображений (необязательно)
        """
        with open(output_path, 'w', encoding='utf-8') as out_file:
            # Если нужно, можно добавить заголовок или метаинформацию
            # if img_description:
            #     out_file.write("Описания изображений:\n")
            #     for img_id, desc in img_description.items():
            #         out_file.write(f"{img_id}: {desc}\n")
            #     out_file.write("\n" + "="*50 + "\n\n")

            # Объединяем содержимое всех файлов
            for i, file_path in enumerate(file_paths):
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_file:
                        content = in_file.read()
                        out_file.write(f"=== Файл {i+1} ===\n")
                        out_file.write(content)
                        # Добавляем разделитель между файлами
                        out_file.write('\n\n')
                except FileNotFoundError:
                    print(f"Файл не найден: {file_path}")
                except Exception as e:
                    print(f"Ошибка при обработке файла {file_path}: {e}")

    async def process_files(self, file_numbers=None):
        """
        Основной метод для обработки файлов
        :param file_numbers: список номеров файлов (например, [4, 8, 12])
        """
        html_output_path = self.path_to_results + 'combined.html'
        txt_output_path = self.path_to_results + 'combined.txt'
        img_description = self._load_json_data(
            'data/img/analysis_results.json')

        if file_numbers is None:
            file_numbers = [3, 7, 11, 15, 19, 23, 27, 30, 34, 38, 42]

        files_to_combine = [
            f"{self.path_to_results}prompts_out/output_prompt_{num}.txt" for num in file_numbers
        ]

        if not files_to_combine:
            print("Не указаны номера файлов для обработки.")
        else:
            # Создаем HTML файл (как было раньше)
            await self.combine_files_to_html(
                files_to_combine, html_output_path, img_description=img_description)

            # Дополнительно создаем TXT файл
            await self._combine_files_to_txt(
                files_to_combine, txt_output_path, img_description=img_description)


if __name__ == "__main__":
    converter = MarkdownToHTMLConverter()
    converter.process_files()
