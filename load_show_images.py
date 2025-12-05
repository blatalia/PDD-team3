import cv2 as cv
import os

from intensity import compute_intensity

import numpy as np

import re


def extract_physical_values(filename):
    name = os.path.splitext(filename)[0]

    current_patterns = [
        r'(\d+(?:\.\d+)?)[ ]?A',         # e.g. 1.50A
        r'prad-(\d+(?:\.\d+)?)[ ]?mA',   # e.g. prad-1mA
        r'(\d+(?:\.\d+)?)[ ]?mA',        # e.g. 1mA
    ]

    voltage_patterns = [
        r'(\d+(?:\.\d+)?)[ ]?V',         # e.g. 2.77V
    ]

    current = None
    voltage = None

    for pat in current_patterns:
        match = re.search(pat, name)
        if match:
            current = match.group(1)
            break

    for pat in voltage_patterns:
        match = re.search(pat, name)
        if match:
            voltage = match.group(1)
            break

    return np.array([current, voltage])

def load_images(folder_path):
    supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    images_dict = {}

    for root, dirs, files in os.walk(folder_path): #root - current folder, dirs - subfolder os.walk potrzebuje 3, a folder jest nested
        for file in files:
            if file.lower().endswith(supported_formats):
                filepath = os.path.join(root, file) #łączymy ścieżki
                img = cv.imread(filepath) #wczytujemy obraz
                relative_path = os.path.relpath(filepath, folder_path)
                current_voltages = extract_physical_values(file)
                images_dict[relative_path] = {
                    'image': img,
                    'current_voltage': current_voltages
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
print("Current and Voltage:", images_dict[choosen_key]['current_voltage'])

img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

N, D, PR = compute_intensity(img)

print("Nominator:", N)
print("Denominator:", D)
print("PR:", PR)
