from PIL import Image
import numpy as np

def compute_intensity_metrics_pil(image):
    grey_scale = image.convert("L")
    array_grey = np.array(grey_scale).astype(float)

    sum_I = array_grey.sum()
    sum_I_sq = (array_grey ** 2).sum()

    numerator = sum_I ** 2
    denominator = sum_I_sq

    PR = numerator / denominator if denominator != 0 else float('inf')

    return numerator, denominator, PR

img = Image.open("C:/Users/48609/Downloads/Dallas_1_x56_y32_T15C_800mA.JPG")

N, D, PR = compute_intensity_metrics_pil(img)

print("Nominator:", N)
print("Denominator:", D)
print("PR:", PR)