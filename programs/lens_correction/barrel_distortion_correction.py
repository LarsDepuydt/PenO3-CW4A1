import numpy as np
import cv2
#import imagezmq
#from imutils.video import VideoStream
from time import sleep

# ==============================
# CONSTANTS
# ==============================

# imgL = cv2.cvtColor(cv2.imread("./programs/lens_correction/source_left_0.png "), cv2.COLOR_BGR2BGRA)
# imgR = cv2.cvtColor(cv2.imread("./programs/lens_correction/source_right_0.png"), cv2.COLOR_BGR2BGRA)
imgL = cv2.cvtColor(cv2.imread("./programs/lens_correction/source_left_1.jpg "), cv2.COLOR_BGR2BGRA)
imgR = cv2.cvtColor(cv2.imread("./programs/lens_correction/source_right_1.jpg"), cv2.COLOR_BGR2BGRA)
# imgL = cv2.cvtColor(cv2.imread("./programs/lens_correction/source_left_2.jpg "), cv2.COLOR_BGR2BGRA)
# imgR = cv2.cvtColor(cv2.imread("./programs/lens_correction/source_right_2.jpg"), cv2.COLOR_BGR2BGRA)

HEIGHT, WIDTH = imgL.shape[:2]

BLEND_FRAC = 0.

KEYPOINT_COUNT = 2000  # set number of keypoints
MAX_MATCH_Y_DISP = 20 # maximum vertical displacement of valid match in pixels
MIN_MATCH_COUNT = 5  # set minimum number of better_matches
KEYPOINT_MASK_X_BOUND = 0.4 # only search for keypoints in this fraction of the image at the stitching edge

# focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
FOCAL_LEN_L_X = 315
FOCAL_LEN_L_Y = 315
FOCAL_LEN_R_X = 315
FOCAL_LEN_R_Y = 315
s = 0 # skew parameter

K = np.array([
    [FOCAL_LEN_L_X, s, WIDTH/2], 
    [0, FOCAL_LEN_L_Y, HEIGHT/2], 
    [0, 0, 1]]                  , dtype=np.float32)  # mock intrinsics
# HAS TO BE OF TYPE FLOAT!!!!!!!!!
# [fx s x0; 0 fy y0; 0 0 1]

#D=np.array([[-0.02268523653207129], [-0.024552020182573187], [-4.141383624332057e-05], [0.011483828520533408]])
D = np.array([[-0.25], [-0.025], [0], [0.010]])

def get_cyl_wrap_assets_crop(K):
    """
    This function returns the cylindrical warp for a given image and intrinsics matrix K
    SOURCE: ???????
    """
    # pixel coordinates
    y_i, x_i = np.indices((HEIGHT, WIDTH))
    X = np.stack([x_i, y_i, np.ones_like(x_i)], axis=-1).reshape(HEIGHT * WIDTH, 3)  # to homog
    Kinv = np.linalg.inv(K)
    X = Kinv.dot(X.T).T  # normalized coords
    # calculate cylindrical coords (sin\theta, h, cos\theta)
    A = np.stack([np.sin(X[:, 0]), X[:, 1], np.cos(X[:, 0])], axis=-1).reshape(WIDTH * HEIGHT, 3)
    #boven onder: A = np.stack([X[:, 0], np.sin(X[:, 1]), np.cos(X[:, 1])], axis=-1).reshape(WIDTH * HEIGHT, 3)
    B = K.dot(A.T).T  # project back to image-pixels plane
    # back from homog coords
    B = B[:, :-1] / B[:, [-1]]
    # make sure warp coords only within image bounds
    B[(B[:, 0] < 0) | (B[:, 0] >= WIDTH) | (B[:, 1] < 0) | (B[:, 1] >= HEIGHT)] = -1
    x_L, x_R = [], []

    B = B.reshape(HEIGHT, WIDTH, -1)
    for y, r in enumerate(B):
        foundleft = False
        for x, p in enumerate(r):
            if not(foundleft) and sum(p) != -2:
                x_L.append(x)
                foundleft = True
            elif x > WIDTH/2 and sum(p) == -2:
                x_R.append(x)
                break
    x_L, x_R = min(x_L), max(x_R)
    B = B[:, x_L:x_R]
    return x_L, x_R, B[:, :, 0].astype(np.float32), B[:, :, 1].astype(np.float32)

def warp_image(img, map1, map2):
    return cv2.remap(img, map1, map2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT)

def get_x_combine_assets(xt, imgL, imgR, log=False):
    '''
    SOURCE FOR IMAGE BLENDING CODE: ??????
    '''
    height, imgL_cropped_width = imgL.shape[:2]
    height, imgR_cropped_width = imgR.shape[:2]

    combined_width = imgL_cropped_width + imgR_cropped_width - xt
    imgL_cropped_no_overlap_width = imgL_cropped_width - xt

    imgL_cropped_noblend_width = imgL_cropped_width - int(np.ceil((1 + BLEND_FRAC)/2 * xt))
    imgR_cropped_noblend_width = imgR_cropped_width - int(np.ceil((1 + BLEND_FRAC)/2 * xt))
    pre_imgR_width = imgL_cropped_noblend_width
    post_imgL_width = imgR_cropped_noblend_width
    print(imgL_cropped_no_overlap_width, imgL_cropped_noblend_width, imgR_cropped_noblend_width)
    # linear blend masks
    maskL = np.repeat(np.tile(np.linspace(1, 0, int(np.ceil(xt * BLEND_FRAC))), (height, 1))[:, :, np.newaxis], 4, axis=2)
    maskR = np.repeat(np.tile(np.linspace(0, 1, int(np.ceil(xt * BLEND_FRAC))), (height, 1))[:, :, np.newaxis], 4, axis=2)

    # constant no blend masks
    mask_imgL_cropped_noblend = np.repeat(
        np.tile(np.full(imgL_cropped_noblend_width, 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_imgR_cropped_noblend = np.repeat(
        np.tile(np.full(imgR_cropped_noblend_width, 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_post_imgL = np.repeat(np.tile(np.full((post_imgL_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_pre_imgR = np.repeat(np.tile(np.full((pre_imgR_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)

    # full-sized masks
    mask_realL = np.concatenate((mask_imgL_cropped_noblend, maskL, mask_post_imgL), axis=1)
    mask_realR = np.concatenate((mask_pre_imgR, maskR, mask_imgR_cropped_noblend), axis=1)

    TL= np.float32([[1, 0, 0], [0, 1, 0]])
    TR = np.float32([[1, 0, imgL_cropped_no_overlap_width], [0, 1, 0]])

    if log:
        cv2.imshow('mask_realL', mask_realL)
        cv2.imshow('mask_realR', mask_realR)
        print('combined width:', combined_width)
        print('height', height)
        print('TL', TL)
        print('TR', TR)
        print('xt', x_t)
        cv2.waitKey(0)

    return TL, TR, combined_width, mask_realL, mask_realR

def undistort(img, balance=1.0, dim2=None, dim3=None):
    dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort
    #assert dim1[0]/dim1[1] == WIDTH/HEIGHT, "Image to undistort needs to have same aspect ratio as the ones used in calibration"
    if not dim2:
        dim2 = dim1
    if not dim3:
        dim3 = dim1
    scaled_K = K * dim1[0] / WIDTH  # The values of K is to scale with image dimension.
    scaled_K[2][2] = 1.0  # Except that K[2][2] is always 1.0
    # This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
    new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, dim2, np.eye(3), balance=balance)
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), new_K, dim3, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return undistorted_img

def combine(log=False):
    imgL_translation = cv2.warpAffine(imgL, TL, (combined_width, HEIGHT))
    imgR_translation = cv2.warpAffine(imgR, TR, (combined_width, HEIGHT))
    final = np.uint8(imgL_translation * mask_realL + imgR_translation * mask_realR)
  
    #cv2.namedWindow("output", cv2.WINDOW_KEEPRATIO)
    if log:
        cv2.imshow('output', final)
        cv2.imshow('imgL_translation', imgL_translation)
        cv2.imshow('imgR_translation', imgR_translation)
        cv2.imshow('imgR', imgR)
        cv2.waitKey(0)
    return final 

imgR = undistort(imgR)
imgL = undistort(imgL)

x_t = 156
TL, TR, combined_width, mask_realL, mask_realR = get_x_combine_assets(x_t, imgL, imgR, log=False)

cv2.imshow("COMBINE NO CYLINDRICAL PROJ", combine(log=False))
cv2.waitKey(0)

x_L, x_R, MAP1, MAP2 = get_cyl_wrap_assets_crop(K)
imgL = warp_image(imgL, MAP1, MAP2)
imgR = warp_image(imgR, MAP1, MAP2)

x_t = 140
TL, TR, combined_width, mask_realL, mask_realR = get_x_combine_assets(x_t, imgL, imgR, log=False)

cv2.imshow("COMBINE WITH CYLINDRICAL PROJ", combine(log=False))
cv2.waitKey(0)

