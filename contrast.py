import numpy as np
from PIL import Image

def compute_contrast(array):
    """
    Compute contrast metrics from a numpy array.
    
    Parameters:
    array: numpy array (grayscale image data)
    
    Returns:
    rms_contrast, histogram_spread_contrast
    """
    array_grey = np.asarray(array).astype(float)

    # RMS
    mean_intensity = np.mean(array_grey)
    rms_contrast = np.sqrt(np.mean((array_grey - mean_intensity) ** 2))
    
    # Histogram spread
    q1 = np.percentile(array_grey, 25)  
    q3 = np.percentile(array_grey, 75)  
    pmax = np.max(array_grey)
    pmin = np.min(array_grey)
    
    histogram_spread_contrast = (q3 - q1) / (pmax - pmin) if (pmax - pmin) != 0 else 0
    
    return rms_contrast, histogram_spread_contrast

img = Image.open("Images/Laser photos/Far field/Dallas_1_x56_y32_T15C_800mA.JPG")
grey_scale = img.convert("L")
array_grey = np.array(grey_scale)

rms, histogram_spread = compute_contrast(array_grey)

print("RMS Contrast:", rms)
print("Histogram Spread Contrast:", histogram_spread)
