import math

WhiteThreshold = 95


class ImageCellItem:
    def __init__(self, cell_ref, color_value) -> None:
        self.cell_ref = cell_ref
        self.color_value = color_value
        
class ImageCellCollection:
    def __init__(self) -> None:
        self.items = []
        self.median_cell = None
        self.minimum_cell = None
        self.maximum_cell = None
        self.median_list = None
        self.total = 0
        self.total_transparent = 0
        self.total_white = 0
        self.transparent_ratio = 0
        self.white_ratio = 0
        self.distance_from_min = 0
        self.distance_from_max = 0
        self.median_abs_deviation = 0.0
        self.reserve_white = False

    def add(self, cell_ref, layer_index = -1):
        if isinstance(cell_ref, list):
            for item in cell_ref:
                self.add_cell_(item, layer_index)
        else:
            self.add_cell_(cell_ref, layer_index)

    def add_cell_(self, item, layer_index):
        if item.reserve_white:
            self.reserve_white = True
        elif layer_index < 0 or item.layer == layer_index:
            if not item.is_transparent:
                self.items.append(ImageCellItem(item, item.delta_e_white))
                if item.lab[0] > WhiteThreshold:
                    self.total_white += 1
            else:
                self.total_transparent += 1
            self.total += 1

    def calculate(self):
        if self.total:
            self.transparent_ratio = self.total_transparent / self.total
            self.white_ratio = self.total_white / self.total
        else:
            self.transparent_ratio = 0
            self.white_ratio = 0

        if self.items:
            self.median_list = sorted(self.items, key=lambda x: x.color_value)
            total_elements = len(self.median_list)
            if total_elements > 1:
                self.median_cell = self.median_list[int(math.floor(total_elements / 2))]
                self.maximum_cell = self.median_list[total_elements - 1]
                self.minimum_cell = self.median_list[0]
                self.distance_from_min = abs(self.median_cell.color_value - self.minimum_cell.color_value)
                self.distance_from_max = abs(self.maximum_cell.color_value - self.median_cell.color_value)

                median_abs_deviation_total = 0.0
                for entry in self.median_list:
                    median_abs_deviation_total += abs(entry.color_value - self.median_cell.color_value)

                self.median_abs_deviation = median_abs_deviation_total / total_elements
            else:
                self.median_cell = self.median_list[0]
                self.minimum_cell = self.median_list[0]
                self.maximum_cell = self.median_list[0]
                self.distance_from_max = 0
                self.distance_from_min = 0
                self.median_abs_deviation = 0
        else:
            self.median_cell = None
            self.minimum_cell = None
            self.maximum_cell = None
