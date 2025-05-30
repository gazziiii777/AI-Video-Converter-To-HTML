import config.config as config


class TableParser:
    @staticmethod
    async def parse_keywords_table(table_string: str) -> tuple:
        """Парсит таблицу с ключевыми словами"""
        lines = [line.strip() for line in table_string.split('\n')
                 if line.strip() and not line.strip().replace('-', '').replace('|', '').replace(' ', '').strip() == '']

        not_included = []
        h2_phrases = []
        included = []

        for line in lines[1:]:  # Пропускаем заголовок
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                if parts[1].strip() == 'Not Included':
                    not_included.append(parts[0].strip())
                elif parts[1].strip() == 'Included':
                    included.append(parts[0].strip())
                    h2_phrases.append(
                        f"{parts[0].strip()} h2: {parts[2].strip()}")

        if len(included) > 0:
            config.H2_INCLUDED = ", ".join(included)

        if len(not_included) > 0:
            return ", ".join(not_included), h2_phrases

        return None, h2_phrases

    @staticmethod
    async def parse_h3_table(table_string: str) -> tuple:
        """Парсит таблицу с H3 заголовками"""
        lines = [line.strip() for line in table_string.split('\n')
                 if line.strip() and not line.strip().replace('-', '').replace('|', '').replace(' ', '').strip() == '']

        result = []
        for line in lines[1:]:  # Пропускаем заголовок
            columns = [col.strip() for col in line.split('|') if col.strip()]
            row_dict = {
                'H3': columns[0] if len(columns) > 0 else '',
                'H2_Before': columns[1] if len(columns) > 1 else '',
                'H2_After': columns[2] if len(columns) > 2 else '',
                'Prompt': columns[3] if len(columns) > 3 else ''
            }
            result.append(row_dict)

        config.H3_DATA = result
        return result, None

    @staticmethod
    async def parse_h2_replacement_table(table_string: str) -> tuple:
        """Парсит таблицу для замены H2 заголовков"""
        lines = [line.strip() for line in table_string.split('\n')
                 if line.strip() and not line.strip().replace('-', '').replace('|', '').replace(' ', '').strip() == '']

        result = []
        for line in lines[1:]:  # Пропускаем заголовок
            columns = [col.strip() for col in line.split('|') if col.strip()]
            row_dict = {
                'keyword': columns[0].strip() if len(columns) > 0 else '',
                'old_h2': columns[1].strip() if len(columns) > 1 else '',
                'new_h2': columns[2].strip() if len(columns) > 2 else '',
            }
            result.append(row_dict)

        return result, None
