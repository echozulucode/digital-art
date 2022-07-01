import itertools
import math
import sys
from tracemalloc import start
from .image_cell import ImageCell
from .image_point import ImagePoint
from .string_line import StringLine

WhiteThreshold = 95
DeltaEGoodThreshold = 10.0
DeltaEBadThreshold = 100.0


def compare_lab(l1, l2):
    dl = l2[0] - l1[0]
    da = l2[1] - l1[1]
    db = l2[2] - l1[2]
    delta_e = math.sqrt(dl * dl + da * da + db * db)
    return delta_e


def convert_rgb_to_lab(inputColor):

    num = 0
    RGB = [0, 0, 0]
    input_rgb = [inputColor[0], inputColor[1], inputColor[2]]

    for value in input_rgb:
        value = float(value) / 255

        if value > 0.04045:
            value = ((value + 0.055) / 1.055) ** 2.4
        else:
            value = value / 12.92

        RGB[num] = value * 100
        num = num + 1

    XYZ = [
        0,
        0,
        0,
    ]

    X = RGB[0] * 0.4124 + RGB[1] * 0.3576 + RGB[2] * 0.1805
    Y = RGB[0] * 0.2126 + RGB[1] * 0.7152 + RGB[2] * 0.0722
    Z = RGB[0] * 0.0193 + RGB[1] * 0.1192 + RGB[2] * 0.9505
    XYZ[0] = round(X, 4)
    XYZ[1] = round(Y, 4)
    XYZ[2] = round(Z, 4)

    XYZ[0] = float(XYZ[0]) / 95.047  # ref_X =  95.047   Observer= 2°, Illuminant= D65
    XYZ[1] = float(XYZ[1]) / 100.0  # ref_Y = 100.000
    XYZ[2] = float(XYZ[2]) / 108.883  # ref_Z = 108.883

    num = 0
    for value in XYZ:

        if value > 0.008856:
            value = value ** (0.3333333333333333)
        else:
            value = (7.787 * value) + (16 / 116)

        XYZ[num] = value
        num = num + 1

    L = (116 * XYZ[1]) - 16
    a = 500 * (XYZ[0] - XYZ[1])
    b = 200 * (XYZ[1] - XYZ[2])
    return (round(L, 4), round(a, 4), round(b, 4))


def rotated_sequence(seq, start_index):
    n = len(seq)
    for i in range(n):
        yield seq[(i + start_index) % n]


def convert_rgb_to_luminance(rgb_tuple):
    if isinstance(rgb_tuple[0], int):
        R = float(rgb_tuple[0]) / 255.0
        G = float(rgb_tuple[1]) / 255.0
        B = float(rgb_tuple[2]) / 255.0
    elif isinstance(rgb_tuple[0], float):
        R = rgb_tuple[0] / 255.0
        G = rgb_tuple[1] / 255.0
        B = rgb_tuple[2] / 255.0
    else:
        raise Exception("invalid")

    return 0.299 * R + 0.587 * G + 0.114 * B


def check_line_collision(x1, y1, x2, y2, x3, y3, x4, y4):
    # LINE/LINE

    # calculate the direction of the lines
    denominator = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denominator:
        u_a = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denominator
        u_b = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denominator
    else:
        # invalidate
        u_a = -1.0
        u_b = -1.0

    # if uA and uB are between 0-1, lines are colliding
    return u_a >= 0.0 and u_a <= 1.0 and u_b >= 0.0 and u_b <= 1.0


class ImageData:
    def __init__(self) -> None:
        self.lookup = dict()
        self.items = []
        self.endpoints = []
        self.max_y_index = 0
        self.max_x_index = 0
        self.line_lookup = dict()
        self.lines = []
        self.endpoint_combinations = None

        # the number of desired passes for 0% luminance
        self.passes_scaler = 10

        self.grid_size = 32

    def add_cell(self, column_index, row_index, ci, location, size):
        key = f"{column_index}_{row_index}"
        if key not in self.lookup:
            if column_index > self.max_x_index:
                self.max_x_index = column_index
            if row_index > self.max_y_index:
                self.max_y_index = row_index

            is_transparent = len(ci) > 3 and ci[3] == 0
            indices = (column_index, row_index)

            if is_transparent:
                luminance = 0
                lab = (0, 0, 0)
                desired_passes = 0
            else:
                luminance = convert_rgb_to_luminance(ci)
                lab = convert_rgb_to_lab(ci)
                desired_passes = int(round((1.0 - luminance) * self.passes_scaler, 0))
                if lab[0] > WhiteThreshold:
                    desired_passes = 0

            cell_data = ImageCell(
                key,
                indices,
                location,
                size,
                ci,
                luminance,
                desired_passes,
                lab,
                is_transparent,
            )
            self.lookup[key] = cell_data
            self.items.append(cell_data)
        else:
            print(f"duplicate: {key}")

    def add_endpoint(
        self, x_index, y_index, location, left_edge, right_edge, top_edge, bottom_edge
    ):
        endpoint = ImagePoint(
            x_index, y_index, location, left_edge, right_edge, top_edge, bottom_edge
        )
        self.endpoints.append(endpoint)

    def get_cell(self, column_index, row_index):
        key = f"{column_index}_{row_index}"
        if key in self.lookup:
            return self.lookup[key]
        else:
            return None

    def check_cell_collision(self, column_index, row_index, p1, p2):
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
        cx1 = column_index * self.grid_size
        cy1 = row_index * self.grid_size
        height = self.grid_size
        width = self.grid_size

        # check left
        collision = check_line_collision(x1, y1, x2, y2, cx1, cy1, cx1, cy1 + height)

        if not collision:
            # check right
            collision = check_line_collision(
                x1, y1, x2, y2, cx1 + width, cy1, cx1 + width, cy1 + height
            )

            if not collision:
                # check top
                collision = check_line_collision(
                    x1, y1, x2, y2, cx1, cy1, cx1 + width, cy1
                )

                if not collision:
                    # check bottom
                    collision = check_line_collision(
                        x1, y1, x2, y2, cx1, cy1 + height, cx1 + width, cy1 + height
                    )

        return collision

    def check_column_collision(self, column_index, p1, p2):
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
        cx1 = column_index * self.grid_size
        cx2 = cx1 + self.grid_size
        height = (self.max_y_index + 1) * self.grid_size

        # check left
        collision = check_line_collision(x1, y1, x2, y2, cx1, 0.0, cx1, height)
        if not collision:
            # check right
            collision = check_line_collision(x1, y1, x2, y2, cx2, 0, cx2, height)

        return collision

    def get_intersecting_cells(self, line_start, line_end):
        """ """
        result = []

        for x in range(self.max_x_index):
            if self.check_column_collision(x, line_start, line_end):
                for y in range(self.max_y_index):
                    if self.check_cell_collision(x, y, line_start, line_end):
                        cell_data = self.get_cell(x, y)
                        if cell_data:
                            result.append(cell_data)

        return result

    def initialize_best_fit(self):
        all_combinations = itertools.combinations(self.endpoints, 2)
        self.endpoint_combinations = []
        for item_tuple in all_combinations:
            if item_tuple[0].allow_line(item_tuple[1]):
                self.endpoint_combinations.append(item_tuple)

    def create_best_fit_line(self, entry):
        # only create lines for this entry for non-white spaces
        if entry.lab[0] < WhiteThreshold:
            start_index = (entry.last_index + 1) % len(self.endpoint_combinations)
            index = start_index
            for item_tuple in rotated_sequence(self.endpoint_combinations, start_index):
                key = item_tuple[0].line_id(item_tuple[1])
                if key not in self.line_lookup:
                    good_fit = 0
                    bad_fit = 0
                    p1 = item_tuple[0]
                    p2 = item_tuple[1]
                    if self.check_cell_collision(
                        entry.cell_indices[0],
                        entry.cell_indices[1],
                        p1.location,
                        p2.location,
                    ):
                        cell_list = self.get_intersecting_cells(
                            p1.location, p2.location
                        )
                        if cell_list:
                            for cell_item in cell_list:
                                if entry.key == cell_item.key:
                                    # this is of course a good fit
                                    good_fit += 1
                                else:
                                    delta_e = compare_lab(entry.lab, cell_item.lab)
                                    if delta_e < DeltaEGoodThreshold:
                                        good_fit += 1
                                    elif delta_e > DeltaEBadThreshold:
                                        if (
                                            cell_item.passes + 1
                                            >= cell_item.maximum_passes
                                        ):
                                            bad_fit += 1
                                    else:
                                        if (
                                            cell_item.passes + 1
                                            >= cell_item.maximum_passes
                                        ):
                                            bad_fit += 1

                            if bad_fit == 0:
                                string_line = StringLine(
                                    key, p1.location, p2.location, entry.ci
                                )
                                self.line_lookup[key] = string_line
                                self.lines.append(string_line)
                                entry.last_index = index

                                for cell_item in cell_list:
                                    delta_e = compare_lab(entry.lab, cell_item.lab)
                                    if delta_e < DeltaEGoodThreshold:
                                        cell_item.passes += 1
                index += 1
