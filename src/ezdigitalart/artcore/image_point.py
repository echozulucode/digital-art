class ImagePoint:
    def __init__(self, x_index, y_index, location, left_edge, right_edge, top_edge, bottom_edge) -> None:
        self.x_index = x_index
        self.y_index = y_index
        self.location = location
        self.left_edge = left_edge
        self.right_edge = right_edge
        self.top_edge = top_edge
        self.bottom_edge = bottom_edge

    def allow_line(self, other):
        if not other:
            result = False
        elif self.left_edge and other.left_edge:
            result = False
        elif self.top_edge and other.top_edge:
            result = False
        elif self.right_edge and other.right_edge:
            result = False
        elif self.bottom_edge and other.bottom_edge:
            result = False
        else:
            result = True

        return result

    def unique_id(self):
        return f'{self.x_index}_{self.y_index}'

    def line_id(self, other):
        return f'{self.x_index}_{self.y_index}_{other.x_index}_{other.y_index}'
