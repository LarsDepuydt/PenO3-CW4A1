import cv2
import os
"""
mainFolder = '../mergeImages/panorama'
myFolders = os.listdir(mainFolder)
print(myFolders)

for folder in myFolders:
    path = mainFolder + '/' + folder
    images = []
    myList = os.listdir(path)
    print(f' in total no of images detected {len(myList)}')
    for imgN in myList:
        curImg = cv.imread(f'{path}/{imgN}')
        #curImg = cv.resize(curImg, (0,0), None, 0.2, 0.2)
        images.append(curImg)
        cv.imshow("test", curImg)

    stitcher = cv.Stitcher.create()
    (status, result) = stitcher.stitch(images)

    if (status == cv.STITCHER_OK):
        print('panorama generated')
        #cv.imshow(folder, result)
        #cv.waitKey(1)
    else:
        print('failed')

cv.waitKey(0)
"""


stitcher = cv2.Stitcher.create()
one = cv2.imread("../cylindrical_projection/left.jpg")
two = cv2.imread("../cylindrical_projection/right.jpg")
cv2.imshow("1", one)
cv2.waitKey(0)
cv2.imshow("2", two)
cv2.waitKey(0)
result = stitcher.stitch((one,two))

print(result)
cv2.imwrite('auto_function_result.jpg', result[1])
cv2.imshow("test", result[1])
cv2.waitKey(0)