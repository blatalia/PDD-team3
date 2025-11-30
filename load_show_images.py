import cv2 as cv
import os

def load_images(folder_path):
    supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    images_dict = {}

    for root, dirs, files in os.walk(folder_path): #root - current folder, dirs - subfolder os.walk potrzebuje 3, a folder jest nested
        for file in files:
            if file.lower().endswith(supported_formats):
                filepath = os.path.join(root, file) #łączymy ścieżki
                img = cv.imread(filepath) #wczytujemy obraz
                relative_path = os.path.relpath(filepath, folder_path)
                images_dict[relative_path] = img #[key] = value

    print(f"Total images loaded: {len(images_dict)}")
    return images_dict


def show_image(image, name="Image"):
    cv.namedWindow(name, cv.WINDOW_NORMAL)  # okno skalowalne - możemy zmieniać wielkość okna myszką, 
    cv.imshow(name, image)
    cv.waitKey(0) #czekaj bez ograniczenia czasowego [ms]
    cv.destroyAllWindows()  #bez tego obraz od razu zniknie

script_dir = os.path.dirname(os.path.abspath(__file__))  # folder, w którym jest plik .py
folder_path = os.path.join(script_dir, "Laser photos")

images_dict = load_images(folder_path)
images_copy = images_dict.copy()

choosen_key = list(images_dict.keys())[1]  #.keys() - zwraca wszystkie klucze (relative path)
img = images_dict[choosen_key] #nazwa obrazu

show_image(img, choosen_key) 