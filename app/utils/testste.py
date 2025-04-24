from PIL import Image, ImageDraw, ImageFont
import os


class TextOnImage:
    def __init__(
        self,
        filename: str,
        text: str,
        text_color: tuple = (255, 255, 255),
        background_color: tuple = (0, 0, 0),
        padding: int = 20,
        font_size: int = 40,
        font_path: str = "arial.ttf",
        bottom_margin: int = 40,
        text_position_ratio: float = 1/3,
        fixed_folder: str = "data/img"
    ):
        """
        Класс для добавления текста с подложкой на изображение.

        :param filename: Имя файла изображения
        :param text: Текст для добавления
        :param text_color: Цвет текста (RGB)
        :param background_color: Цвет подложки (RGB)
        :param padding: Отступ текста от краев подложки
        :param font_size: Размер шрифта
        :param font_path: Путь к файлу шрифта
        :param bottom_margin: Отступ подложки от нижнего края изображения
        :param text_position_ratio: Положение текста по вертикали (0-1)
        :param fixed_folder: Фиксированная папка для поиска изображения
        """
        self.image_path = self.find_image(filename, fixed_folder)
        self.text = text
        self.text_color = text_color
        self.background_color = background_color
        self.padding = padding
        self.font_size = font_size
        self.font_path = font_path
        self.bottom_margin = bottom_margin
        self.text_position_ratio = text_position_ratio

        self.image = None
        self.draw = None
        self.font = None

    def find_image(self, filename: str, fixed_folder: str = None) -> str:
        """Ищет файл изображения в указанной папке"""
        if fixed_folder:
            # Проверяем абсолютный это путь или относительный
            if not os.path.isabs(fixed_folder):
                # Если путь относительный, преобразуем в абсолютный
                fixed_folder = os.path.abspath(fixed_folder)

            full_path = os.path.join(fixed_folder, filename)
            if os.path.exists(full_path):
                return full_path
            raise FileNotFoundError(
                f"Файл '{filename}' не найден в папке '{fixed_folder}'")

        # Если папка не указана, ищем в текущей директории
        for file in os.listdir('.'):
            if file.lower() == filename.lower():
                return file
        raise FileNotFoundError(f"Файл '{filename}' не найден в текущей папке")

    def load_image(self):
        """Загружает изображение и создает объект для рисования"""
        self.image = Image.open(self.image_path)
        self.draw = ImageDraw.Draw(self.image)

    def load_font(self):
        """Загружает шрифт"""
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except IOError:
            self.font = ImageFont.load_default()

    def calculate_dimensions(self):
        """Вычисляет размеры текста и подложки"""
        text_bbox = self.draw.textbbox((0, 0), self.text, font=self.font)
        self.text_width = text_bbox[2] - text_bbox[0]
        self.text_height = text_bbox[3] - text_bbox[1]

        self.box_width = self.text_width + 2 * self.padding
        self.box_height = self.text_height + 2 * self.padding

    def calculate_positions(self):
        """Вычисляет позиции подложки и текста"""
        image_width, image_height = self.image.size
        self.box_x = 0
        self.box_y = image_height - self.box_height - self.bottom_margin

        self.text_x = self.box_x + (self.box_width - self.text_width) // 2
        self.text_y = self.box_y + \
            (self.box_height - self.text_height) * self.text_position_ratio

    def draw_elements(self):
        """Рисует подложку и текст"""
        self.draw.rectangle(
            [(self.box_x, self.box_y), (self.box_x +
                                        self.box_width, self.box_y + self.box_height)],
            fill=self.background_color
        )
        self.draw.text((self.text_x, self.text_y), self.text,
                       font=self.font, fill=self.text_color)

    def save_image(self, output_path: str = "output.jpg"):
        """Сохраняет результат"""
        self.image.save(output_path)
        print(f"Текст с подложкой добавлен! Результат: {output_path}")

    def process(self, output_path: str = "data/img/output.jpg"):
        """Основной метод обработки"""
        self.load_image()
        self.load_font()
        self.calculate_dimensions()
        self.calculate_positions()
        self.draw_elements()
        self.save_image(output_path)


# Пример использования с файлом в data/img/
if __name__ == "__main__":
    # Вариант 1: Используем относительный путь
    processor1 = TextOnImage(
        filename="17.jpg",
        text="Текст на изображении",
    )
    processor1.process()

    # # Вариант 2: Используем абсолютный путь
    # processor2 = TextOnImage(
    #     filename="example.jpg",
    #     text="Текст на изображении",
    #     fixed_folder=os.path.abspath("data/img")  # Абсолютный путь к папке
    # )
    # processor2.process("result2.jpg")
