# import cv2 as cv
# import os

# def load_images(folder_path):
#     supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
#     images_dict = {}

#     for root, dirs, files in os.walk(folder_path): #root - current folder, dirs - subfolder os.walk potrzebuje 3, a folder jest nested
#         for file in files:
#             if file.lower().endswith(supported_formats):
#                 filepath = os.path.join(root, file) #łączymy ścieżki
#                 img = cv.imread(filepath) #wczytujemy obraz
#                 relative_path = os.path.relpath(filepath, folder_path)
#                 images_dict[relative_path] = img #[key] = value

#     print(f"Total images loaded: {len(images_dict)}")
#     return images_dict


# def show_image(image, name="Image"):
#     cv.namedWindow(name, cv.WINDOW_NORMAL)  # okno skalowalne - możemy zmieniać wielkość okna myszką, 
#     cv.imshow(name, image)
#     cv.waitKey(0) #czekaj bez ograniczenia czasowego [ms]
#     cv.destroyAllWindows()  #bez tego obraz od razu zniknie

# script_dir = os.path.dirname(os.path.abspath(__file__))  # folder, w którym jest plik .py
# folder_path = os.path.join(script_dir, "test_images")

# images_dict = load_images(folder_path)
# images_copy = images_dict.copy()

# choosen_key = list(images_dict.keys())[1]  #.keys() - zwraca wszystkie klucze (relative path)
# img = images_dict[choosen_key] #nazwa obrazu

# show_image(img, choosen_key) 



import cv2 as cv
import os

from intensity import compute_intensity

import numpy as np

import re


def extract_physical_values(filename):
    name = os.path.splitext(filename)[0]

    current_patterns = [
        r'(\d+(?:\.\d+)?)[ ]?(A|mA)',         # e.g. 1.50A, 1mA
        r'prad-(\d+(?:\.\d+)?)[ ]?(mA)',      # e.g. prad-1mA
    ]
    voltage_patterns = [
        r'(\d+(?:\.\d+)?)[ ]?(V)',            # e.g. 2.77V
    ]

    current = (None, None)
    voltage = (None, None)

    for pat in current_patterns:
        match = re.search(pat, name)
        if match:
            if len(match.groups()) >= 2:
                current = (match.group(1), match.group(2))
            break

    for pat in voltage_patterns:
        match = re.search(pat, name)
        if match:
            if len(match.groups()) >= 2:
                voltage = (match.group(1), match.group(2))
            break

    return current, voltage


def load_images(folder_path):
    supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    images_dict = {}

    for root, dirs, files in os.walk(folder_path): #root - current folder, dirs - subfolder os.walk potrzebuje 3, a folder jest nested
        for file in files:
            if file.lower().endswith(supported_formats):
                filepath = os.path.join(root, file) #łączymy ścieżki
                img = cv.imread(filepath) #wczytujemy obraz
                relative_path = os.path.relpath(filepath, folder_path)
                current, voltage = extract_physical_values(file)
                images_dict[relative_path] = {
                    'image': img,
                    'current': current,
                    'voltage': voltage
                }

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
img = images_dict[choosen_key]['image'] #nazwa obrazu

show_image(img, choosen_key)

print(f"Current (value and unit): {images_dict[choosen_key]['current']}")
print(f"Voltage (value and unit): {images_dict[choosen_key]['voltage']}")

img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

N, D, PR = compute_intensity(img)

print("Nominator:", N)
print("Denominator:", D)
print("PR:", PR)