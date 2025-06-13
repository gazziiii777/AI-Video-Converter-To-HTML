import json
from typing import Dict, Optional



class PromptManager:
    def __init__(self, json_file_path: str = "neuronwriter_prompts.json"):
        self.json_file_path = json_file_path
        self.data = self._load_json_data()

    def _load_json_data(self) -> Dict:
        """Загружает данные из JSON файла"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise Exception(f"Файл {self.json_file_path} не найден")
        except json.JSONDecodeError:
            raise Exception("Ошибка парсинга JSON")

    async def get_prompt_by_name(self, prompt_name: str) -> Optional[Dict]:
        return next((p for p in self.data['prompts'] if p['name'] == prompt_name), None)

    async def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict]:
        return next((p for p in self.data['prompts'] if p['number'] == prompt_id), None)