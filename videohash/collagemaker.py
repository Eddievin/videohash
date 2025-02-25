import os
from PIL import Image
from math import ceil, sqrt

from .exceptions import CollageOfZeroFramesError
from .utils import does_path_exists


# Module to create collage from list of images, the
# images are the extracted frames of the input video.


class MakeCollage(object):

    """
    Class that creates the collage from list of images.

    Collage that should be as close to the shape of a square.

    The images are arranged by timestamp of the frames, their
    index in the image_list is based on thier timestamp on the
    video. The image with the index 2 is a frame from the 3rd
    second and an index 39 is from at the 40th second. The index
    is one less due to zero-based indexing.


    Let's say we have a list with 9 images.

    As the images should be arranged in a way to resemble a
    square, we take the square root of 9 and that is 3. Now
    we need to make a 3x3 frames collage.

    Arrangement should be:
    Img1 Img2 Img3
    Img4 Img5 Img6
    Img7 Img8 Img9

    If the number of images is not a perfect square, calculate the
    square root and round it to the nearest integer.

    If number of images is 13, which is not a perfect square.

    sqrt(13) = 3.605551275463989
    round(3.605551275463989) = 4

    Thus the image should be 4x4 frames of collage.

    Arrangement should be:
    -----------------------------
    |  Img1  Img2  Img3   Img4  |
    |  Img5  Img6  Img7   Img8  |
    |  Img9  Img10 Img11  Img12 |
    |  Img13  X     X      X    |
    -----------------------------

    X denotes the empty space due to lack of images.
    But the empty spaces will not affect the robustness
    as downsized/transcoded version of the video will also
    produce these vacant spaces.
    """

    def __init__(self, image_list, output_path, collage_image_width=1024):
        """
        Checks if the list passed is not an empty list.
        Also makes sure that the output_path directory exists.

        And calls the make method, the make method creates the collage.

        :param image_list: A python list containing the list of absolute
                           path of images that are to be added in the collage.
                           The order of images is kept intact and is very important.

        :param output_path: Absolute path of the collage including
                            the image name. (This is where the collage is saved.)
                            Example: '/home/username/projects/collage.jpeg'.

        :param collage_image_width: An integer specifying the image width of the
                                    output collage. Default value is 1024 pixels.
        """
        self.image_list = image_list
        self.number_of_images = len(self.image_list)
        self.output_path = output_path
        self.collage_image_width = collage_image_width

        # The algorithm will calculate the collage image height and set
        # the value to this attribute.
        self.collage_image_height = None

        self.images_per_row_in_collage = int(round(sqrt(self.number_of_images)))

        if self.number_of_images == 0:
            raise CollageOfZeroFramesError("Can not make a collage of zero images.")

        output_path_dir = os.path.dirname(self.output_path) + "/"
        if not does_path_exists(output_path_dir):
            raise FileNotFoundError(
                "Directory at which output collage is to be saved does not exists."
            )

        self.make()

    def make(self):
        """
        Creates the collage from the list of images.

        It calculates the scale of the images on collage by
        measuring the first image width and height, there's no
        reason for choosing first one and it's arbitrary. But
        we assume that all the images passed should have same size.

        Read the comments made in the code to understand how the
        collage maker algorithm works.
        """
        # arbitrarily selecting the first image from the list, index 0
        first_frame_image = Image.open(self.image_list[0])

        # calculate the width and height of the first image of the list.
        # Here we assume that all the images passed should have same size.
        frame_image_width, frame_image_height = first_frame_image.size

        # scale is the ratio of collage_image_width and product of
        # images_per_row_in_collage with frame_image_width.
        # clearly denominator will be bigger than numerator unless
        # collage_image_width is set to a very small integer, the video
        # is of very low resolution or collage_image_width is set to a big
        # integer.
        # Therefore scale will always lie between 0 and 1, which implies that
        # the images are always going to get downsized.
        scale = (self.collage_image_width) / (
            self.images_per_row_in_collage * frame_image_width
        )

        # Calculating the scaled height and width for the frame image.
        scaled_frame_image_width = ceil(frame_image_width * scale)
        scaled_frame_image_height = ceil(frame_image_height * scale)

        # Divide the number of images by images_per_row_in_collage. The later
        # was calculated by taking the square root of total images.
        number_of_rows = ceil(self.number_of_images / self.images_per_row_in_collage)

        # We are multiplying the height of one downsized image with number of rows.
        # height of 1 downsized image = scale * frame_image_height
        # total height is clearly the multiplication of number of rows and height of
        # one downsized image.
        self.collage_image_height = ceil(scale * frame_image_height * number_of_rows)

        # Create an image of passed collage_image_width and calculated collage_image_height.
        # The downsized images will be pasted on this new base image.
        # The image is 0,0,0 RGB(black) and has little effect on the hash value also it
        # reduces the issues with the black-bars in some videos.
        collage_image = Image.new(
            "RGB", (self.collage_image_width, self.collage_image_height)
        )

        # keep track of the x and y coordinates of the resized frame images
        i, j = (0, 0)

        # iterate the frames and paste them on their position on the collage_image
        for count, frame in enumerate(self.image_list):

            # Set the x coordinate to zero if we are on the first column
            # If self.images_per_row_in_collage is 4
            # then 0,4,8 and so on should have their x coordinate as 0
            if (count % self.images_per_row_in_collage) == 0:
                i = 0

            # open the frame image, must open it to resize it using the thumbnail method
            frame = Image.open(frame)

            # scale the opened frame images
            frame.thumbnail(
                (scaled_frame_image_width, scaled_frame_image_height), Image.ANTIALIAS
            )

            # set the value of x to that of i's value.
            # i is set to 0 if we are on the first column.
            x = i

            # It ensures that y coordinate stays the same for any given row.
            # The floor of a real number is the largest integer that is less
            # than or equal to the number. floor division is used because of
            # the zero based indexing, the floor of the division stays same
            # for an entier row as the decimal values are negled by the floor.
            # for the first row the result of floor division is always zero and
            # the product of 0 with scaled_frame_image_height is also zero, they
            # y coordinate for the first row is 0.
            # For the second row the result of floor division is one and the prodcut
            # with scaled_frame_image_height enusre that the y coordinate is
            # scaled_frame_image_height below the images of the first row.
            y = (j // self.images_per_row_in_collage) * scaled_frame_image_height

            # paste the frame image on the newly created base image(base image is black)
            collage_image.paste(frame, (x, y))

            # increase the x coordinate by scaled_frame_image_width
            # to get the x coordinate of the next frame. unless the next image
            # will be on the very first column this will be the x coordinate.
            i = i + scaled_frame_image_width

            # increase the value of j by 1, this is to calculate the y coordinate of
            # next image. The increased number will be floor divided by images_per_row_in_collage
            # therefore the y coordinate stays the same for any given row.
            j += 1

        # save the base image with all the scaled images embeded on it.
        collage_image.save(self.output_path)
