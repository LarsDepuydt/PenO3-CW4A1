# You should replace these 3 lines with the output in calibration step
import cv2
import numpy as np

DIM=(640, 480)
K=np.array([[308.4274361323937, 0.0, 307.74004197343186], [0.0, 307.15971371728705, 251.85734467095995], [0.0, 0.0, 1.0]])
D=np.array([[-0.02268523653207129], [-0.024552020182573187], [-4.141383624332057e-05], [0.011483828520533408]])

def undistort(img_path):
    img = cv2.imread(img_path)
    h,w = img.shape[:2]
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cv2.imwrite("undistorted.jpg", undistorted_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
        undistort("calibration_images_far/cfoto1.jpg")