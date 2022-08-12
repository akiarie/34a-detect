import sys
import os
from colors import Colors
from ms_read_api import ReadApi, read_image, show_image

if len(sys.argv) != 2:
    sys.exit("must give input file")

input_path = sys.argv[1]

if not os.path.exists(input_path):
    sys.exit("input file does not exist")

output_path = f"{input_path}-post"

readApi = ReadApi(input_path)
read_result = readApi.process_image()
readApi.visualize_results(read_result, result_image_name = f"{output_path}")
