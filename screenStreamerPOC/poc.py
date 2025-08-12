# Python program to take
# screenshots
  
  
import numpy as np
import cv2
import pyautogui
import io
   
  
# take screenshot using pyautogui
image = pyautogui.screenshot()
   
# since the pyautogui takes as a 
# PIL(pillow) and in RGB we need to 
# convert it to numpy array and BGR 
# so we can write it to the disk
# image = cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
img_bytes_arr=io.BytesIO()
image.save(img_bytes_arr, format='png', subsampling=0, quality=100)
img_byte_arr = img_bytes_arr.getvalue()
print(img_byte_arr)
cv2.imwrite("image1.png", image)