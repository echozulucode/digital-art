import math


class ImageCell:
    def __init__(
        self,
        key,
        cell_indices,
        location,
        size,
        ci,
        luminance,
        desired_passes,
        lab,
        is_transparent,
        delta_e_white,
    ) -> None:
        self.ci = ci
        self.key = key
        self.luminance = luminance
        self.lab = lab
        self.delta_e_white = delta_e_white
        self.source_size = size
        self.source_location = location
        self.cell_indices = cell_indices
        self.desired_passes = desired_passes
        self.passes = 0
        self.last_index = -1
        self.reserve_white = not is_transparent and delta_e_white < 30.0
        self.is_transparent = is_transparent
        self.maximum_passes = 100 if is_transparent else desired_passes * 2 + 4
        self.layer = int(math.floor(delta_e_white / 20))
