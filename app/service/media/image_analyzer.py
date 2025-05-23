import os
import json
from pathlib import Path
from typing import List, Dict
from PIL import Image
import imagehash
from config.config import SUPPORTED_IMAGE_FORMATS, PATH_TO_IMG

class ImageProcessor:
    def __init__(self, gpt_client):
        self.gpt_client = gpt_client
        self.batch_size = 3
        self.SUPPORTED_IMAGE_FORMATS = SUPPORTED_IMAGE_FORMATS

    async def process_directory(self, image_dir: str, output_file: str):
        """Обрабатывает все изображения в директории"""
        all_results = []

        # Фильтрация изображений по поддерживаемым форматам
        image_paths = [
            str(p) for p in Path(image_dir).glob("*")
            if p.is_file() and p.suffix.lower() in self.SUPPORTED_IMAGE_FORMATS
        ]

        if not image_paths:
            print("⚠️ No supported images found in directory!")
            return

        print(f"Found {len(image_paths)} supported images to process")

        for i in range(0, len(image_paths), self.batch_size):
            batch = image_paths[i:i + self.batch_size]
            print(f"Processing batch {i//self.batch_size + 1}...")

            try:
                instruction = "These are all pictures related to 3D printer. Describe what is in each image (in max detail). If this is a print sample, state so. Format: '1: [description]', '2: [description]', ..."
                descriptions = await self.gpt_client.analyze_images_batch(batch, instruction)
                batch_results = self._parse_descriptions(descriptions, batch)
                all_results.extend(batch_results)
                self._save_results(all_results, output_file)

            except Exception as e:
                print(
                    f"⚠️ Error processing batch {i//self.batch_size + 1}: {e}")
                # Пропускаем проблемный батч или обрабатываем отдельно
                continue

    def _parse_descriptions(self, text: str, paths: List[str]) -> List[Dict]:
        """Парсит ответ LLM в структурированный формат"""
        results = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if i < len(paths):
                results.append({
                    "image": os.path.basename(paths[i]),
                    "description": line.split(":", 1)[-1].strip()
                })
        return results

    def _save_results(self, results: List[Dict], output_file: str):
        """Сохраняет результаты в JSON файл"""
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
    async def delete_duplicates(self):
        # Папка с изображениями
        folder = PATH_TO_IMG
        hashes = {}
        duplicates = []

        threshold = 20  # Допуск на различие в хэшах

        for filename in os.listdir(folder):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                continue
            filepath = os.path.join(folder, filename)
            try:
                with Image.open(filepath) as img:
                    hash = imagehash.phash(img)
                    duplicate_found = False
                    for existing_hash in hashes:
                        if abs(hash - existing_hash) <= threshold:
                            print(f"Дубликат найден: {filename} ≈ {hashes[existing_hash]}")
                            duplicates.append(filepath)
                            duplicate_found = True
                            break
                    if not duplicate_found:
                        hashes[hash] = filename
            except Exception as e:
                print(f"Ошибка с {filename}: {e}")

        # Удаление найденных дубликатов
        for dup in duplicates:
            try:
                os.remove(dup)
                print(f"Удалено: {dup}")
            except Exception as e:
                print(f"Не удалось удалить {dup}: {e}")


