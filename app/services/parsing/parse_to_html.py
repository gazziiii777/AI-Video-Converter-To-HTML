import re
import os


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
        self.path_to_results = 'D:/pythonProject/AI-Video-Converter-To-HTML/results/'

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
                if '---' not in line and ('Build Volume' in line or '3D Printer Model' in line):
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

    def combine_files_to_html(self, output_files, output_path="combined.html"):
        """Объединяет файлы в один HTML"""
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

            html_content += self.convert_md_to_html(content) + "\n<hr>\n"

        html_content += "</body></html>"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Результат сохранён в файл: {output_path}")

    def process_files(self, file_numbers=None):
        """
        Основной метод для обработки файлов
        :param file_numbers: список номеров файлов (например, [4, 8, 12])
        :param output_path: путь к выходному файлу
        """
        output_path = self.path_to_results + 'combined.html'

        if file_numbers is None:
            file_numbers = [4, 8, 12, 16, 20, 24, 28, 31, 35, 39, 43, 47, 51]

        files_to_combine = [
            f"{self.path_to_results}prompts_out/output_prompt_{num}.txt" for num in file_numbers
        ]

        if not files_to_combine:
            print("Не указаны номера файлов для обработки.")
        else:
            self.combine_files_to_html(files_to_combine, output_path)


if __name__ == "__main__":
    converter = MarkdownToHTMLConverter()

    # Пример 1: С значениями по умолчанию
    # converter.process_files()

    # Пример 2: С указанием конкретных номеров файлов
    converter.process_files()

    # Пример 3: С указанием выходного файла
    # converter.process_files(file_numbers=[4, 8, 12], output_path="my_output.html")
