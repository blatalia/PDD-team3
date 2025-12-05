from PIL import Image
import numpy as np

def compute_intensity(array):
    """
    Compute intensity metrics from a numpy array.
    
    Parameters:
    array: numpy array (grayscale image data)
    
    Returns:
    numerator, denominator, PR
    """
    array_grey = np.asarray(array).astype(float)

    sum_I = array_grey.sum()
    sum_I_sq = (array_grey ** 2).sum()

    numerator = sum_I ** 2
    denominator = sum_I_sq

    PR = numerator / denominator if denominator != 0 else float('inf')

    return numerator, denominator, PR

img = Image.open("Images/Laser photos/Far field/Dallas_1_x56_y32_T15C_800mA.JPG")
grey_scale = img.convert("L")
array_grey = np.array(grey_scale)
# N, D, PR = compute_intensity(array_grey)
#
# print("Nominator:", N)
# print("Denominator:", D)
# print("PR:", PR)