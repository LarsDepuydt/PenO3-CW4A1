import cv2
import numpy as np

KEYPOINTS = 1000
MIN_MATCH = 10
MAX_VERTICAL_DISP = 20 #pixels

imgL = cv2.imread("C:/Users/robin/Desktop/left0_cyl.png", cv2.IMREAD_UNCHANGED)
imgR = cv2.imread("C:/Users/robin/Desktop/right0_cyl.png", cv2.IMREAD_UNCHANGED)

# np.float32(imgL) messes with keypoint finder/matcher

#cv2.imshow('left', imgL)
#cv2.imshow('right', imgR)
#cv2.waitKey(0)
'''
Transparency masking code source:
https://stackoverflow.com/questions/45810417/opencv-python-how-to-use-mask-parameter-in-orb-feature-detector
'''
t = np.zeros((640, 480), dtype=np.uint8)
mask_cond_L = imgL[:,:,3] == 255 # create mask for non-transparant pixels
mask_L = np.array(np.where(mask_cond_L, 255, 0), dtype=np.uint8) # must use uint8 for ORB to work
mask_cond_R = imgR[:,:,3] == 255
mask_R = np.array(np.where(mask_cond_R, 255, 0), dtype=np.uint8)
#cv2.imshow('leftmask', mask_L)
#cv2.imshow('rightmask', mask_R)
#cv2.waitKey(0)

orb = cv2.ORB_create(nfeatures=KEYPOINTS)
keyptsL, descriptorsL = orb.detectAndCompute(imgL, mask=mask_L)
keyptsR, descriptorsR = orb.detectAndCompute(imgR, mask=mask_R)
#cv2.drawKeypoints(imgL, keyptsL, imgL, color=(255,0,0))
#cv2.drawKeypoints(imgR, keyptsR, imgR, color=(0,0,255))
#cv2.imshow('left', imgL)
#cv2.imshow('right', imgR)
#cv2.waitKey(0)
print(keyptsL[0], keyptsL[0].pt)
print(descriptorsL[0])
bf = cv2.BFMatcher_create(cv2.NORM_HAMMING)
matches = bf.knnMatch(descriptorsL, descriptorsR, k=2)


print(matches[0])
print(matches[0][0].distance, matches[0][0].queryIdx, matches[0][0].trainIdx, matches[0][0].imgIdx)
print(matches[0][1].distance, matches[0][1].queryIdx, matches[0][1].trainIdx, matches[0][1].imgIdx)
#print(matches)
# Finding the best matches
good_matches = []
for m, n in matches:
    if m.distance < 0.6 * n.distance:
        good_matches.append(m)

#Filter out matches with too much vertical displacement
better_matches, filtered_because_of_vert_disp = [], 0
for m in good_matches:
    if abs(keyptsL[m.queryIdx].pt[1] - keyptsR[m.trainIdx].pt[1]) <= MAX_VERTICAL_DISP:
        better_matches.append(m)
    else:
        filtered_because_of_vert_disp += 1
print("Filtered out ", filtered_because_of_vert_disp, " good matches because of vertical displacement")

#good_matches_img = cv2.drawMatches(imgL, keyptsL, imgR, keyptsR, good_matches, None, matchColor=(0,255,0))
#better_matches_img = cv2.drawMatches(imgL, keyptsL, imgR, keyptsR, better_matches, None, matchColor=(255, 0, 255))
#cv2.imshow("Good matches", good_matches_img)
#cv2.imshow("Better Matches", better_matches_img)
#cv2.waitKey(0)


print("keypoints: ", KEYPOINTS, "| matches: ", len(matches), "| good matches:", len(good_matches), "| better matches:", len(better_matches))
assert len(better_matches) >= MIN_MATCH

avg_x_disp, avg_y_disp = 0, 0
for m in better_matches:
    xL, yL= keyptsL[m.queryIdx].pt
    xR, yR= keyptsR[m.trainIdx].pt
    avg_x_disp += abs(640-xL + xR)
    avg_y_disp += abs(yR-yL)
avg_x_disp = avg_x_disp / len(better_matches)
avg_y_disp = avg_y_disp / len(better_matches)
print(avg_x_disp, avg_y_disp)
avg_x_disp = int(avg_x_disp)
avg_y_disp = int(avg_y_disp)

#imgOut = np.zeros((480+avg_y_disp,2*640-avg_x_disp, 4), np.uint8)
#print(len(imgOut), len(imgOut[0]))

for pi, pixel in enumerate(np.flip(imgL[240])):
    if pixel[3] != 0:
        xLn = pi # distance overlap point to black border
        break
for pi, pixel in enumerate(imgR[240]):
    if pixel[3] != 0:
        xRn = pi
        break
print("HOHO", xLn, xRn)

print(avg_x_disp)
BLEND_WIDTH = avg_x_disp - xLn - xRn
height, width = imgL.shape[:2]
imgL_cropped_width = width - 2*xLn
imgR_cropped_width = width - 2*xRn

total_width = imgL_cropped_width + imgR_cropped_width - BLEND_WIDTH
imgL_cropped_noblend_width = imgL_cropped_width - BLEND_WIDTH
imgR_cropped_noblend_width = imgR_cropped_width - BLEND_WIDTH
pre_imgR_width = imgL_cropped_noblend_width
post_imgL_width = imgR_cropped_noblend_width

print(BLEND_WIDTH)

# small linear masks
maskL = np.repeat(np.tile(np.linspace(1, 0, BLEND_WIDTH), (height, 1))[:, :, np.newaxis], 4, axis=2)
maskR = np.repeat(np.tile(np.linspace(0, 1, BLEND_WIDTH), (height, 1))[:, :, np.newaxis], 4, axis=2)

# full show mask
mask_imgL_cropped_noblend = np.repeat(np.tile(np.full(imgL_cropped_noblend_width, 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
mask_imgR_cropped_noblend = np.repeat(np.tile(np.full(imgR_cropped_noblend_width, 1.), (height, 1))[:, :, np.newaxis], 4, axis=2)
mask_post_imgL = np.repeat(np.tile(np.full((post_imgL_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)
mask_pre_imgR = np.repeat(np.tile(np.full((pre_imgR_width), 0.), (height, 1))[:, :, np.newaxis], 4, axis=2)

# rest aanvullen
#mask_andere1 = np.repeat(np.tile(np.full(totalWidth - img1.shape[1], 0.), (img2.shape[0], 1))[:, :, np.newaxis], 4, axis=2)
#mask_andere2 = np.repeat(np.tile(np.full(totalWidth - img1.shape[1] - (width - 2*WEG - BLEND_WIDTH), 0.), (img2.shape[0], 1))[:, :, np.newaxis], 4, axis=2)

mask_realL = np.concatenate((mask_imgL_cropped_noblend, maskL, mask_post_imgL), axis=1)
mask_realR = np.concatenate((mask_pre_imgR, maskR, mask_imgR_cropped_noblend), axis=1)

TL= np.float32([[1, 0, -xLn], [0, 1, 0]])
TR = np.float32([[1, 0, (width - 2*xLn -xRn - BLEND_WIDTH)], [0, 1, 0]])

imgL_translation = cv2.warpAffine(imgL, TL, (total_width, height))
imgR_translation = cv2.warpAffine(imgR, TR, (total_width, height))

# Generate output by linear blending
finalL = np.uint8(imgL_translation * mask_realL)
finalR = np.uint8(imgR_translation * mask_realR)

final = np.uint8(imgL_translation * mask_realL + imgR_translation * mask_realR)
cv2.imshow('output', final)
cv2.waitKey(0)

'''
imgOut[0:480, 0:640] = imgL
imgOut[
    avg_y_disp:480+avg_y_disp,
    640-avg_x_disp:2*640-avg_x_disp
      ] += imgR
#imgOut=cv2.addWeighted(imgOut[avg_y_disp:avg_y_disp+480, 640-avg_x_disp:2*640-avg_x_disp],1,imgR,1,0)
cv2.imshow('output', imgOut)
cv2.waitKey(0)
cv2.imwrite('./outputimg.png', imgOut)

'''
# Convert keypoints to an argument for findHomography
src_pts = np.float32([keyptsL[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
dst_pts = np.float32([keyptsR[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

# Establish a homography
M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

