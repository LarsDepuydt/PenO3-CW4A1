#Image Stitching
You will have to follow several steps to stitch images.

##1. Selecting corresponding points
In order to stitch two images successfully, first you will need a good selection of corresponding points between your input images. For this purpose, you are allowed to use ginput function (under matplotlib.pyplot) which will operate on images and provide you to select these point pairs (x,y) with mouse clicks. You can use any other function if you know a good replacement as well.

Also, keep in mind that you are going to try out different correpondence point configurations. Thus, you don't want to waste too much time marking points. Mark lots of corresponding point pairs for each of the images sets, write it to a file and use it in your main code (you can use numpy.save and numpy.load for this process).

Important Note: Using any automated interest point detecting functionality such as SIFT, SURF or Harris is forbidden.

##2. Homography estimation
Write a function that can calculate the homogpraphy matrix between two images using the corresponding point pairs which were selected before. For your solution, the signature of this function should be:

homography = computeH(points_im1, points_im2)

points_im1 and points_im2 are the matrices which consists of corresponding point pairs. 

To calculate the homography, you are allowed to use svd function (in numpy.linalg).

##3. Image warping
After you have successfully estimated the homography between two images, you should be able to warp these images using backward transform. For your solution, the signature of this function should be:

image_warped = warp(image, homography)

For this step, you have write your own warping function. You are not allowed to use any functionality such as PIL.imtransform. However, you can use any interpolation function (in numpy, scipy and opencv) to interpolate the results of backward transform (you will need this process at some point in your solution).

##4. Blending images
Once you have the warped images, you can merge them into a single panoramic/mosaic/stitched image. If you directly put images on top of each other, every pixel you write will overwrite pixels of the previous image. Hence, you can use the image pixel that has the maximum intensity for overlapping areas.
