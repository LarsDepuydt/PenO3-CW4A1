import cv2
import numpy as np

WEG = 65
OVERLAP = 140

# Some input images
img1 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/left0_cyl.png')
img2 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/right0_cyl.png')

"""
img1 = cv2.resize(img1, (400, 300))
img2 = cv2.resize(img2, (400, 300))

img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2BGRA)
img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2BGRA)
"""

height, width = img1.shape[:2]
small_image_width = width - 2*WEG
total_width = 2*small_image_width - OVERLAP
blur_width = OVERLAP
full_width = small_image_width - OVERLAP
before_after_width = small_image_width - OVERLAP

print(blur_width)

# small linear mask
mask1 = np.repeat(np.tile(np.linspace(1, 0, blur_width), (height, 1))[:, :, np.newaxis], 3, axis=2)
mask2 = np.repeat(np.tile(np.linspace(0, 1, blur_width), (height, 1))[:, :, np.newaxis], 3, axis=2)

# full show mask
mask3 = np.repeat(np.tile(np.full(full_width, 1.), (height, 1))[:, :, np.newaxis], 3, axis=2)

# before image 2 mask
mask_pre_post = np.repeat(np.tile(np.full((before_after_width), 0.), (height, 1))[:, :, np.newaxis], 3, axis=2)

# rest aanvullen
#mask_andere1 = np.repeat(np.tile(np.full(totalWidth - img1.shape[1], 0.), (img2.shape[0], 1))[:, :, np.newaxis], 4, axis=2)
#mask_andere2 = np.repeat(np.tile(np.full(totalWidth - img1.shape[1] - (width - 2*WEG - OVERLAP), 0.), (img2.shape[0], 1))[:, :, np.newaxis], 4, axis=2)

mask_real1 = np.concatenate((mask3, mask1, mask_pre_post), axis=1)
mask_real2 = np.concatenate((mask_pre_post, mask2, mask3), axis=1)


T1 = np.float32([[1, 0, -WEG], [0, 1, 0]])
T2 = np.float32([[1, 0, (width - 3*WEG - OVERLAP)], [0, 1, 0]])

img1_translation = cv2.warpAffine(img1, T1, (total_width, height))
img2_translation = cv2.warpAffine(img2, T2, (total_width, height))

# Generate output by linear blending
final1 = np.uint8(img1_translation * mask_real1)
final2 = np.uint8(img2_translation * mask_real2)

final = np.uint8(img1_translation * mask_real1 + img2_translation * mask_real2)

# Outputs
#cv2.imshow('mask_real1', mask_real1)
#cv2.imshow('mask_real2', mask_real2)
#cv2.imshow('img2_translation', img2_translation)
#cv2.imshow('img1_translation', img1_translation)
#cv2.imshow('final1', final1)
#cv2.imshow('final2', final2)
cv2.imwrite('final.png', final)
