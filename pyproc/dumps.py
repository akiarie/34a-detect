import json
import sys
import argparse
from stats import *
from candidates import *
import cv2 

from typing import Any

sys.path.append("../azure_process/")
from ms_read_api import ReadApi #type: ignore

parser = argparse.ArgumentParser(description='Process Azure Cognitive Services response to JSON')

parser.add_argument('-i', '--input_path',  type=str, required = False, default = "../../../VenVs/PollingEnv/Project/image_data/sample.jpg",
                    help='input path of image Form34A to be processed')
parser.add_argument('-o', '--output_path', type=str, required = False, default = "Out path",
                    help='Output path for storing results')

arguments = parser.parse_args()

candidates: dict[str, int] = InitCandidateVotes()
stats: dict[str, int] = initVotesStats()

image_path = arguments.input_path

readApi = ReadApi(image_path, "../azure_process/.env")
read_result = readApi.process_image()

lines = []

for text_result in read_result.analyze_result.read_results:
    for line in text_result.lines:
        for word in line.words:
            if (word.text).isdigit():
                lines += [{"bounding_box": word.bounding_box, "text": word.text, "possible_vote": True}]
            else:
                lines += [{"bounding_box": line.bounding_box, "text": line.text, "possible_vote": False}]
                break
print(json.dumps(lines))

