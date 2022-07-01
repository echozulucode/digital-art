class ImageCell:
    def __init__(self, key, cell_indices, location, size, ci, luminance, desired_passes, lab, is_transparent) -> None:
        self.ci = ci
        self.key = key
        self.luminance = luminance
        self.lab = lab
        self.source_size = size
        self.source_location = location
        self.cell_indices = cell_indices
        self.desired_passes = desired_passes
        self.passes = 0
        self.last_index = -1
        self.is_transparent = is_transparent
        self.maximum_passes = 100 if is_transparent else desired_passes * 2 + 4

