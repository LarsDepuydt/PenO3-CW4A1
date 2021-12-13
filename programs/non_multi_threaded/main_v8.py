import numpy as np
import cv2
import imagezmq
from imutils.video import VideoStream
from time import sleep
from math import floor, ceil

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

BLURR_WIDTH = 1/10

KEYPOINT_COUNT = 2000  # set number of keypoints
MAX_MATCH_Y_DISP = 20 # maximum vertical displacement of valid match in pixels
MIN_MATCH_COUNT = 5  # set minimum number of better_matches
KEYPOINT_MASK_X_BOUND = 0.4 # only search for keypoints in this fraction of pixel towards the bound

# focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
FOCAL_LEN_L_X = 315
FOCAL_LEN_L_Y = 315
FOCAL_LEN_R_X = 315
FOCAL_LEN_R_Y = 315
s = 0 # skew parameter

KL = np.array([[FOCAL_LEN_L_X, s, WIDTH/2], [0, FOCAL_LEN_L_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
KR = np.array([[FOCAL_LEN_R_X, 0, WIDTH/2], [0, FOCAL_LEN_R_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]

PRECROP_ENABLED = True

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

#imgL = cv2.cvtColor(cv2.imread("./programs/cylindrical_projection/sterio_vision/images/left/left0.png"), cv2.COLOR_BGR2BGRA)
#imgR = cv2.cvtColor(cv2.imread("./programs/cylindrical_projection/sterio_vision/images/right/right0.png"), cv2.COLOR_BGR2BGRA)

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
    theta_s = X[:, 0]
    phi_s = X[:, 1]
    A = np.stack([np.cos(phi_s) * np.sin(theta_s), np.sin(phi_s), np.cos(phi_s) * np.cos(theta_s)], axis=-1).reshape(
        WIDTH * HEIGHT, 3)
    #B = K.dot(A.T).T
    ro = np.arctan2(np.sqrt(A[:,0]**2 + A[:,1]**2),A[:,2])
    theta = np.arctan2(A[:,1],A[:,0])
    B = np.stack([ro*np.cos(theta), ro*np.sin(theta), np.ones_like(A[:,0])], axis=-1).reshape(WIDTH * HEIGHT, 3)
    B = K.dot(B.T).T  # project back to image-pixels plane
    B = B[:, :-1] / B[:, [-1]]
    # make sure warp coords only within image bounds
    B[(B[:, 0] < 0) | (B[:, 0] >= WIDTH) | (B[:, 1] < 0) | (B[:, 1] >= HEIGHT)] = -1
    B = B.reshape(HEIGHT, WIDTH, -1)
    x_L, x_R = [], []
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

def get_translation_parameters(imgL, imgR, log=False):
    '''
    Transparency masking code source:
    https://stackoverflow.com/questions/45810417/opencv-python-how-to-use-mask-parameter-in-orb-feature-detector
    '''
    h, w = imgL.shape[:2]
    keypoint_mask_width = int(w * KEYPOINT_MASK_X_BOUND)
    no_keypoint_mask_width = w - keypoint_mask_width

    mask_cond_L = imgL[:,:,3] == 255 # create mask for non-transparant pixels
    mask_L = np.array(np.where(mask_cond_L, 255, 0), dtype=np.uint8) # must use uint8 for ORB to work
    mask_L[:,:no_keypoint_mask_width] = 0 # create mask for pixels outside are of interest next to image border

    mask_cond_R = imgR[:,:,3] == 255
    mask_R = np.array(np.where(mask_cond_R, 255, 0), dtype=np.uint8)
    mask_R[:, keypoint_mask_width:] = 0

    orb = cv2.ORB_create(nfeatures=KEYPOINT_COUNT)
    keyptsL, descriptorsL = orb.detectAndCompute(imgL, mask=mask_L)
    keyptsR, descriptorsR = orb.detectAndCompute(imgR, mask=mask_R)

    bf = cv2.BFMatcher_create(cv2.NORM_HAMMING)
    matches = bf.knnMatch(descriptorsL, descriptorsR, k=2)

    # Finding the best matches
    good_matches = []
    for m, n in matches:
        if m.distance < 0.6 * n.distance:
            good_matches.append(m)

    #Filter out matches with too much vertical displacement
    better_matches, filtered_because_of_vert_disp = [], 0
    for m in good_matches:
        if abs(keyptsL[m.queryIdx].pt[1] - keyptsR[m.trainIdx].pt[1]) <= MAX_MATCH_Y_DISP:
            better_matches.append(m)
        else:
            filtered_because_of_vert_disp += 1

    print("keypoints: ", len(keyptsL), "| matches: ", len(matches), "| good matches:", len(good_matches), "| better matches:", len(better_matches))
    assert len(better_matches) >= MIN_MATCH_COUNT

    x_t, avg_y_disp = 0, 0
    for m in better_matches:
        xL, yL= keyptsL[m.queryIdx].pt
        xR, yR= keyptsR[m.trainIdx].pt
        x_t += abs(w-xL + xR)
        avg_y_disp += abs(yR-yL)
    x_t = int(x_t / len(better_matches))
    avg_y_disp = int(avg_y_disp / len(better_matches))

    if log:
        cv2.imshow('left mask', mask_L)
        cv2.imshow('right mask', mask_R)
        cv2.imshow('left img keypts', cv2.drawKeypoints(imgL, keyptsL, None, color=(255,0,0)))
        cv2.imshow('right img keypts', cv2.drawKeypoints(imgR, keyptsR, None, color=(255,0,0)))
        cv2.imshow("Good matches", cv2.drawMatches(imgL, keyptsL, imgR, keyptsR, good_matches, None, matchColor=(0,255,0)))
        cv2.imshow("Better Matches", cv2.drawMatches(imgL, keyptsL, imgR, keyptsR, better_matches, None, matchColor=(255, 0, 255)))
        cv2.waitKey(0)
    
    return x_t, avg_y_disp

def get_x_combine_assets_transparent_borders_no_precrop(x_t, log=False):
    '''
    SOURCE FOR IMAGE BLENDING CODE: ??????
    '''
    for pi, pixel in enumerate(np.flip(imgL[240])):
        if pixel[3] != 0:
            xLn = pi # distance overlap point to black border
            break
    for pi, pixel in enumerate(imgR[240]):
        if pixel[3] != 0:
            xRn = pi
            break

    xt = x_t - xLn - xRn
    height, width = imgL.shape[:2]
    imgL_cropped_width = width - 2*xLn
    imgR_cropped_width = width - 2*xRn

    combined_width = imgL_cropped_width + imgR_cropped_width - xt
    imgL_cropped_noblend_width = imgL_cropped_width - xt
    imgR_cropped_noblend_width = imgR_cropped_width - xt
    pre_imgR_width = imgL_cropped_noblend_width
    post_imgL_width = imgR_cropped_noblend_width

    print(xt)

    # small linear masks
    maskL = np.repeat(np.tile(np.linspace(1, 0, xt), (height, 1))[:, :, np.newaxis], 4, axis=2)
    maskR = np.repeat(np.tile(np.linspace(0, 1, xt), (height, 1))[:, :, np.newaxis], 4, axis=2)

    # full show mask
    mask_imgL_cropped_noblend = np.repeat(np.tile(np.full(imgL_cropped_noblend_width, 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_imgR_cropped_noblend = np.repeat(np.tile(np.full(imgR_cropped_noblend_width, 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_post_imgL = np.repeat(np.tile(np.full((post_imgL_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)
    mask_pre_imgR = np.repeat(np.tile(np.full((pre_imgR_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)

    mask_realL = np.concatenate((mask_imgL_cropped_noblend, maskL, mask_post_imgL), axis=1)
    mask_realR = np.concatenate((mask_pre_imgR, maskR, mask_imgR_cropped_noblend), axis=1)

    TL= np.float32([[1, 0, -xLn], [0, 1, 0]])
    TR = np.float32([[1, 0, (width - 2*xLn -xRn - xt)], [0, 1, 0]])

    if log:
        cv2.imshow('mask_realL', mask_realL)
        cv2.imshow('mask_realR', mask_realR)
        print('combined width:', combined_width)
        print('height', height)
        print('TL', TL)
        print('TR', TR)
        cv2.waitKey(0)

    return TL, TR, combined_width, mask_realL, mask_realR

def get_x_combine_assets_transparent_borders_precrop(xt, log=False):
    '''
    SOURCE FOR IMAGE BLENDING CODE: ??????
    '''
    height, imgL_cropped_width = imgL.shape[:2]
    height, imgR_cropped_width = imgR.shape[:2]

    imgL_cropped_no_overlap_width = imgL_cropped_width - xt

    imgL_cropped_noblend_width = imgL_cropped_width - ceil((1 + BLURR_WIDTH)/2 * xt)
    imgR_cropped_noblend_width = imgR_cropped_width - ceil((1 + BLURR_WIDTH)/2 * xt)
    pre_imgR_width = imgL_cropped_noblend_width
    post_imgL_width = imgR_cropped_noblend_width
    print(imgL_cropped_no_overlap_width, imgL_cropped_noblend_width, imgR_cropped_noblend_width)
    # linear blend masks
    maskL = np.repeat(np.tile(np.linspace(1, 0, ceil(xt * BLURR_WIDTH)), (height, 1))[:, :, np.newaxis], 4, axis=2)
    maskR = np.repeat(np.tile(np.linspace(0, 1, ceil(xt * BLURR_WIDTH)), (height, 1))[:, :, np.newaxis], 4, axis=2)

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

    height_real, combined_width = mask_realL.shape[:2]

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

def combine(log = False):
    imgL_translation = cv2.warpAffine(imgL, TL, (combined_width, HEIGHT))
    imgR_translation = cv2.warpAffine(imgR, TR, (combined_width, HEIGHT))
    
    final = np.uint8(imgL_translation * mask_realL + imgR_translation * mask_realR)
    if log:
        pass
    return final


xR_L, xR_R, MAPR1, MAPR2 = get_cyl_wrap_assets_crop(KR)
xL_L, xL_R, MAPL1, MAPL2 = get_cyl_wrap_assets_crop(KL)

SENDER.send_image(RB_IP_MAIN, np.array([MAPL1, MAPL2]))
print('Sent MAPL1 and MAPL2')

#x_t, y_t = get_translation_parameters(imgL, imgR, log=False)
x_t = 472
imgL = warp_image(imgL, MAPL1, MAPL2)
imgR = warp_image(imgR, MAPR1, MAPR2)

TL, TR, combined_width, mask_realL, mask_realR = get_x_combine_assets_transparent_borders_precrop(x_t, log=False)

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
