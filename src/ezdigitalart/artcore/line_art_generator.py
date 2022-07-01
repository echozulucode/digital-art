from PIL import Image
import math
import svgwrite
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
import pathlib
from .image_data import ImageData


def get_average_rgb_square(pxa, image_width, image_height, x_start, y_start, width):
    num = 0
    r = 0
    g = 0
    b = 0
    transparent_count = 0

    for x_offset in range(width):
        for y_offset in range(width):
            x = x_start + x_offset
            y = y_start + y_offset

            if x >= 0 and x < image_width and y >= 0 and y < image_height:
                ci = pxa[x, y]

                if len(ci) > 2:
                    a = ci[3]
                    if a == 0:
                        transparent_count += 1
                else:
                    a = 255

                if transparent_count >= width:
                    # return transparent color
                    return (0,0,0,0)

                if a > 0:
                    num += 1
                    r += ci[0] * ci[0]
                    g += ci[1] * ci[1]
                    b += ci[2] * ci[2]

    # Return the sqrt of the mean of squared R, G, and B sums
    if num:
        return (math.sqrt(r / num), math.sqrt(g / num), math.sqrt(b / num), 255)
    else:
        return None


class LineArtGenerator:
    def __init__(self) -> None:
        self.cols = 32
        self.rows = 32
        self.export_png_path = None
        self.debug = False

    def convert(self, input_path, output_path):
        """
        1. Read Image
           a. get average color / darkness for grid (alt: circle?)
        2. Create list of starting / ending points
        3. Iterate all points. Add number of passes based on darkness... Best fit line for 
        """
        im = Image.open(input_path)
        px = im.load()
        image_data = ImageData()

        w = im.width
        h = im.height
        p_x = math.ceil(im.width / self.cols)
        p_y = math.ceil(im.height / self.rows)
        size_per_pixel = p_x if p_x > p_y else p_y
        regions_x = math.ceil(w / size_per_pixel)
        regions_y = math.ceil(h / size_per_pixel)
        dwg = svgwrite.Drawing(output_path, profile="tiny", size=(regions_x * size_per_pixel, regions_y * size_per_pixel))

        # Import the color and luminance region into custom sized grid
        for x in range(regions_x):
            for y in range(regions_y):
                ci = get_average_rgb_square(
                    px, w, h, x * size_per_pixel, y * size_per_pixel, size_per_pixel
                )
                if ci is not None:
                    region_size = (size_per_pixel, size_per_pixel)
                    region_location = (x * size_per_pixel, y * size_per_pixel)
                    image_data.add_cell(x, y, ci, region_location, region_size)

        # add points surrounding the image as the valid line start and end points
        for x in range(regions_x + 1):
            for y in range(regions_y + 1):
                left_edge = (x == 0)
                right_edge = (x >= regions_x)
                top_edge = (y == 0)
                bottom_edge =  (y >= regions_y)
                if left_edge or right_edge or top_edge or bottom_edge:
                  region_location = (x * size_per_pixel, y * size_per_pixel)
                  image_data.add_endpoint(x, y, region_location, left_edge, right_edge, top_edge, bottom_edge)

        # paint the endpoints (for debug)
        for endpoint in image_data.endpoints:
            # Draw a small white circle in the top left of box
            dwg.add(dwg.circle(center=endpoint.location,
                r=1,
                stroke=svgwrite.rgb(15, 15, 15, '%'),
                fill='white')
            )

        image_data.initialize_best_fit()

        done = False
        maximum_iterations = 1000
        iteration_count = 0
        while not done:
            remaining = 0
            for entry in image_data.items:
                if entry.passes < entry.desired_passes:
                    remaining += entry.desired_passes - entry.passes
                    image_data.create_best_fit_line(entry)

            if remaining == 0:
                done = True

            maximum_iterations -= 1
            if maximum_iterations <= 0:
                done = True

            iteration_count += 1
            if not done:
                print(f'iterations = {iteration_count}, remaining = {remaining}')

        for line in image_data.lines:
            dwg.add(dwg.line(line.p1, line.p2, stroke=svgwrite.rgb(line.ci[0], line.ci[1], line.ci[2]), stroke_width=1))

        if self.debug:
            # output our svg image as raw xml
            print(dwg.tostring())

        # write svg file to disk
        dwg.save()

        if self.export_png_path:
            if pathlib.Path(output_path).exists():
                drawing = svg2rlg(output_path)
                renderPM.drawToFile(drawing, self.export_png_path, fmt="PNG", bg=0x00ffffff)
