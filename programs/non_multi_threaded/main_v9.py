import numpy as np
from sys import argv
import cv2
import imagezmq
from imutils.video import VideoStream
from time import sleep
from math import floor, ceil

# ==============================
# ARGUMENT PARSER
# ==============================
USE_KEYPOINT_TRANSLATE = bool(argv[1])
RESOLUTION = WIDTH, HEIGHT = [int(x) for x in argv[2].split(",")]
BLEND_FRAC = float(argv[3])
X_t = int(argv[4])
PC_IP = argv[5]

# ==============================
# CONSTANTS
# ==============================

CAMERAMODE = 1 # 1 = imutils.VideoStream, 2 = cv2.VideoCapture
RB_IP_MAIN =    'tcp://169.254.165.116:5555'
RB_IP_HELPER =  'tcp://169.254.222.67:5555'
PREVIOUS_CALIBRATION_DATA_PATH = "calibration_data.txt"

KEYPOINT_COUNT = 2000  # set number of keypoints
MAX_MATCH_Y_DISP = int() # maximum vertical displacement of valid match in pixels
MIN_MATCH_COUNT = 5  # set minimum number of better_matches
KEYPOINT_MASK_X_BOUND = 0.4 # only search for keypoints in this fraction of pixel towards the bound

FOCAL_LEN = 315 # focal length = 3.15mm volgens waveshare.com/imx219-d160.htm
s = 0 # skew parameter
KL = np.array([[FOCAL_LEN, s, WIDTH/2], [0, FOCAL_LEN, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
KR = np.array([[FOCAL_LEN, 0, WIDTH/2], [0, FOCAL_LEN, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)  # mock intrinsics
# [fx s x0; 0 fy y0; 0 0 1]

if CAMERAMODE == 1:
    PICAM = VideoStream(usePiCamera=True, resolution=RESOLUTION).start()
elif CAMERAMODE ==2:
    PICAM = cv2.VideoCapture(0)
    PICAM.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    PICAM.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
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
print("Received left calibration image")

def get_projection_objects(K):
    """
    This function returns the cylindrical warp for a given image and intrinsics matrix K
    SOURCE: ???????
    """
    y_i, x_i = np.indices((HEIGHT, WIDTH)) # pixel coordinates
    X = np.stack([x_i, y_i, np.ones_like(x_i)], axis=-1).reshape(HEIGHT * WIDTH, 3)  # to homog
    Kinv = np.linalg.inv(K)
    X = Kinv.dot(X.T).T  # normalized coords
    theta_s = X[:, 0]
    phi_s = X[:, 1]
    A = np.stack([np.cos(phi_s) * np.sin(theta_s), np.sin(phi_s), np.cos(phi_s) * np.cos(theta_s)], axis=-1).reshape(WIDTH * HEIGHT, 3)
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

    X_t, avg_y_disp = 0, 0
    for m in better_matches:
        xL, yL= keyptsL[m.queryIdx].pt
        xR, yR= keyptsR[m.trainIdx].pt
        X_t += abs(w-xL + xR)
        avg_y_disp += abs(yR-yL)
    X_t = int(X_t / len(better_matches))
    avg_y_disp = int(avg_y_disp / len(better_matches))

    if log:
        cv2.imshow('left mask', mask_L)
        cv2.imshow('right mask', mask_R)
        cv2.imshow('left img keypts', cv2.drawKeypoints(imgL, keyptsL, None, color=(255,0,0)))
        cv2.imshow('right img keypts', cv2.drawKeypoints(imgR, keyptsR, None, color=(255,0,0)))
        cv2.imshow("Good matches", cv2.drawMatches(imgL, keyptsL, imgR, keyptsR, good_matches, None, matchColor=(0,255,0)))
        cv2.imshow("Better Matches", cv2.drawMatches(imgL, keyptsL, imgR, keyptsR, better_matches, None, matchColor=(255, 0, 255)))
        cv2.waitKey(0)
    
    return X_t, avg_y_disp

def get_combine_objects(xt, log=False):
    '''
    SOURCE FOR IMAGE BLENDING CODE: ??????
    '''
    height, imgL_cropped_width = imgL.shape[:2]
    height, imgR_cropped_width = imgR.shape[:2]

    combined_width = imgL_cropped_width + imgR_cropped_width - xt
    imgL_cropped_no_overlap_width = imgL_cropped_width - xt

    imgL_cropped_noblend_width = imgL_cropped_width - ceil((1 + BLEND_FRAC)/2 * xt)
    imgR_cropped_noblend_width = imgR_cropped_width - ceil((1 + BLEND_FRAC)/2 * xt)
    pre_imgR_width = imgL_cropped_noblend_width
    post_imgL_width = imgR_cropped_noblend_width

    # linear blend masks
    maskL = np.repeat(np.tile(np.linspace(1, 0, ceil(xt * BLEND_FRAC)), (height, 1))[:, :, np.newaxis], 4, axis=2)
    maskR = np.repeat(np.tile(np.linspace(0, 1, ceil(xt * BLEND_FRAC)), (height, 1))[:, :, np.newaxis], 4, axis=2)

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
        print('xt', X_t)
        cv2.waitKey(0)

    return TL, TR, combined_width, mask_realL, mask_realR


xR_L, xR_R, MAPR1, MAPR2 = get_projection_objects(KR)
xL_L, xL_R, MAPL1, MAPL2 = get_projection_objects(KL)

SENDER.send_image(RB_IP_MAIN, np.array([MAPL1, MAPL2]))
print('MAPL1 and MAPL2 were received by helper')

imgL = cv2.remap(imgL, MAPL1, MAPL2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT)
imgR = cv2.remap(imgR, MAPR1, MAPR2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT)

if USE_KEYPOINT_TRANSLATE:
    X_t, Y_t = get_translation_parameters(imgL, imgR, log=False)
# else: fifth program argument is used

TL, TR, combined_width, mask_realL, mask_realR = get_combine_objects(X_t, log=False)

# write output image of calibration images
'''
    # def combine(log = False):
    #     imgL_translation = cv2.warpAffine(imgL, TL, (combined_width, HEIGHT))
    #     imgR_translation = cv2.warpAffine(imgR, TR, (combined_width, HEIGHT))
        
    #     final = np.uint8(imgL_translation * mask_realL + imgR_translation * mask_realR)
    #     if log:
    #         pass
    #     return final
    # cv2.imwrite("output.png", combine())
'''

SENDER = imagezmq.ImageSender(connect_to=PC_IP)

while True:
    imgR = cv2.remap(cv2.cvtColor(PICAM.read(), cv2.COLOR_BGR2BGRA), MAPL1, MAPL2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT)
    imgL = IMAGE_HUB.recv_image()[1]
    SENDER.send_image(RB_IP_MAIN, np.uint8(cv2.warpAffine(imgL, TL, (combined_width, HEIGHT)) * mask_realL + cv2.warpAffine(imgR, TR, (combined_width, HEIGHT)) * mask_realR))
    IMAGE_HUB.send_reply(b'OK')

