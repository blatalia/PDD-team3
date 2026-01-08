import cv2 as cv
import os
import re
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt


RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def compute_intensity(array):
    array_gray = np.asarray(array).astype(float)
    sum_I = array_gray.sum()
    sum_I_sq = (array_gray ** 2).sum()
    numerator = sum_I ** 2
    denominator = sum_I_sq
    PR = numerator / denominator if denominator != 0 else float('inf')
    return numerator, denominator, PR

def compute_contrast(array):
    array_gray = np.asarray(array).astype(float)
    
    # Michelson Contrast
    I_max = array_gray.max()
    I_min = array_gray.min()
    michelson_contrast = (I_max - I_min) / (I_max + I_min) if (I_max + I_min) != 0 else float('inf')

    # RMS Contrast
    mean_intensity = np.mean(array_gray)
    rms_contrast = np.sqrt(np.mean((array_gray - mean_intensity) ** 2))
    
    # Histogram Spread Contrast
    q1 = np.percentile(array_gray, 25)  
    q3 = np.percentile(array_gray, 75)  
    histogram_spread_contrast = (q3 - q1) / (I_max - I_min) if (I_max - I_min) != 0 else 0
    
    # Std/Mean Contrast
    mean_I = array_gray.mean()
    std_I = array_gray.std()
    std_mean_contrast = std_I / mean_I if mean_I != 0 else float('inf')
    
    return michelson_contrast, rms_contrast, histogram_spread_contrast, std_mean_contrast

def extract_physical_values(filename):
    name = os.path.splitext(filename)[0]
    current_patterns = [r'(\d+(?:\.\d+)?)[ ]?(A|mA)', r'prad-(\d+(?:\.\d+)?)[ ]?(mA)']
    voltage_patterns = [r'(\d+(?:\.\d+)?)[ ]?(V)']
    current = (None, None) #wartość i jednostka
    voltage = (None, None)

    for pat in current_patterns:
        match = re.search(pat, name)
        if match and len(match.groups()) >= 2:
            current = (match.group(1), match.group(2))
            break
    for pat in voltage_patterns:
        match = re.search(pat, name)
        if match and len(match.groups()) >= 2:
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
                images_dict[relative_path] = {
                    'image': img,
                    'current': current,
                    'voltage': voltage
                }
    return images_dict

def save_all_results_to_txt(filename, all_results):
    output_path = os.path.join(RESULTS_DIR, filename)
    with open(output_path, 'w') as f:
        f.write("Image, Current, Voltage, Nominator ((Sum I)^2), Denominator (Sum I^2), PR, Michelson Contrast, RMS Contrast, Histogram Spread Contrast, Std/Mean Contrast\n")
        for data in all_results:
            current_str = f"{data['current_val']} {data['current_unit']}" if data['current_val'] is not None else "NaN"
            voltage_str =f"{data['voltage_val']} {data['voltage_unit']}" if data['voltage_val'] is not None else "NaN"
            line = f"{data['source_file']}, {current_str}, {voltage_str}, {data['Nominator']:.4f}, {data['Denominator']:.4f}, {data['PR']:.4f}, {data['Michelson']:.4f}, {data['RMS']:.4f}, {data['HistogramSpread']:.4f}, {data['StdMean']:.4f}\n"
            f.write(line)

def save_plot_as_image(fig, filename):
    output_path = os.path.join(RESULTS_DIR, filename)
    fig.savefig(output_path)
    plt.close(fig)

def generate_and_save_pr_plot(all_results): #To do ogarnięcia
    current_values = [item['current_val'] for item in all_results if item['current_val'] is not None]
    pr_values = [item['PR'] for item in all_results if item['current_val'] is not None]
    if not current_values:
        return
    current_unit = next((item['current_unit'] for item in all_results if item['current_unit']), 'A.U.')
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(current_values, pr_values, 'o--', color='blue')
    ax.set_title('Purity Ratio (PR) vs. Experimental Current (Task 8)')
    ax.set_xlabel(f'Current ({current_unit})')
    ax.set_ylabel('Purity Ratio (PR)')
    ax.grid(True)
    save_plot_as_image(fig, "Overall_PR_vs_Current_Plot.png")

script_dir = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(script_dir, "Laser photos")

images_dict = load_images(folder_path)
all_results_for_plot = []

for relative_path, data in images_dict.items():
    img_array = data['image']
    current_data = data['current']
    voltage_data = data['voltage']

    if img_array is not None:
        try:
            #grayscale
            img_gray = cv.cvtColor(img_array, cv.COLOR_BGR2GRAY)

            N, D, PR = compute_intensity(img_gray)
            michelson, rms, hist_spread, std_mean = compute_contrast(img_gray)
            
            current_val = float(current_data[0]) if current_data[0] else None
            current_unit = current_data[1] if current_data[1] else ''

            voltage_val = float(voltage_data[0]) if voltage_data[0] else None
            voltage_unit = voltage_data[1] if voltage_data[1] else ''

            results_data = {
                'source_file': relative_path,
                'current_val': current_val,
                'current_unit': current_unit,
                'voltage_val': voltage_val,
                'voltage_unit': voltage_unit,
                'Nominator': N,
                'Denominator': D,
                'PR': PR,
                'Michelson': michelson,
                'RMS': rms,
                'HistogramSpread': hist_spread,
                'StdMean': std_mean
            }

            all_results_for_plot.append(results_data)

        except Exception as e:
            print(f"Error processing {relative_path}: {e}")

save_all_results_to_txt("results.txt", all_results_for_plot)


#generate_and_save_pr_plot(all_results_for_plot)
print("koniec")
