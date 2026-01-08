import numpy as np
from PIL import Image

def compute_contrast(array):
    """
    Compute contrast metrics from a numpy array.
    
    Parameters:
    array: numpy array (grayscale image data)
    
    Returns:
    rms_contrast, histogram_spread_contrast, michelson_contrast, std_mean_contrast
    """
    array_grey = np.asarray(array).astype(float)
    
    # Michelson Contrast
    I_max = array_grey.max()
    I_min = array_grey.min()
    
    if (I_max + I_min) != 0:
        michelson_contrast = (I_max - I_min) / (I_max + I_min)
    else:
        michelson_contrast = float('inf')

    # RMS Contrast
    mean_intensity = np.mean(array_grey)
    rms_contrast = np.sqrt(np.mean((array_grey - mean_intensity) ** 2))
    
    # Histogram Spread Contrast
    q1 = np.percentile(array_grey, 25)  
    q3 = np.percentile(array_grey, 75)  
    pmax = I_max
    pmin = I_min
    
    histogram_spread_contrast = (q3 - q1) / (pmax - pmin) if (pmax - pmin) != 0 else 0
    
    # Std/Mean Contrast
    mean_I = array_grey.mean()
    std_I = array_grey.std()
    
    if mean_I != 0:
        std_mean_contrast = std_I / mean_I
    else:
        std_mean_contrast = float('inf')
    
    return michelson_contrast, rms_contrast, histogram_spread_contrast, std_mean_contrast

img = Image.open("/home/maciej/studiapodobno/lasery/app-work/PDD-team3/Laser photos/Far field/Dallas_1_x56_y32_T15C_800mA.JPG")
grey_scale = img.convert("L")
array_grey = np.array(grey_scale)

rms, histogram_spread, michelson, std_mean = compute_contrast(array_grey)

print("RMS Contrast:", rms)
print("Histogram Spread Contrast:", histogram_spread)
print("Michelson Contrast:", michelson)
print("Std/Mean Contrast:", std_mean)
