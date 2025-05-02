from PIL import Image
import cv2
import numpy as np

def enhance_image(input_path, output_path):
    # Загрузка изображения
    image = Image.open(input_path)
    img = np.array(image)

    # Преобразуем в BGR для OpenCV
    if img.shape[2] == 4:  # RGBA
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Увеличение резкости (sharpen)
    sharpen_kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
    sharpened = cv2.filter2D(img, -1, sharpen_kernel)

    # Уменьшение шума (билатеральный фильтр)
    denoised = cv2.bilateralFilter(sharpened, d=9, sigmaColor=75, sigmaSpace=75)

    # Яркость и контраст (опционально)
    enhanced = cv2.convertScaleAbs(denoised, alpha=1.2, beta=10)

    # Преобразуем обратно в RGB
    final_img = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
    result = Image.fromarray(final_img)

    # Сохраняем результат
    result.save(output_path)
    print(f"Сохранено улучшенное изображение: {output_path}")

# Пример использования
enhance_image("70.jpg", "output.jpg")
