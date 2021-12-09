import cv2
import numpy as np

WEG = 60
OVERLAP = 60
BOVEN_HEIGHT = 30

# Some input images
img1 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/left0_cyl.png')
img1_mask = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/left0_cyl.png')
img2 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/right0_cyl.png')
img2_mask = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/right0_cyl.png')

height, width = img1.shape[:2]

small_image_width = width - 2*WEG
total_width = 2*small_image_width - OVERLAP
blur_width = OVERLAP
full_width = small_image_width - OVERLAP
before_after_width = small_image_width - OVERLAP


# small linear mask
mask1 = np.repeat(np.tile(np.linspace(1, 0, blur_width), (height, 1))[:, :, np.newaxis], 3, axis=2)
mask2 = np.repeat(np.tile(np.linspace(0, 1, blur_width), (height, 1))[:, :, np.newaxis], 3, axis=2)

# full show mask
mask3 = np.repeat(np.tile(np.full(full_width, 1.), (height, 1))[:, :, np.newaxis], 3, axis=2)

# before image 2 mask
mask_pre_post = np.repeat(np.tile(np.full((before_after_width), 0.), (height, 1))[:, :, np.newaxis], 3, axis=2)


mask_real1 = np.concatenate((mask3, mask1, mask_pre_post), axis=1)
mask_real2 = np.concatenate((mask_pre_post, mask2, mask3), axis=1)





T1 = np.float32([[1, 0, - WEG + 10], [0, 1, 0]])
T2 = np.float32([[1, 0, (width - 3*WEG - OVERLAP)], [0, 1, 0]])

img1_translation = cv2.warpAffine(img1, T1, (total_width, height))
img2_translation = cv2.warpAffine(img2, T2, (total_width, height))



# mask images
img1_translation_mask = cv2.warpAffine(img1_mask, T1, (total_width, height))
img2_translation_mask = cv2.warpAffine(img2_mask, T2, (total_width, height))

img1_translation_mask[np.where((img1_translation_mask>[0,0,0]).all(axis=2))] = [255,255,255]
img2_translation_mask[np.where((img2_translation_mask>[0,0,0]).all(axis=2))] = [255,255,255]



# change image size
img1_translation_mask_small = cv2.warpAffine(img1_mask, T1, (small_image_width, height))
img2_translation_mask_small = cv2.warpAffine(img2_mask, T1, (small_image_width, height))

img1_translation_mask_small[np.where((img1_translation_mask_small>[0,0,0]).all(axis=2))] = [255,255,255]
img2_translation_mask_small[np.where((img2_translation_mask_small>[0,0,0]).all(axis=2))] = [255,255,255]




#full white
full_white = np.repeat(np.tile(np.full((small_image_width - OVERLAP), 1.), (height, 1))[:, :, np.newaxis], 3, axis=2)

# linespace with white
mask_real1_white = np.concatenate((mask2, mask3), axis=1)
mask_real2_white = np.concatenate((mask3, mask1), axis=1)

mask_real1_rounded = np.uint8(img1_translation_mask_small * mask_real1_white)
mask_real2_rounded = np.uint8(img2_translation_mask_small * mask_real2_white)

mask_real1_rounded_white = np.uint8(np.concatenate((full_white, mask_real1_rounded, ), axis=1))
mask_real2_rounded_white = np.uint8(np.concatenate((mask_real2_rounded, full_white), axis=1))

mask_real1_rounded_white[np.where((mask_real1_rounded_white==[1,1,1]).all(axis=2))] = [255,255,255]
mask_real2_rounded_white[np.where((mask_real2_rounded_white==[1,1,1]).all(axis=2))] = [255,255,255]



output_mask1 = np.uint8(img1_translation_mask * mask_real1_rounded_white)
output_mask1[np.where((output_mask1==[0,0,0]).all(axis=2))] = [255,255,255]
output_mask1[np.where((output_mask1==[1,1,1]).all(axis=2))] = [255,255,255]


vector1 = np.repeat(255, output_mask1.size)
output_mask1 = output_mask1 / vector1.reshape(output_mask1.shape)

#np.set_printoptions(threshold=np.inf)
#print(output_mask1[200:300])



output_mask2 = np.uint8(img2_translation_mask * mask_real2_rounded_white)
output_mask2[np.where((output_mask2==[0,0,0]).all(axis=2))] = [255,255,255]
output_mask2[np.where((output_mask2==[1,1,1]).all(axis=2))] = [255,255,255]

vector2 = np.repeat(255, output_mask2.size)
output_mask2 = output_mask2 / vector2.reshape(output_mask2.shape)

# Generate output by linear blending
final1 = np.uint8(img1_translation * output_mask1)
final2 = np.uint8(img2_translation * output_mask2)

final = np.uint8(final1 + final2)


# Outputs

cv2.imshow('final1', final1)
cv2.imshow('final2', final2)
cv2.imshow('final', final)
cv2.waitKey(0)

cv2.destroyAllWindows()
