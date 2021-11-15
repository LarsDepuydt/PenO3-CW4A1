# You should replace these 3 lines with the output in calibration step
import cv2
import numpy as np

DIM=(1920, 1080)
K=np.array([[882.9706641599224, 0.0, 886.8464271188375], [0.0, 871.9774467716989, 648.1940900533385], [0.0, 0.0, 1.0]])
D=np.array([[-0.05214776804512603], [0.0003246928229686672], [-0.06727664331462517], [0.03550588688174445]])
def undistort(img_path):
    img = cv2.imread(img_path)
    h,w = img.shape[:2]
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, DIM, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cv2.imshow("undistorted", undistorted_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
        undistort("calibration_images_far/cfoto1.jpg")