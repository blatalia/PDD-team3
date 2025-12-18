import cv2 as cv
import os
import re
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def compute_intensity(array):
    array_grey = np.asarray(array).astype(float)
    sum_I = array_grey.sum()
    sum_I_sq = (array_grey ** 2).sum()
    numerator = sum_I ** 2
    denominator = sum_I_sq
    PR = numerator / denominator if denominator != 0 else float('inf')
    return numerator, denominator, PR

def save_data_to_txt(filename, data_dict):
    output_path = os.path.join(RESULTS_DIR, filename)
    with open(output_path, 'w') as f:
        f.write("--- Image Analysis Results ---\n")
        f.write(f"Source File: {data_dict.get('source_file', 'N/A')}\n")
        f.write(f"Current: {data_dict.get('current_val', 'N/A')} {data_dict.get('current_unit', '')}\n")
        f.write("-" * 30 + "\n")
        f.write(f"Nominator ((Sum I)^2): {data_dict['Nominator']:.4f}\n")
        f.write(f"Denominator (Sum I^2): {data_dict['Denominator']:.4f}\n")
        f.write(f"Purity Ratio (PR): {data_dict['PR']:.4f}\n")

def save_plot_as_image(fig, filename):
    output_path = os.path.join(RESULTS_DIR, filename)
    fig.savefig(output_path)
    plt.close(fig)

def generate_and_save_pr_plot(all_results):
    current_values = [item['current_val'] for item in all_results if item['current_val'] is not None]
    pr_values = [item['PR'] for item in all_results if item['current_val'] is not None]

    if not current_values:
        return

    current_unit = next((item['current_unit'] for item in all_results if item['current_unit']), 'A.U.')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(current_values, pr_values, 'o--', color='blue') 
    ax.set_title('Purity Ratio (PR) vs. Experimental Current (Task 8)')
    ax.set_xlabel(f'Current ({current_unit})')
    ax.set_ylabel('Purity Ratio (PR)')
    ax.grid(True)
    
    save_plot_as_image(fig, "Overall_PR_vs_Current_Plot.png")

def extract_physical_values(filename):
    name = os.path.splitext(filename)[0]
    current_patterns = [r'(\d+(?:\.\d+)?)[ ]?(A|mA)', r'prad-(\d+(?:\.\d+)?)[ ]?(mA)']
    voltage_patterns = [r'(\d+(?:\.\d+)?)[ ]?(V)']
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
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(supported_formats):
                filepath = os.path.join(root, file)
                img = cv.imread(filepath)
                relative_path = os.path.relpath(filepath, folder_path)
                current, voltage = extract_physical_values(file)
                
                if img is not None:
                    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                else:
                    img_gray = None

                images_dict[relative_path] = {
                    'image_gray': img_gray,
                    'current': current,
                    'voltage': voltage
                }
    return images_dict

script_dir = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(script_dir, "Laser photos")

images_dict = load_images(folder_path)

all_results_for_plot = []

for relative_path, data in images_dict.items():
    img_array = data['image_gray']
    current_data = data['current']
    base_filename = os.path.splitext(os.path.basename(relative_path))[0]

    if img_array is not None:
        try:
            N, D, PR = compute_intensity(img_array)
            
            current_val = float(current_data[0]) if current_data[0] else None
            current_unit = current_data[1] if current_data[1] else ''

            results_data = {
                'source_file': relative_path,
                'current_val': current_val,
                'current_unit': current_unit,
                'Nominator': N,
                'Denominator': D,
                'PR': PR
            }

            txt_filename = f"{base_filename}_results.txt"
            save_data_to_txt(txt_filename, results_data)
            
            all_results_for_plot.append(results_data)

        except Exception:
            pass

generate_and_save_pr_plot(all_results_for_plot)