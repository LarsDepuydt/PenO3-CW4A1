import numpy as np
import cv2
import imagezmq
from imutils.video import VideoStream
from time import sleep
import copy

# ==============================
# CONSTANTS
# ==============================

CAMERAMODE = 1 # 1 = imutils.VideoStream, 2 = cv2.VideoCapture
CALIBRATION_RESOLUTION = WIDTH, HEIGHT = (640, 480)
STREAM_RESOLUTION      = (640, 480)
RB_IP_MAIN =    'tcp://169.254.165.116:5555'
RB_IP_HELPER =  'tcp://169.254.222.67:5555'
#PC_IP =         'tcp://192.168.137.1:5555'
#PC_IP = 'tcp://169.254.62.171:5555'
PC_IP = 'tcp://169.254.236.78:5555'
PREVIOUS_CALIBRATION_DATA_PATH = "calibration_data.txt"

#INIT_HELPER_CMD = "sh sshconn_and_execute_cmd.sh 'cd Desktop/PenO3-CW4A1/programs/MAIN_code/non_multi_threaded;python3 ./helper_v3.py'"
#from os import system
#system(INIT_HELPER_CMD)       # init helper pi

KEYPOINT_COUNT = 2000  # set number of keypoints
MAX_MATCH_Y_DISP = 20 # maximum vertical displacement of valid match in pixels
MIN_MATCH_COUNT = 5  # set minimum number of better_matches
KEYPOINT_MASK_X_BOUND = 0.4 # only search for keypoints in this fraction of pixel towards the bound

# focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
FOCAL_LEN_L_X = 310
FOCAL_LEN_L_Y = 310
FOCAL_LEN_R_X = 310
FOCAL_LEN_R_Y = 310
s = 0 # skew parameter

KL = np.array([[FOCAL_LEN_L_X, s, WIDTH/2], [0, FOCAL_LEN_L_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
KR = np.array([[FOCAL_LEN_R_X, s, WIDTH/2], [0, FOCAL_LEN_R_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]

if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=CALIBRATION_RESOLUTION).start()
elif CAMERAMODE ==2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, CALIBRATION_RESOLUTION[0])
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIBRATION_RESOLUTION[1])
IMAGE_HUB = imagezmq.ImageHub()

sleep(2)  # allow camera sensor to warm up and wait to make sure helper is running
SENDER = imagezmq.ImageSender(connect_to=RB_IP_HELPER)


# ==============================
# INITIALISATION
# ==============================

SENDER.send_image(RB_IP_MAIN, np.array(["ready"]))
print("Ready message was received by helper")

imgR = cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA)
imgL = IMAGE_HUB.recv_image()[1]
IMAGE_HUB.send_reply(b'OK')


#imgL = cv2.cvtColor(cv2.imread("./programs/cylindrical_projection/sterio_vision/images/left/left1.png"), cv2.COLOR_BGR2BGRA)
#imgR = cv2.cvtColor(cv2.imread("./programs/cylindrical_projection/sterio_vision/images/right/right1.png"), cv2.COLOR_BGR2BGRA)

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

def get_x_combine_assets_transparent_borders_precrop(xt, imgL, imgR, log=False):
    '''
    SOURCE FOR IMAGE BLENDING CODE: ??????
    '''
    height, imgL_cropped_width = imgL.shape[:2]
    height, imgR_cropped_width = imgR.shape[:2]

    combined_width = imgL_cropped_width + imgR_cropped_width - xt
    imgL_cropped_noblend_width = imgL_cropped_width - xt
    imgR_cropped_noblend_width = imgR_cropped_width - xt
    post_imgL_width = imgR_cropped_noblend_width
    pre_imgR_width = imgL_cropped_noblend_width

    ##########################################################################################

    # linear blend masks
    maskL = np.repeat(np.tile(np.linspace(1, 0, xt), (height, 1))[:, :, np.newaxis], 4, axis=2)
    maskR = np.repeat(np.tile(np.linspace(0, 1, xt), (height, 1))[:, :, np.newaxis], 4, axis=2)

    # mask of image
    imgL_mask = copy.deepcopy(imgL)
    imgR_mask = copy.deepcopy(imgR)
    imgL_mask[np.where((imgL_mask>[0,0,0,0]).all(axis=2))] = [255,255,255,1]
    imgR_mask[np.where((imgR_mask>[0,0,0,0]).all(axis=2))] = [255,255,255,1]

    #full white
    full_whiteL = np.repeat(np.tile(np.full((imgL_cropped_noblend_width), 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    full_whiteR = np.repeat(np.tile(np.full((imgR_cropped_noblend_width), 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)

    # linespace with white
    mask_realL = np.concatenate((maskR, full_whiteR), axis=1)
    mask_realR = np.concatenate((full_whiteL, maskL), axis=1)
    
    mask_realL_rounded = np.uint8(imgL_mask * mask_realL)
    mask_realR_rounded = np.uint8(imgR_mask * mask_realR)
    

    # white before mask
    mask_realL_rounded_white = np.uint8(np.concatenate((full_whiteL, mask_realL_rounded, ), axis=1))
    mask_realR_rounded_white = np.uint8(np.concatenate((mask_realR_rounded, full_whiteR), axis=1))


    # make orinigal img mask longer
    mask_postL = np.repeat(np.tile(np.full((post_imgL_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_preR = np.repeat(np.tile(np.full((pre_imgR_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)

    imgL_full = np.uint8(np.concatenate((imgL_mask, mask_postL), axis=1))
    imgR_full = np.uint8(np.concatenate((mask_preR, imgR_mask), axis=1))

    # left image mask
    output_maskL = np.uint8(imgL_full * mask_realL_rounded_white)
    output_maskL[np.where((output_maskL==[0,0,0,0]).all(axis=2))] = [255,255,255,1]

    vector1 = np.repeat(255, output_maskL.size)
    output_maskL = output_maskL / vector1.reshape(output_maskL.shape)


    # right image mask
    output_maskR = np.uint8(imgR_full * mask_realR_rounded_white)
    output_maskR[np.where((output_maskR==[0,0,0,0]).all(axis=2))] = [255,255,255,1]

    vector2 = np.repeat(255, output_maskR.size)
    output_maskR = output_maskR / vector2.reshape(output_maskR.shape)
    
    ##########################################################################################

    TL= np.float32([[1, 0, 0], [0, 1, 0]])
    TR = np.float32([[1, 0, imgL_cropped_noblend_width], [0, 1, 0]])

    if log:
        cv2.imshow('output_maskL', output_maskL)
        cv2.imshow('output_maskR', output_maskR)
        print('combined width:', combined_width)
        print('height', height)
        print('TL', TL)
        print('TR', TR)
        print('xt', x_t)
        cv2.waitKey(0)

    return TL, TR, combined_width, output_maskL, output_maskR

def combine():
    imgL_translation = cv2.warpAffine(imgL, TL, (combined_width, HEIGHT))
    imgR_translation = cv2.warpAffine(imgR, TR, (combined_width, HEIGHT))
    final = np.uint8(imgL_translation * mask_realL + imgR_translation * mask_realR)
    
    #cv2.namedWindow("output", cv2.WINDOW_KEEPRATIO)
    cv2.imshow('output', final)
    return final
    cv2.imshow('imgL_translation', imgL_translation)
    cv2.imshow('imgR_translation', imgR_translation)
    cv2.imshow('imgR', imgR)
    cv2.waitKey(0)
    

xL_L, xL_R, MAPL1, MAPL2 = get_cyl_wrap_assets_crop(KL)
xR_L, xR_R, MAPR1, MAPR2 = get_cyl_wrap_assets_crop(KR)

SENDER.send_image(RB_IP_MAIN, np.array([MAPL1, MAPL2]))
print('Sent MAPL1 and MAPL2')

#x_t, y_t = get_translation_parameters(imgL, imgR, log=False)
x_t = 100
'''
####################################################################################
dit faalt als het 2x wordt uitgevoerd !!!!!!!!!!!!!!!! (soms)
####################################################################################
'''
imgR = warp_image(imgR, MAPR1, MAPR2)
imgL = warp_image(imgL, MAPL1, MAPL2)


TL, TR, combined_width, mask_realL, mask_realR = get_x_combine_assets_transparent_borders_precrop(x_t, imgL, imgR, log=False)

cv2.imwrite("output.png", combine())


SENDER = imagezmq.ImageSender(connect_to=PC_IP)
while True:
    imgR = cv2.remap(cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA), MAPL1, MAPL2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT)
    imgL = IMAGE_HUB.recv_image()[1]
    SENDER.send_image(RB_IP_MAIN, np.uint8(cv2.warpAffine(imgL, TL, (combined_width, HEIGHT)) * mask_realL + cv2.warpAffine(imgR, TR, (combined_width, HEIGHT)) * mask_realR))
    IMAGE_HUB.send_reply(b'OK')

'''
TO DO:
[X] Remove linear-alpha blending artefacts
[X] Crop Final image
[X] Optimization
[X] Lock camera settings (ISO, shutterspeed, whitebalance, etc.)

TO CONSIDER:
[X] Add vertical displacement correction
[X] Add rotational correction
[X] Add perspective correction

'''
