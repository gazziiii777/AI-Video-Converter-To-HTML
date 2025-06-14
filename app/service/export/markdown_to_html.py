import re
import os
import json
from app.client.claude import ClaudeClient
from config.config import IMG_HTML_CODE, PATH_TO_RESULTS_HTML, PATH_TO_ANALYSIS_RESULTS, OUTPUT_HTML_NAME, FILES_FOR_HTML
from app.service.media.text_on_image import TextOnImage
from app.service.browser.youtube_downloader import YouTubeDownloader


class MarkdownToHTMLConverter:
    def __init__(self):
        self.youtube_iframe = """
        <iframe allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                src="https://www.youtube-nocookie.com/embed/{video_id}?si=pu2-LwdzHJ8v5NlS"
                title="YouTube video player"
                loading="lazy"
                frameborder="0"
                class="sc-c59b7c5-2 jNytQI"
                width="800"
                height="450">
        </iframe>
        """
        self.path_to_results = PATH_TO_RESULTS_HTML

    def format_links(self, links_array):
        result = []
        for link_info in links_array:
            parts = []
            if len(link_info) >= 1:
                parts.append(str(link_info[0]))  # url
            if len(link_info) >= 2:
                parts.append(str(link_info[1]))  # title
            result.append(", ".join(parts))
        return "\n".join(result)

    def extract_answer(self, text: str) -> str:
        """
        Извлекает текст внутри тегов <answer> и </answer> из переданного текста.

        Args:
            text: Исходный текст, содержащий ответ в тегах <answer>

        Returns:
            Текст внутри тегов answer или пустая строка, если теги не найдены
        """
        match = re.search(r'<answer>(.*?)</answer>', text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def extract_youtube_id(self, url):
        """
        Извлекает идентификатор видео из URL YouTube.
        Работает с обычными URL (watch?v=...) и сокращенными URL (youtu.be/...).
        """
        # Проверяем стандартный URL с watch?v=
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        # Проверяем сокращенный URL youtu.be/
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        # Если URL не распознан, возвращаем None
        else:
            return None

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
                # Считаем количество решеток в начале строки
                level = len(line) - len(line.lstrip('#'))
                heading = line.lstrip('#').strip()
                heading = re.sub(r'Section \d+\.\s*', '', heading)

                # Определяем уровень заголовка
                if level == 1:
                    html_lines.append(f'<h2>{heading}</h2>')
                elif level == 2:
                    html_lines.append(f'<h3>{heading}</h3>')
                elif level == 3:
                    html_lines.append(f'<h4>{heading}</h4>')
                # Можно продолжить для более глубоких уровней
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

    async def _parse_input_data(self, answer):
        result = []
        lines = answer.strip().split('\n')

        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue

            # Check if line starts with a number (optionally followed by '. ')
            if not line[0].isdigit():
                print(f"Skipping line (doesn't start with digit): '{line}'")
                continue

            try:
                # Split on first occurrence of '. ' to remove numbering
                if '. ' in line:
                    content = line.split('. ', 1)[1]
                else:
                    # If no '. ', try to find the first space after the number
                    space_pos = line.find(' ')
                    if space_pos > 0:
                        content = line[space_pos+1:]
                    else:
                        content = line

                # Split filename and description
                if ' - ' in content:
                    filename, description = content.split(' - ', 1)
                else:
                    # Handle case where there's no description
                    filename = content.strip()
                    description = ""

                result.append([filename.strip(), description.strip()])
            except Exception as e:
                print(f"Error processing line: '{line}'. Error: {e}")
                continue

        return result

    async def _caption_and_image_for_section(self, img_description, output_files):
        client = ClaudeClient()
        content = ''

        for i, file_path in enumerate(output_files):

            if not os.path.exists(file_path):
                print(f"Файл {file_path} не найден, пропускаем...")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content += f.read()
        messages = [
            {"role": "user",
                "content": f"Read the content about the following product {content}. I am writing an e-commerce page with the following sections:\n1. What is the print quality and performance of the [Printer Name]?\n2. Which materials can you use with the [Printer Name]?\n3. What is the build volume of the [Printer Name]?\n4. What printer controls are available on the [Printer Name]?\n5. What connectivity options are available on the [Printer Name]?\n6. What software is offered with the [Printer Name]?\n7. What is the design and build quality of the [Printer Name]?\n8. What comes included in the box with [Printer Name]?\n9. What upgrades and accessories are available for the [Printer Name]?\n10. How reliable is the [Printer Name] and what maintenance does it require?\n11. What support and warranty come with the [Printer Name]?\n12. How much does the [Printer Name] cost?\nEACH SECTION CONTAINS AN IMAGE AT THE END. Create a compelling, benefit-focused caption (3-5 words) for this 3D printer product image that will appear on an e-commerce page. Your caption should: 1. Highlight a key feature or benefit of the product. 2. Be technically accurate. 3. Start with a Verb. 4. No fluff. 5. Use UPPER CASE formatting consistently. Don't write the text of the e-commerce product page itself. Only provide captions in a numbered list from 1 to 12. Avoid generic descriptions and ensure your caption would help sell the product by emphasizing its unique advantages or capabilities."}
        ]
        answer_1 = await client.ask_claude(
            max_tokens=4000,
            messages=messages,
            # file_name=f"data/prompts_out/photo_{prompt_counter}.txt"
        )
        messages.append(
            {"role": "assistant", "content": answer_1})
        messages.append(
            {"role": "user", "content": f"You have a set of content sections (with captions) and a list of image descriptions. For each section-keeping the original order-select the single most appropriate image. Each image may only be used once.\n\nInputs:\n\nContent / Captions: {answer_1}\n\nImage Descriptions: {img_description}\n\nRequirements:\n\nMatch each caption to the one image that best illustrates it.\n\nPreserve the original numbering/order of the captions.\n\nDo not reuse any image.\n\nOutput exactly in this format (one line per item): use only those images name that are in the Image Descriptions \n\n[section number]. [photo_name] - [caption]"})

        answer = await client.ask_claude(
            max_tokens=3000,
            messages=messages,
            # file_name=f"data/prompts_out/photo_{prompt_counter}.txt"
        )
        result = await self._parse_input_data(answer)
        return result

    async def _video_faunder(self, img_description, output_files):
        client = ClaudeClient()
        content = ''

        for i, file_path in enumerate(output_files):

            if not os.path.exists(file_path):
                print(f"Файл {file_path} не найден, пропускаем...")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content += f.read()
        messages = [
            {"role": "user",
                "content": f"Read the content about the following product {content}. I am writing an e-commerce page with the following sections:\n1. What is the print quality and performance of the [Printer Name]?\n2. Which materials can you use with the [Printer Name]?\n3. What is the build volume of the [Printer Name]?\n4. What printer controls are available on the [Printer Name]?\n5. What connectivity options are available on the [Printer Name]?\n6. What software is offered with the [Printer Name]?\n7. What is the design and build quality of the [Printer Name]?\n8. What comes included in the box with [Printer Name]?\n9. What upgrades and accessories are available for the [Printer Name]?\n10. How reliable is the [Printer Name] and what maintenance does it require?\n11. What support and warranty come with the [Printer Name]?\n12. How much does the [Printer Name] cost?\nEACH SECTION CONTAINS AN IMAGE AT THE END. Create a compelling, benefit-focused caption (3-5 words) for this 3D printer product image that will appear on an e-commerce page. Your caption should: 1. Highlight a key feature or benefit of the product. 2. Be technically accurate. 3. Start with a Verb. 4. No fluff. 5. Use UPPER CASE formatting consistently. Don't write the text of the e-commerce product page itself. Only provide captions in a numbered list from 1 to 12. Avoid generic descriptions and ensure your caption would help sell the product by emphasizing its unique advantages or capabilities."}
        ]
        answer_1 = await client.ask_claude(
            max_tokens=4000,
            messages=messages,
            # file_name=f"data/prompts_out/photo_{prompt_counter}.txt"
        )
        messages.append(
            {"role": "assistant", "content": answer_1})
        messages.append(
            {"role": "user", "content": f"You have a set of content sections (with captions) and a list of image descriptions. For each section-keeping the original order-select the single most appropriate image. Each image may only be used once.\n\nInputs:\n\nContent / Captions: {answer_1}\n\nImage Descriptions: {img_description}\n\nRequirements:\n\nMatch each caption to the one image that best illustrates it.\n\nPreserve the original numbering/order of the captions.\n\nDo not reuse any image.\n\nOutput exactly in this format (one line per item): use only those images name that are in the Image Descriptions \n\n[section number]. [photo_name] - [caption]"})

        answer = await client.ask_claude(
            max_tokens=3000,
            messages=messages,
            # file_name=f"data/prompts_out/photo_{prompt_counter}.txt"
        )
        result = await self._parse_input_data(answer)
        return result

    async def combine_files_to_html(self, output_files, output_path="combined.html", img_description=None):
        """Объединяет файлы в один HTML"""
        client = ClaudeClient()
        used_images = set()
        # text_on_image = TextOnImage()
        img_and_desk = await self._caption_and_image_for_section(img_description, output_files)

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
                if len(lines) > 1:  # Если есть хотя бы две строки (первая + остальное)
                    lines = lines[1:]  # Удаляем первую строку
                # Собираем обратно с двумя переносами
                content = '\n'.join(lines) + "\n\n"
                video_from_channel = await YouTubeDownloader().parse_channel_videos()
                video_from_search = await YouTubeDownloader().search("Prusa CORE One Review", True)

                formatted_video_from_channel = self.format_links(
                    video_from_channel)
                formatted_video_from_search = self.format_links(
                    video_from_search)

                messages = [
                    {"role": "user",
                     "content": f"PROMPT:  You are tasked with selecting a YouTube review video for a product page. Your objective is to choose the most appropriate video based on specific criteria. The product name is: <product_name> 'Prusa CORE One' </product_name> Here are the videos from Top 3D Shop's YouTube Channel: <top3dshop_youtube_videos> YouTube Link Vidio Title {formatted_video_from_channel} </top3dshop_youtube_videos> Here are the videos from YouTube search for Prusa CORE One <search_results> YouTube Link Vidio Title Author of the video {formatted_video_from_search} </search_results> Analyze the search results and select one YouTube review video based on the following criteria, in order of priority: 1. If a video by Top 3D Shop exists, select that video (in English). 2. If a video by the manufacturer exists, select that video. 3. If no Top 3D Shop or manufacturer video is available, select the most comprehensive and highly-rated review. Important requirements: - Select only one YouTube review video specifically relevant to the product name. - Exclude videos about previous generations or significantly different versions. - Output only the final selected video URL as a clickable link, with no additional text or explanation. - The output must be a clean YouTube link in the format: https://www.youtube.com/watch?v=XXXXXXXXXXX - Remove any extra URL parameters (such as &pp, &t=, etc.)—the link must contain only the base ?v= parameter. - Do not include any tags, timestamps, or formatting other than the clickable link. - Do not include any explanations, self-references, or additional output. Your final output should be in the following format: <answer> [The selected YouTube video URL] </answer> "}
                ]
                answer = await client.ask_claude_web(
                    max_tokens=4000,
                    messages=messages,
                )
                answer_clear = self.extract_answer(answer)
                clear_video_id = self.extract_youtube_id(answer_clear)

                iframe_template = self.youtube_iframe.format(
                    video_id=clear_video_id)

                html_content += self.convert_md_to_html(
                    content) + iframe_template + "\n<hr>\n"
                continue
            else:
                # max_attempts = 5
                # attempt = 0
                # file_name_answer = None

                # while attempt < max_attempts:
                #     messages = [
                #         {"role": "user", "content": f"Tell me which picture best fits the context: {content}. In response, write only the name of the picture"}
                #     ]
                #     messages.append(
                #         {"role": "user", "content": f"Description of the art and file name {img_description}"}
                #     )
                #     if file_name_answer is not None:
                #         messages.append(
                #             {"role": "user",
                #                 "content": f"Don`t use images with names {used_images}"}
                #         )
                #     file_name_answer = await client.ask_claude(20, messages)
                #     file_name_answer_without_ext = file_name_answer.split('.')[
                #         0]

                #     if file_name_answer_without_ext not in used_images:
                #         used_images.add(file_name_answer_without_ext)
                #         break  # нашли уникальное изображение
                #     else:
                #         print(
                #             f"Изображение '{file_name_answer}' уже использовано, пробуем снова...")
                #         attempt += 1

                # if attempt == max_attempts:
                #     print(
                #         "Не удалось получить уникальное изображение после нескольких попыток.")
                #     html_content += self.convert_md_to_html(
                #         content) + "\n<hr>\n"
                #     continue

                # if file_name_answer_without_ext.isdigit():
                #     desc = await self.get_description_by_filename(file_name_answer, img_description)
                #     messages = [
                #         {"role": "user", "content": f"Create a compelling, benefit-focused caption (3-5 words) for this 3D printer product image that will appear on an e-commerce text: {content}. Your caption should: 1. Highlight a key feature or benefit of the product 2. Be technically accurate 3. Start with a Verb. 4. No fluff. 5. Use UPPER CASE formatting consistently Don’t write the text of the e-commerce product page itself. Avoid generic descriptions and ensure your caption would help sell the product by emphasizing its unique advantages or capabilities"}
                #     ]
                #     desc_answer = await client.ask_claude(100, messages)
                #     processor1 = TextOnImage(
                #         filename=file_name_answer,
                #         text=desc_answer,
                #     )
                #     new_filename = file_name_answer_without_ext + "_new.jpg"
                #     processor1.process(new_filename)
                #     html_content += self.convert_md_to_html(
                #         content) + img_html_code.format(img=f"img/{new_filename}") + "\n<hr>\n"
                #     continue
                # else:
                #     html_content += self.convert_md_to_html(
                #         content) + "\n<hr>\n"
                # continue

                processor1 = TextOnImage(
                    filename=img_and_desk[i-1][0],
                    text=img_and_desk[i-1][1],
                )
                new_filename = img_and_desk[i-1][0].split('.')[0] + "_new.jpg"
                processor1.process(new_filename)
                html_content += self.convert_md_to_html(
                    content) + IMG_HTML_CODE.format(img=f"img/{new_filename}") + "\n<hr>\n"
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

    async def _create_file_html(self, files_to_combine):
        pass

    async def process_files(self, file_numbers=None, max_attempts=5):
        """
        Основной метод для обработки файлов с повторными попытками при ошибках
        :param file_numbers: список номеров файлов (например, [4, 8, 12])
        :param max_attempts: максимальное количество попыток выполнения (по умолчанию 5)
        """
        html_output_path = self.path_to_results + OUTPUT_HTML_NAME + '.html'
        txt_output_path = self.path_to_results + OUTPUT_HTML_NAME + '.txt'
        img_description = self._load_json_data(PATH_TO_ANALYSIS_RESULTS)

        if file_numbers is None:
            file_numbers = FILES_FOR_HTML

        files_to_combine = [
            f"{self.path_to_results}prompts_out/output_prompt_{num}.txt" for num in file_numbers
        ]

        if not files_to_combine:
            print("Не указаны номера файлов для обработки.")
            return False

        attempt = 0
        last_error = None

        while attempt < max_attempts:
            attempt += 1
            try:
                # Создаем HTML файл
                await self.combine_files_to_html(
                    files_to_combine, html_output_path, img_description=img_description)

                # Дополнительно создаем TXT файл
                # await self._combine_files_to_txt(
                #     files_to_combine, txt_output_path, img_description=img_description)

                print(
                    f"Файлы успешно обработаны (попытка {attempt}/{max_attempts})")
                return True

            except Exception as e:
                last_error = e
                print(
                    f"Ошибка при обработке (попытка {attempt}/{max_attempts}): {str(e)}")
                if attempt < max_attempts:
                    print("Повторная попытка...")

        print(
            f"Достигнуто максимальное количество попыток ({max_attempts}). Обработка не удалась.")
        print(f"Последняя ошибка: {str(last_error)}")
        return False

        # html_output_path = self.path_to_results + 'combined_with_quotes.html'

        # files_to_combine = [
        #     f"{self.path_to_results}prompts_out_with_quotes/output_prompt_{num}.txt" for num in file_numbers
        # ]

        # if not files_to_combine:
        #     print("Не указаны номера файлов для обработки.")
        # else:
        #     # Создаем HTML файл (как было раньше)
        #     await self.combine_files_to_html(
        #         files_to_combine, html_output_path, img_description=img_description)

        #     # Дополнительно создаем TXT файл
        #     await self._combine_files_to_txt(
        #         files_to_combine, txt_output_path, img_description=img_description)


if __name__ == "__main__":
    converter = MarkdownToHTMLConverter()
    converter.process_files()
