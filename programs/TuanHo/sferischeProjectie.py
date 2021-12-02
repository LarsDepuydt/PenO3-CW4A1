'''
1. each point 𝑷′(𝑥′,𝑦′) in the input fisheye image is projected 
to a 3-D point 𝑷(cos𝜑𝑠 sin𝜃𝑠, cos𝜑𝑠 cos𝜃𝑠 , sin𝜑𝑠) in the 
unit  sphere.

MET: 𝜃𝑠 =𝑓 𝑥′𝑊 −0.5,
𝜑𝑠 =𝑓 𝑦′𝐻  −0.5

EN: 𝑓 is  the  lens’  field  of  view  (in  degree)


2. 𝑥′′ =0.5𝑊+𝜌cos𝜃, 𝑦′′ =0.5𝐻+𝜌sin𝜃, and 𝜃 = tan−1(𝑧 𝑥⁄ )
MET: 𝜌= 𝐻 𝑓 tan−1√𝑥2+𝑧2 𝑦 
'''

import numpy as np
import cv2

F = 170   # the  lens’  field  of  view  (in  degree)
W = 640   # width
H = 480   # height

def sferical_projection(pixel_array):
  x_in, y_in = pixel_array
  theta_s = F * (x_in / W) - 0.5
  phi_s = F * (y_in / H) - 0.5

  x, y, z = [np.cos(phi_s) * np.sin(theta_s), np.cos(phi_s) * np.cos(theta_s), np.sin(phi_s)]
  Ro = (H / F) * np.arctan((np.sqrt(x**2 + z**2)) / y)

  theta = np.arctan(z / x)
  x_output = 0.5 * W + Ro * np.cos(theta)
  y_output = 0.5 * H + Ro * np.sin(theta)
  return x_output, y_output


def sferischeWarp(img):
    """This function returns the sferical warp for a given image"""
    h_, w_ = img.shape[:2]

    # pixel coordinates
    y_i, x_i = np.indices((h_, w_))
    X = np.stack([x_i, y_i], axis=-1).reshape(h_ * w_, 2)

    return_img = map(sferical_projection, X)
    print(list(return_img))

    return list(return_img)



if __name__ == '__main__':
    img = cv2.imread('/Users/lars/Desktop/PenO3-CW4A1/programs/cylindrical_projection/sterio_vision/images/left/left0.png')
    img_sf = sferischeWarp(img)
    cv2.imwrite('/Users/lars/Desktop/PenO3-CW4A1/programs/TuanHo/sferisch.png', img_sf)