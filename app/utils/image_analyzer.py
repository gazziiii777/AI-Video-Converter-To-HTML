import os
import json
from pathlib import Path
from typing import List, Dict


class ImageProcessor:
    def __init__(self, gpt_client):
        self.gpt_client = gpt_client
        self.batch_size = 10

    async def process_directory(self, image_dir: str, output_file: str):
        """Обрабатывает все изображения в директории"""
        all_results = []
        image_paths = [str(p)
                       for p in Path(image_dir).glob("*") if p.is_file()]

        for i in range(0, len(image_paths), self.batch_size):
            batch = image_paths[i:i + self.batch_size]
            print(f"Processing batch {i//self.batch_size + 1}...")

            instruction = "Опиши кратко, что на каждом изображении. Формат: '1: [описание]', '2: [описание]', ..."
            descriptions = await self.gpt_client.analyze_images_batch(batch, instruction)
            batch_results = self._parse_descriptions(descriptions, batch)

            all_results.extend(batch_results)
            self._save_results(all_results, output_file)

        print(f"Done! Results saved to {output_file}")

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
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
