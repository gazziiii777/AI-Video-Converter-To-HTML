import whisper
import os
from pydub import AudioSegment
from moviepy import VideoFileClip
from typing import Optional, List


class MediaTranscriber:
    def __init__(self, model_name: str = "base", language: str = "ru"):
        """
        Инициализация транскрибатора медиафайлов.

        Параметры:
            model_name (str): Модель Whisper (tiny, base, small, medium, large)
            language (str): Язык для транскрибации (например, "ru", "en")
        """
        self.model_name = model_name
        self.language = language
        self.model = None

    def load_model(self) -> None:
        """Загружает модель Whisper."""
        print(f"Загружаем модель '{self.model_name}'...")
        self.model = whisper.load_model(self.model_name)

    def extract_audio(
        self,
        video_path: str,
        audio_path: str = "output_audio.wav",
        sample_rate: int = 16000,
    ) -> str:
        """
        Извлекает аудио из видео с помощью moviepy.

        Параметры:
            video_path (str): Путь к видеофайлу.
            audio_path (str): Куда сохранить аудио (поддерживает WAV, MP3).
            sample_rate (int): Частота дискретизации.

        Возвращает:
            str: Абсолютный путь к сохранённому аудиофайлу.
        """
        try:
            video = VideoFileClip(video_path)
            audio = video.audio

            audio.write_audiofile(
                audio_path,
                fps=sample_rate,
                codec="pcm_s16le",
            )

            audio.close()
            video.close()

            return os.path.abspath(audio_path)

        except Exception as e:
            raise RuntimeError(f"Ошибка при извлечении аудио: {e}")

    @staticmethod
    def format_time(seconds: float) -> str:
        """Конвертирует секунды в формат SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")

    def transcribe_file(
        self,
        input_path: str,
        output_txt: str = "transcription.txt",
        output_srt: str = "transcription.srt",
    ) -> dict:
        """
        Транскрибирует аудио/видео файл.

        Параметры:
            input_path (str): Путь к входному файлу.
            output_txt (str): Имя файла для текстовой транскрипции.
            output_srt (str): Имя файла для субтитров (SRT).

        Возвращает:
            dict: Результат транскрибации от Whisper.
        """
        if self.model is None:
            self.load_model()

        # Извлекаем аудио если это видео
        if input_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            print(f"Извлекаем аудио из видео {input_path}...")
            audio_path = self.extract_audio(input_path)
            is_temp_audio = True
        else:
            audio_path = input_path
            is_temp_audio = False

        try:
            print("Идёт транскрибация... (это может занять время)")
            result = self.model.transcribe(
                audio_path, language=self.language, word_timestamps=True)

            # Сохраняем результаты
            self._save_results(result, output_txt, output_srt)

            return result

        finally:
            # Удаляем временный аудиофайл если он был создан
            if is_temp_audio and os.path.exists(audio_path):
                os.remove(audio_path)

    def _save_results(
        self,
        result: dict,
        output_txt: str,
        output_srt: str
    ) -> None:
        """Сохраняет результаты транскрибации в файлы."""
        # Создаем папки если их нет
        os.makedirs("txt_output", exist_ok=True)
        os.makedirs("srt_output", exist_ok=True)

        # Полные пути к файлам
        txt_path = os.path.join("txt_output", output_txt)
        srt_path = os.path.join("srt_output", output_srt)

        # Сохраняем текст
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"Текст сохранён в {txt_path}")

        # Сохраняем субтитры
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(result["segments"]):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                f.write(
                    f"{i+1}\n{self.format_time(start)} --> {self.format_time(end)}\n{text}\n\n")
        print(f"Субтитры сохранены в {srt_path}")

    def process_folder(
        self,
        folder_path: str,
        output_prefix: str = "transcription_",
        extensions: tuple = ('.mp4', '.avi', '.mov', '.mkv')
    ) -> List[str]:
        """
        Обрабатывает все файлы с указанными расширениями в папке.

        Параметры:
            folder_path (str): Путь к папке с файлами.
            output_prefix (str): Префикс для выходных файлов.
            extensions (tuple): Кортеж поддерживаемых расширений.

        Возвращает:
            List[str]: Список обработанных файлов.
        """
        if not os.path.isdir(folder_path):
            raise ValueError(f"Папка {folder_path} не существует")

        media_files = [
            f for f in os.listdir(folder_path)
            if f.lower().endswith(extensions)
        ]

        if not media_files:
            print(
                f"В папке {folder_path} не найдено файлов с расширениями {extensions}")
            return []

        print(f"Найдено {len(media_files)} файлов для обработки:")
        processed_files = []

        for i, media_file in enumerate(media_files, 1):
            media_path = os.path.join(folder_path, media_file)
            print(f"\nОбработка файла {i} из {len(media_files)}: {media_file}")

            base_name = os.path.splitext(media_file)[0]
            output_txt = f"{output_prefix}{base_name}.txt"
            output_srt = f"{output_prefix}{base_name}.srt"

            try:
                self.transcribe_file(
                    input_path=media_path,
                    output_txt=output_txt,
                    output_srt=output_srt,
                )
                processed_files.append(media_path)
            except Exception as e:
                print(f"Ошибка при обработке файла {media_file}: {e}")
                continue

        return processed_files

    import os

    def merge_txt_files(self, folder_path='txt_output') -> str:
        merged_text = []
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    merged_text.append(f.read())

        return '\n'.join(merged_text)


if __name__ == "__main__":
    # Пример использования
    transcriber = MediaTranscriber(
        model_name="base",  # Для русского лучше 'small' или 'medium'
        language="en"       # Язык для транскрибации
    )

    # Обработка папки с видео
    # transcriber.process_folder(
    #     folder_path="videos",
    #     output_prefix="result_"
    # )

    a = transcriber.merge_txt_files()
    print(a)
