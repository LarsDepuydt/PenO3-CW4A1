# You should replace these 3 lines with the output in calibration step
import cv2
import numpy as np

DIM=(640, 480)
K=np.array([[308.4274361323937, 0.0, 307.74004197343186], [0.0, 307.15971371728705, 251.85734467095995], [0.0, 0.0, 1.0]])
D=np.array([[-0.02268523653207129], [-0.024552020182573187], [-4.141383624332057e-05], [0.011483828520533408]])

def undistort(img_path, balance=1.0, dim2=None, dim3=None):
    img = cv2.imread(img_path)
    dim1 = img.shape[:2][::-1]  #dim1 is the dimension of input image to un-distort
    #assert dim1[0]/dim1[1] == DIM[0]/DIM[1], "Image to undistort needs to have same aspect ratio as the ones used in calibration"
    if not dim2:
        dim2 = dim1
    if not dim3:
        dim3 = dim1
    scaled_K = K * dim1[0] / DIM[0]  # The values of K is to scale with image dimension.
    scaled_K[2][2] = 1.0  # Except that K[2][2] is always 1.0
    # This is how scaled_K, dim2 and balance are used to determine the final K used to un-distort image. OpenCV document failed to make this clear!
    new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(scaled_K, D, dim2, np.eye(3), balance=balance)
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(scaled_K, D, np.eye(3), new_K, dim3, cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    hight, width = undistorted_img.shape[:2]
    print(hight, width)
    print(undistorted_img)
    cv2.imwrite("left.jpg", undistorted_img[70:405, 20:640])


if __name__ == '__main__':
    undistort( "sterio_vision/images/left/left3.png")
