import numpy as np
import cv2

WEG = 65
OVERLAP = 140
FOCAL_LENGTH = 320

# Some input images
img1 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/left0_cyl.png')
img2 = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/cylindrical_projection_images/right0_cyl.png')

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

mask_real1 = np.concatenate((mask3, mask1), axis=1)
mask_real2 = np.concatenate((mask2, mask3), axis=1)


def cylindricalWarp(img, K):
    """This function returns the cylindrical warp for a given image and intrinsics matrix K"""
    h_, w_ = img.shape[:2]
    # pixel coordinates
    y_i, x_i = np.indices((h_, w_))
    X = np.stack([x_i, y_i, np.ones_like(x_i)], axis=-1).reshape(h_ * w_, 3)  # to homog
    Kinv = np.linalg.inv(K)
    X = Kinv.dot(X.T).T  # normalized coords
    # calculate cylindrical coords (sin\theta, h, cos\theta)
    A = np.stack([np.sin(X[:, 0]), X[:, 1], np.cos(X[:, 0])], axis=-1).reshape(w_ * h_, 3)
    #boven onder: A = np.stack([X[:, 0], np.sin(X[:, 1]), np.cos(X[:, 1])], axis=-1).reshape(w_ * h_, 3)
    B = K.dot(A.T).T  # project back to image-pixels plane
    # back from homog coords
    B = B[:, :-1] / B[:, [-1]]
    # make sure warp coords only within image bounds
    B[(B[:, 0] < 0) | (B[:, 0] >= w_) | (B[:, 1] < 0) | (B[:, 1] >= h_)] = -1
    B = B.reshape(h_, w_, -1)

    #img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)  # for transparent borders...
    # warp the image according to cylindrical coords
    return cv2.remap(img, B[:, :, 0].astype(np.float32), B[:, :, 1].astype(np.float32), cv2.INTER_AREA,
                     borderMode=cv2.BORDER_TRANSPARENT)


h = height
w = width
K = np.array([[FOCAL_LENGTH, 0, w/2], [0, FOCAL_LENGTH, h/2], [0, 0, 1]])  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]
img_cyl = cylindricalWarp(mask_real1, K)

cv2.imshow('mask_real1.png', mask_real1)
cv2.imshow('img_cyl.png', img_cyl)

cv2.waitKey(0)
cv2.destroyAllWindows()