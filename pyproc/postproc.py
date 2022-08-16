from dataclasses import InitVar
from distutils import extension
import json
import argparse
from re import L 
import sys 
import cv2 

from pprint import pprint
from typing import Optional

from candidates import (
    InitCandidateVotes,
    fillCandidateVotes,
    isCandidateVotesEqualsSum
)
from stats import (
    initVotesStats,
    fillVotesStats
)
from helpers import (
    Line, 
    getBounds, 
    getCandidateVotesTotal,
    getOtherVotesTotal,
    TopLeftandBottomRight,
    sortVotesByY
    )
from errorcorrection import (
    candidate_names,
    stats_names,
    getLinesWithinBounds,
    allCandidateLines,
    allStatsLines,
    getErroneousVote,
    allIndividualVotesPresent,
    sumAllVotes
)

parser = argparse.ArgumentParser(description='Process JSON results')
parser.add_argument('-f', '--file', type=str, required = True,
                    help='JSON file for processing')
parser.add_argument('-i', '--image_dir', type=str, required = False,
                    help='Image directory')
parser.add_argument('-e', '--extension', type=str, required = False, default = ".png",
                    help='Image extension')
arguments = parser.parse_args()

file: str = arguments.file
image_dir: str = arguments.image_dir
image_extension: str = arguments.extension

if not file.endswith("txt"):
    print(f"File: {file} needs to be text")
    sys.exit(0)

def getImage(file: str):
    image_path = f"{image_dir}/{file.split('/')[-1][:-4]}{image_extension}"
    image = readImage(image_path)
    return image 

def readImage(path: str) -> cv2.Mat:
    image = cv2.imread(path)
    return image 

def showImage(image: cv2.Mat, title: str = "image") -> None:
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def drawOnImage(
    image: cv2.Mat, 
    bounds:list[Line],
    color = (0, 0, 255)) -> None:
    thickness = 5
    for bound in bounds:
        top_left, bottom_right = TopLeftandBottomRight(bound)
        cv2.rectangle(image, top_left, bottom_right, color, thickness)

def getUpperLowerDecBounds(lines: list[Line]) -> list[
    Optional[list[int]]
]:
    upper_bounds: Optional[list[int]] = None
    lower_bounds: Optional[list[int]] = None
    declaration_bounds: Optional[list[int]] = None
    for line in lines:
        search_up = "number votes cast favour each candidate"
        search_down = "decision(s) on disputed votes if any"
        bound = getBounds(search_up, line)
        if bound is not None:
            upper_bounds = bound
        bound = getBounds(search_down, line)
        if bound is not None:
            lower_bounds = bound
        bound = getBounds("declaration", line, min = 1)
        if bound is not None:
            declaration_bounds = bound
    return [upper_bounds, lower_bounds, declaration_bounds]

def getVotesInCriticalSection(
    votes: list[Line],
    upper_bounds: Optional[list[int]],
    lower_bounds: Optional[list[int]],
    declaration_bounds: Optional[list[int]],
    x_filter_candidate_votes: int,
) -> list[list[Line]]:
    candidate_votes_total = getCandidateVotesTotal(votes, upper_bounds, lower_bounds, x_filter_candidate_votes)
    other_votes_total = getOtherVotesTotal(votes, lower_bounds, declaration_bounds)
    return [
        candidate_votes_total,
        other_votes_total
    ]

try:
    with open(file) as f:
        lines: list[Line] = json.load(f)
        # get bounds to critical section
        (
            upper_bounds, 
            lower_bounds,
            declaration_bounds
        ) = getUpperLowerDecBounds(lines)

        lines_within_bounds = getLinesWithinBounds(lines, upper_bounds[1], lower_bounds[1])
        candidate_lines = allCandidateLines(lines_within_bounds)
        reference_y, x_filter_candidate_votes = candidate_lines[0]['bounding_box'][1:3]

        if not (upper_bounds and lower_bounds):
            print(f"{file} === Candidate vote bounds not found!")
            sys.exit(0)
        votes: list[Line] = [line for line in lines if line['possible_vote']]

        (
            candidate_votes_total,
            other_votes_total
        ) = getVotesInCriticalSection(votes, upper_bounds,lower_bounds, declaration_bounds, x_filter_candidate_votes)
        image = getImage(file)
        len_candidate_votes_total = len(candidate_votes_total)
        len_other_votes_total = len(other_votes_total)
        final_votes: dict[str, int] = InitCandidateVotes()
        final_stats: dict[str, int] = initVotesStats()
        candidate_votes_sorted = sortVotesByY(candidate_votes_total)
        other_votes_sorted = sortVotesByY(other_votes_total)
        
        primary_votes = [int(i['text']) for i in candidate_votes_sorted]
        secondary_votes = [int(i['text']) for i in other_votes_sorted]
        total = sumAllVotes(
                        allIndividualVotesPresent(candidate_votes_sorted, reference_y + 500)
                        )
        if len_candidate_votes_total == 5:
            if len_candidate_votes_total == len_other_votes_total:
                if primary_votes[-1] == secondary_votes[-1]:
                    final_votes = fillCandidateVotes(primary_votes, final_votes)
                    final_stats = fillVotesStats(secondary_votes, final_stats)
                    verified = isCandidateVotesEqualsSum(primary_votes[:-1], primary_votes[-1])
                    if verified:
                        print(f"{file} == Verified")
                else:
                    print(f"{file} == All values but Assertion of Total", end=" ")
                    final_votes = fillCandidateVotes(primary_votes, final_votes)
                    final_stats = fillVotesStats(secondary_votes, final_stats)
                    if total == final_votes["total"]:
                        final_stats["validcast"] = total
                    elif total == final_stats["validcast"]:
                        final_votes["total"] = total
                    else:
                        print(f"{file} == Irrepairable!")
                        sys.exit(0)
                    print(" == Verified!")
            else:
                print(f"{file} == Auxiliary votes missing", end="")
                lines_within_bounds = getLinesWithinBounds(lines, lower_bounds[1], declaration_bounds[1])
                stat_lines = allStatsLines(lines_within_bounds)
                erronous_other_vote = getErroneousVote(stat_lines, candidate_votes_total)
                indexOf = stats_names.index(erronous_other_vote['text'])
                final_votes = fillCandidateVotes(primary_votes, final_votes)
                if indexOf == 4 and len_other_votes_total == 4:
                    if total == final_votes["total"]:
                        final_stats = fillVotesStats(secondary_votes + [final_votes["total"]], final_stats)
                    else:
                        secondary_votes.insert(indexOf, -1)
                        final_stats = fillVotesStats(secondary_votes + [final_votes["total"]], final_stats)
                else:
                    print(" == Secondary stats not verified!")
                print(" == Verified")

                # drawOnImage(image, candidate_votes_total)
                # drawOnImage(image, other_votes_total)
                # drawOnImage(image, candidateLines)
                # drawOnImage(image, stat_lines)
                # showImage(image, f"{file}")


        elif len_candidate_votes_total == 4:
            print(f"{file} == Primary votes (or Total) missing", end=" ")
            all_individual_votes = allIndividualVotesPresent(candidate_votes_sorted, reference_y + 500)
            sum_all_votes = sumAllVotes(all_individual_votes)
            # print(f"{other_votes_sorted[-1]['text']} ~~~ {sum_all_votes}")
            if len(all_individual_votes) >= 4:
                if int(other_votes_sorted[-1]['text']) == sum_all_votes:
                        final_votes = fillCandidateVotes(primary_votes + [int(other_votes_sorted[-1]['text'])], final_votes)
                        if secondary_votes == 5:
                            final_stats = fillVotesStats(secondary_votes, final_stats)
                            lines_within_bounds = getLinesWithinBounds(lines, lower_bounds[1], declaration_bounds[1])
                            stat_lines = allStatsLines(lines_within_bounds)
                            erronous_other_vote = getErroneousVote(stat_lines, other_votes_total)
                            indexOf = stats_names.index(erronous_other_vote['text'])
                            pprint(final_votes)
                            pprint(final_stats)
                            print(" == Verified")
            else:
                erronous_candidate_vote = getErroneousVote(candidate_lines, candidate_votes_total)
                indexOf = candidate_names.index(erronous_candidate_vote['text'])
                results = [int(i['text']) for i in candidate_votes_sorted]
                if len(other_votes_sorted) == 5:
                    results.insert(indexOf, int(other_votes_sorted[-1]['text']) - sum_all_votes)
                    # print(f"ERROR ==== {indexOf} : {erronous_candidate_vote['text']}")
                else:
                    # TO BE REMOVED
                    results.insert(indexOf, int(other_votes_sorted[-1]['text']) - sum_all_votes)
                    final_votes = fillCandidateVotes(results, final_votes)
                    print(f"{file} == Verified")
                    # END -- TO BE REMOVED
            
        else:
            print(f"{file} Irrepairable! {len_candidate_votes_total}") 
            # drawOnImage(image, other_votes_total)
            # drawOnImage(image, candidateLines)
            # drawOnImage(image, stat_lines)
        drawOnImage(image, candidate_votes_sorted)
        drawOnImage(image, other_votes_sorted)
        showImage(image, f"{file}")
except FileNotFoundError:
    print(f"Check if file path {file} is correct!")