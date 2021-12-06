import cv2
import cv2.cv2
import numpy as np
from math import pi


FOCAL_LEN_L_X = 320
FOCAL_LEN_L_Y = 320
FOCAL_LEN_R_X = 320
FOCAL_LEN_R_Y = 320
F = 170
W = 640
H = 480
s = 0
CALIBRATION_RESOLUTION = WIDTH, HEIGHT = (640, 480)
KL = np.array([[FOCAL_LEN_L_X, s, WIDTH/2], [0, FOCAL_LEN_L_Y, HEIGHT/2], [0, 0, 1]], dtype=np.uint16)

imgL = cv2.cvtColor(cv2.imread("sterio_vision/images/left/left1.png"), cv2.COLOR_BGR2BGRA)
imgR = cv2.cvtColor(cv2.imread("sterio_vision/images/right/right1.png"), cv2.COLOR_BGR2BGRA)


def get_cyl_wrap_assets_crop(K):
    """
    This function returns the cylindrical warp for a given image and intrinsics matrix K
    SOURCE: https://gist.github.com/royshil/0b21e8e7c6c1f46a16db66c384742b2b
    """
    # pixel coordinates
    y_i, x_i = np.indices((HEIGHT, WIDTH))
    X = np.stack([x_i, y_i, np.ones_like(x_i)], axis=-1).reshape(HEIGHT * WIDTH, 3)  # to homog
    Kinv = np.linalg.inv(K)
    X = Kinv.dot(X.T).T  # normalized coords
    # calculate cylindrical coords (sin\theta, h, cos\theta)
    theta_s = X[:, 0]
    phi_s = X[:, 1]
    A = np.stack([np.cos(phi_s)*np.sin(theta_s), np.sin(phi_s), np.cos(phi_s)*np.cos(theta_s)], axis=-1).reshape(WIDTH * HEIGHT, 3)
    B = K.dot(A.T).T
    #ro = 2*np.arctan2(np.sqrt(A[:,0]**2 + A[:,1]**2),A[:,2])
    #theta = np.arctan2(A[:,1],A[:,0])
    #B = np.stack([ro*np.cos(theta), ro*np.sin(theta), np.ones_like(A[:,0])], axis=-1).reshape(WIDTH * HEIGHT, 3)
    #B = K.dot(B.T).T  # project back to image-pixels plane
    B = B[:, :-1] / B[:, [-1]]
    # back from homog coords

    # make sure warp coords only within image bounds
    #B[(B[:, 0] < 0) | (B[:, 0] >= WIDTH) | (B[:, 1] < 0) | (B[:, 1] >= HEIGHT)] = -1
    x_L, x_R = [], []
    B = B.reshape(HEIGHT, WIDTH, -1)
    np.savetxt("sphericalB0", B[:,:,0])
    return x_L, x_R, B[:, :, 0].astype(np.float32), B[:, :, 1].astype(np.float32)


def warp_image(img, map1, map2):
    return cv2.remap(img, map1, map2, cv2.INTER_AREA, borderMode=cv2.BORDER_TRANSPARENT)


xL_L, xL_R, MAPL1, MAPL2 = get_cyl_wrap_assets_crop(KL)
imgL = warp_image(imgL, MAPL1, MAPL2)
imgR = warp_image(imgR, MAPL1, MAPL2)
cv2.imshow('bollinks.jpg', imgL)
#cv2.imwrite('bolrechts.jpg', imgR)
cv2.waitKey(0)