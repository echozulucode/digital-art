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

                if len(ci) > 3:
                    a = ci[3]
                    if a == 0:
                        transparent_count += 1
                else:
                    a = 255

                if transparent_count >= width:
                    # return transparent color
                    return (0, 0, 0, 0)

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


def export_to_png(output_path, export_png_path = None):
    if not export_png_path:
        export_png_path = str(output_path) + '.png'

    if pathlib.Path(output_path).exists():
        drawing = svg2rlg(output_path)
        renderPM.drawToFile(
            drawing, export_png_path, fmt="PNG", bg=0x00FFFFFF
        )


class LineArtGenerator:
    def __init__(self) -> None:
        self.cols = 32
        self.rows = 32
        self.export_png_path = None
        self.debug = True
        self.maximum_lines = 2000
        self.maximum_rank = 20.0

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
        image_data.grid_size = size_per_pixel

        print(f'image size = {w}, {h}\np_x = {p_x}, p_y = {p_y}\nsize_per_pixel = {size_per_pixel}')

        dwg = svgwrite.Drawing(
            output_path,
            profile="tiny",
            size=(regions_x * size_per_pixel, regions_y * size_per_pixel),
        )

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

        
        if self.debug:
            for layer_index in range(5):
                layer_debug_output_path = str(output_path) + "_layer" + str(layer_index) + ".svg"
                layer_dwg = svgwrite.Drawing(
                    layer_debug_output_path,
                    profile="tiny",
                    size=(regions_x * size_per_pixel, regions_y * size_per_pixel),
                )

                for item in image_data.items:
                    if not item.is_transparent and item.layer == layer_index:
                        x = item.cell_indices[0] * size_per_pixel
                        y = item.cell_indices[1] * size_per_pixel
                        ci = item.ci
                        layer_dwg.add(
                                layer_dwg.rect((x, y), (size_per_pixel, size_per_pixel), fill=svgwrite.rgb(ci[0], ci[1], ci[2]))
                            )
                layer_dwg.save()
                export_to_png(output_path=layer_debug_output_path)

        # add points surrounding the image as the valid line start and end points
        for x in range(regions_x + 1):
            for y in range(regions_y + 1):
                left_edge = x == 0
                right_edge = x >= regions_x
                top_edge = y == 0
                bottom_edge = y >= regions_y
                if left_edge or right_edge or top_edge or bottom_edge:
                    region_location = (x * size_per_pixel, y * size_per_pixel)
                    image_data.add_endpoint(
                        x,
                        y,
                        region_location,
                        left_edge,
                        right_edge,
                        top_edge,
                        bottom_edge,
                    )

        # paint the endpoints (for debug)
        for endpoint in image_data.endpoints:
            # Draw a small white circle in the top left of box
            dwg.add(
                dwg.circle(
                    center=endpoint.location,
                    r=1,
                    stroke=svgwrite.rgb(15, 15, 15, "%"),
                    fill="white",
                )
            )

        image_data.create_best_fit_lines()

        if image_data.lines:
            sorted_lines = sorted(image_data.lines, key=lambda x: x.rank, reverse=False)

            total_lines = len(sorted_lines)
            best_rank = sorted_lines[0].rank
            worst_rank = sorted_lines[total_lines - 1].rank
            print(f'total lines = {total_lines}, best rank = {best_rank}, worst rank = {worst_rank}')
            self.minimum_lines = 2000
            self.maximum_lines = total_lines / 2
            if self.maximum_lines < self.minimum_lines:
                self.maximum_lines = self.minimum_lines

            self.maximum_rank = 40.0

            applied_lines = 0
            for line in sorted_lines:
                if line.rank > self.maximum_rank:
                    break

                dwg.add(
                    dwg.line(
                        line.p1,
                        line.p2,
                        stroke=svgwrite.rgb(line.ci[0], line.ci[1], line.ci[2]),
                        stroke_width=1,
                    )
                )

                applied_lines += 1

                if applied_lines > self.maximum_lines:
                    break

            print(f'applied_lines = {applied_lines}, worst rank = {sorted_lines[applied_lines-1].rank}')

        if self.debug:
            # output our svg image as raw xml
            print(dwg.tostring())

        # write svg file to disk
        dwg.save()

        if self.export_png_path:
            export_to_png(output_path=output_path, export_png_path=self.export_png_path)
