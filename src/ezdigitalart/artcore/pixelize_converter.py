from PIL import Image
import math
import svgwrite
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
import pathlib


def get_average_rgb_square(pxa, image_width, image_height, x_start, y_start, width):
    num = 0
    r = 0
    g = 0
    b = 0
    for x_offset in range(width):
        for y_offset in range(width):
            x = x_start + x_offset
            y = y_start + y_offset

            if x >= 0 and x < image_width and y >= 0 and y < image_height:
                ci = pxa[x, y]
                r += ci[0] * ci[0]
                g += ci[1] * ci[1]
                b += ci[2] * ci[2]
                num += 1

    # Return the sqrt of the mean of squared R, G, and B sums
    if num:
        return (math.sqrt(r / num), math.sqrt(g / num), math.sqrt(b / num))
    else:
        return None


class PixelizeConverter:
    def __init__(self) -> None:
        self.cols = 32
        self.rows = 32
        self.export_png_path = None
        self.debug = False

    def convert(self, input_path, output_path):
        im = Image.open(input_path)
        px = im.load()

        w = im.width
        h = im.height
        p_x = math.ceil(im.width / self.cols)
        p_y = math.ceil(im.height / self.rows)
        size_per_pixel = p_x if p_x > p_y else p_y
        regions_x = math.ceil(w / size_per_pixel)
        regions_y = math.ceil(h / size_per_pixel)
        dwg = svgwrite.Drawing(output_path, profile="tiny", size=(regions_x, regions_y))

        for x in range(regions_x):
            for y in range(regions_y):
                ci = get_average_rgb_square(
                    px, w, h, x * size_per_pixel, y * size_per_pixel, size_per_pixel
                )
                if ci is not None:
                    dwg.add(
                        dwg.rect((x, y), (1, 1), fill=svgwrite.rgb(ci[0], ci[1], ci[2]))
                    )

        if self.debug:
            # output our svg image as raw xml
            print(dwg.tostring())

        # write svg file to disk
        dwg.save()

        if self.export_png_path:
            if pathlib.Path(output_path).exists():
                drawing = svg2rlg(output_path)
                renderPM.drawToFile(
                    drawing, self.export_png_path, fmt="PNG", bg=0x00FFFFFF
                )
