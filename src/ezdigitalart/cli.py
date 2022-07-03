import pathlib
import os
from artcore import PixelizeConverter
from artcore import LineArtGenerator


def main():
    cwd = os.getcwd()
    input_path = pathlib.Path(cwd, "data", "photo-test.png")
    output_filename = 'outputtest20'
    output_path = pathlib.Path(cwd, "work", output_filename + ".svg")

    # converter = PixelizeConverter()
    converter = LineArtGenerator()
    converter.export_png_path = pathlib.Path(cwd, "work", output_filename + ".png")
    converter.convert(input_path, output_path)


if __name__ == "__main__":
    main()
