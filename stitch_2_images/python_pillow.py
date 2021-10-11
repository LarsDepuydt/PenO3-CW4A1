import cv as cv
from PIL import Image
#Read the two images
image1 = Image.open('../images/testing_images_online/lokaal/mergePart1.jpg')
#image1.show()
image2 = Image.open('../images/testing_images_online/lokaal/mergePart2.jpg')
#image2.show()

########################
# merge 2 images
########################

#image1 = image1.resize((426, 240))
image1_size = image1.size
image2_size = image2.size
new_image = Image.new('RGB',(2*image1_size[0], image1_size[1]), (250,250,250))
new_image.paste(image1,(0,0))
new_image.paste(image2,(image1_size[0],0))
new_image.save("mergeImages/merged_image.jpg","JPEG")
new_image.show()

