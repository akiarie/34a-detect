import glob
from typing import final 
import cv2 
import numpy as np 
import editdistance
import matplotlib.pyplot as plt 

import easyocr
from coolors import Coolors
from ms_read_api import ReadApi, show_image
from tqdm import tqdm 
from pprint import pprint 

readApi = ReadApi()

types = ('*.jpg', '*.png') # the tuple of file types
image_paths = []
for files in types:
    image_paths.extend(glob.glob(f"./image_data/{files}"))

print(image_paths)
reader = easyocr.Reader(['en'])

def read_image(image_path, resize = False):
    image = cv2.imread(image_path, 3)
    if resize:
        image = cv2.resize(image, (3400, 4900))
    return image 

def region_of_interest(image, title_y_start = None):
    color = (0, 0, 255)
    thickness = 5
    start_point = (150, title_y_start + 50)
    end_point = (3300, title_y_start + 1700)
    region = image[
        start_point[1]: end_point[1],
        start_point[0]: end_point[0]
        ]
    return (region, ((start_point[0], start_point[1]),(end_point[0], end_point[1])))

def draw_region(image, bounds):
    top_left = bounds[0]
    bottom_right = bounds[1]
    color = (0, 0, 255)
    thickness = 5
    cv2.rectangle(image, top_left, bottom_right, color, thickness)

def preprocess_image(image, adaptive = False):
    if adaptive:
        thresh = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    else:
        _, thresh = cv2.threshold( image, 155, 255, cv2.THRESH_BINARY)
    return thresh

def process_next_image(i = 0):
    if i != len(image_paths) - 1:
        page = read_image(image_paths[i])  
        result = reader.readtext(page)
        result = [{
            "levenshtein": editdistance.eval('Number of votes cast in favour of each candidate', i[1]),
            "coordinates": (i[0][0], i[0][2]),
            "word": i[1]
            } for i in result]
        title_data = sorted(result, key=lambda d: d['levenshtein'])[0]
        top_left = title_data['coordinates'][0]
        _, bounds = region_of_interest(page, title_y_start=top_left[1])
        draw_region(page, bounds)
        process_next_image(i + 1)
    else:
        return None

def euclidean(reference, value):
    x1, y1 = reference[0], reference[1]
    x2, y2 = value[0], value[1]
    return ((x1 - x2)**2 + (y1 - y2)**2)**.5

# process_next_image()
def process_candidate_info(read_result):
    votes = []
    for text_result in read_result.analyze_result.read_results:
        for line in text_result.lines:
            if (line.text).isdigit():
                vote = int(line.text)
                top_left = [int(i) for i in line.bounding_box[:2]]
                bottom_right = [int(i) for i in line.bounding_box[4:6]]
                votes.append({
                    "votes": vote,
                    "coordinates": (top_left, bottom_right),
                    })
    def process_candidate_votes(top_left, votes):
        _, top_left_y = top_left
        result = min(votes, key = lambda x: abs(
            x['coordinates'][0][1] - top_left_y
            ))
        return result
    candidates = [
        "RAILA",
        "WILLIAM",
        "GEORGE",
        "DAVID"
    ]
    get_votes = True
    candidate_votes_ = {}
    for text_result in read_result.analyze_result.read_results:
        for line in text_result.lines:
            if "Declaration" in line.text:
                declaration_coords = [int(i) for i in line.bounding_box[:2]]
    print("READ RESULT: ", read_result.analyze_result.read_results)
    import sys 
    sys.exit(0)
    for text_result in read_result.analyze_result.read_results:
        for line in text_result.lines:
            for candidate in candidates:  
                if candidate in ((line.text).split()):
                    candidate_top_left = [int(i) for i in line.bounding_box[:2]]
                    candidate_bottom_right = [int(i) for i in line.bounding_box[4:6]]
                    if get_votes:
                        sorted_votes = sorted(votes, key = lambda x: abs(
                            x['coordinates'][0][1] - int(candidate_top_left[1])
                        ))
                        final_votes = sorted(sorted_votes[:4], key = lambda x: x['coordinates'][0][1]) 
                        candidate_votes_["RAILA"] = final_votes[0]['votes']
                        candidate_votes_["RUTO"] = final_votes[1]['votes']
                        candidate_votes_["DAVID"] = final_votes[2]['votes']
                        candidate_votes_["GEORGE"] = final_votes[3]['votes']
                        pprint(candidate_votes_)
                       
                        greater_final_votes = lambda x: x['coordinates'][1][1] > final_votes[3]['coordinates'][1][1]
                        temp_results = list(filter(greater_final_votes, sorted_votes))
                        print('Temp results: ', temp_results)
                        temp_ = sorted(temp_results, key = lambda x: abs(
                            x['coordinates'][1][0] - final_votes[3]['coordinates'][1][0]
                        )) 

                        print(f"Total votes: {temp_[:3]}")

                        get_votes_after_candidates = lambda x: x['coordinates'][1][0] > candidate_bottom_right[0]
                        tallying_results = list(filter(get_votes_after_candidates, votes))
                        get_votes_before_declaration = lambda x: x['coordinates'][0][1] < declaration_coords[1]
                        declaration_results = list(filter(get_votes_before_declaration, tallying_results)) 
                        after_results = sorted(declaration_results, key = lambda x: x['coordinates'][0][0])
                        pprint(after_results[:5])
                        return

                    # print(f"{Coolors.CRED} CANDIDATE: {Coolors.CGREEN} {line.text} {Coolors.CEND}")
                    # print(f"{Coolors.CRED} CANDIDATE COORDINATES: {Coolors.CGREEN} {candidate_top_left} {Coolors.CEND}")
                    # candidate_votes = process_candidate_votes(candidate_top_left, votes)
                    # print(f"{Coolors.CGREEN}VOTES: {candidate_votes['votes']}{Coolors.CEND}")
                    # print(f"{Coolors.CBEIGE}{'='*50}{Coolors.CEND}")

index = 0
for image_path in image_paths:
    image = read_image(image_path)
    readApi = ReadApi(image_url = image_path)
    read_result = readApi.process_image()
    image = readApi.visualize_results(
        image, 
        read_result, 
        result_image_name = f"{(image_path[:-4]).split('/')[-1]}", 
        results=False)
    print(f"{Coolors.CBLUE}{image_path}{Coolors.CEND}")
    process_candidate_info(read_result)
    index += 1
