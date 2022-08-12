import json
import os
import sys
from ms_read_api import ReadApi, read_image, show_image

if len(sys.argv) != 3:
    sys.exit("must give input file and output path for image")

input_path = sys.argv[1]

if not os.path.exists(input_path):
    sys.exit("input file does not exist")

output_path = sys.argv[2]
output_ext = os.path.splitext(output_path)[1][1:]
if output_ext not in ["png", "jpg"]:
    sys.exit(f"output extension must be '.png' or '.jpg'")

readApi = ReadApi(input_path)
read_result = readApi.process_image()
readApi.visualize_results(read_result, result_image_name = output_path)

lines = []
for text_result in read_result.analyze_result.read_results:
    for line in text_result.lines:
        lines += [{"bounding_box": line.bounding_box, "text": line.text}]

print(json.dumps(lines))
