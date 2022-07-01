import imp
import pathlib
import os
from artcore import PixelizeConverter
from artcore import LineArtGenerator


def main():
    print("Hello World!")
    cwd = os.getcwd()
    input_path = pathlib.Path(cwd, "data", "stop-sign-test.png")
    output_path = pathlib.Path(cwd, "outputtest5.svg")

    # converter = PixelizeConverter()
    converter = LineArtGenerator()
    converter.export_png_path = pathlib.Path(cwd, "outputtest5.png")
    converter.convert(input_path, output_path)


if __name__ == "__main__":
    main()
