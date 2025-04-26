# import yt_dlp

# url = 'https://www.youtube.com/watch?v=2AYuijbofiM&t=453s'

# ydl_opts = {
#     'format': 'best',  # Выбрать лучшее качество
#     'outtmpl': '%(title)s.%(ext)s',  # Сохранять файл с названием видео
# }

# with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     ydl.download([url])

from yt_dlp import YoutubeDL

def search_youtube(query, max_results=5):
    options = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': True,
        'noplaylist': True
    }
    
    with YoutubeDL(options) as ydl:
        search_query = f"ytsearch{max_results * 2}:{query}"  # ищем чуть больше, чтобы потом отфильтровать
        info = ydl.extract_info(search_query, download=False)
        videos = info.get('entries', [])
        
        links = []
        for video in videos:
            # Проверяем, что это не шорт
            if 'shorts' not in video.get('url', '') and video.get('duration', 0) > 60:
                links.append(f"https://www.youtube.com/watch?v={video['id']}")
            if len(links) >= max_results:
                break
        
        return links

# Пример использования
if __name__ == "__main__":
    query = input("Введите поисковый запрос: ")
    videos = search_youtube(query)
    for video in videos:
        print(video)

