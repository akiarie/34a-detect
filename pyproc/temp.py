import json
import argparse
import sys 
import cv2 
from typing import List, Dict, Tuple
import logging

from typing import Optional, Any

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
parser.add_argument('-e', '--extension', type=str, required = False, default = "png",
                    help='Image extension')

arguments = parser.parse_args()

file: str = arguments.file
image_dir: str = arguments.image_dir
image_extension: str = arguments.extension

if not file.endswith("txt"):
    logging.error(f"File: {file} needs to be text")
    sys.exit(0)

def getImage(file: str):
    image_path = f"{image_dir}/{file.split('/')[-1][:-4]}.{image_extension}"
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
    bounds:List[Line],
    color = (0, 0, 255)) -> None:
    thickness = 5
    for bound in bounds:
        top_left, bottom_right = TopLeftandBottomRight(bound)
        cv2.rectangle(image, top_left, bottom_right, color, thickness)

def getUpperLowerDecBounds(lines: List[Line]) -> List[
    Any
]:
    upper_bounds: Optional[List[int]] = None
    lower_bounds: Optional[List[int]] = None
    declaration_bounds: Optional[List[int]] = None
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
    votes: List[Line],
    upper_bounds: Optional[List[int]],
    lower_bounds: Optional[List[int]],
    declaration_bounds: Optional[List[int]],
    x_filter_candidate_votes: int,
) -> List[List[Line]]:
    candidate_votes_total = getCandidateVotesTotal(votes, upper_bounds, lower_bounds, x_filter_candidate_votes)
    other_votes_total = getOtherVotesTotal(votes, lower_bounds, declaration_bounds)
    return [
        candidate_votes_total,
        other_votes_total
    ]


def CandidatesVotes5(
    candidate_votes_sorted: List[Line], 
    final_votes: Dict[str, int],
    ):
    primary_votes = [int(i['text']) for i in candidate_votes_sorted]
    final_votes = fillCandidateVotes(primary_votes, final_votes)
    return final_votes

def CandidateVotes4(
    candidate_lines: List[Line],
    final_votes: Dict[str, int], 
    candidate_votes_sorted: List[Line],
    reference_y: int,
) -> Tuple[Dict[str, int], int]:
    all_individual_votes = allIndividualVotesPresent(candidate_votes_sorted, reference_y)
    primary_votes = [int(i['text']) for i in candidate_votes_sorted]
    if len(all_individual_votes) == 4:
        primary_votes.insert(len(primary_votes), -1)
        final_votes = fillCandidateVotes(primary_votes, final_votes)
        return final_votes, len(primary_votes)
    else:
        erronous_candidate_vote = getErroneousVote(candidate_lines, candidate_votes_sorted)
        index = candidate_names.index(erronous_candidate_vote['text'])
        primary_votes.insert(index, -1)
        final_votes = fillCandidateVotes(primary_votes, final_votes)
        return final_votes, index

def OtherVotes5(
    other_votes_sorted: List[Line], 
    final_stats: Dict[str, int],
    ):
    secondary_votes = [int(i['text']) for i in other_votes_sorted]
    final_stats = fillVotesStats(secondary_votes, final_stats)
    return final_stats

def OtherVotes4(
    lines: List[Line],
    lower_bounds: Any,
    declaration_bounds: Any,
    other_votes_sorted: List[Line],
    final_stats: Dict[str, int],
) -> Tuple[Dict[str, int], int]:
        lines_within_bounds = getLinesWithinBounds(lines, lower_bounds[1], declaration_bounds[1])
        stat_lines = allStatsLines(lines_within_bounds)
        secondary_votes = [int(i['text']) for i in other_votes_sorted]
        erronous_other_vote = getErroneousVote(stat_lines, other_votes_sorted)
        index = stats_names.index(erronous_other_vote['text'])
        secondary_votes.insert(index, -1)
        final_stats = fillVotesStats(secondary_votes, final_stats)
        return final_stats, index

def individualEqualsTotal(
    final_votes: Dict[str, int]
    ) -> bool:
    values = list(final_votes.values())
    verified = isCandidateVotesEqualsSum(values[:-1], values[-1])
    return verified

def correctCandidatesTotal(
    final_votes: Dict[str, int], 
    final_stats: Dict[str, int], 
    total:int):
    if total == final_stats["validcast"]:
        final_votes['total'] = total 
    return final_votes
        
def correctStatsTotal(
    final_votes: Dict[str, int],
    final_stats: Dict[str, int], 
    total:int):
    if total == final_votes["total"]:
        final_stats["validcast"] = total 
    return final_stats

def checkTwoTotals(
    final_votes: Dict[str, int], 
    final_stats: Dict[str, int]
    ) -> bool:
    return final_votes['total'] == final_stats["validcast"]


try:
    with open(file) as f:
        lines: List[Line] = json.load(f)
        (
            upper_bounds, 
            lower_bounds,
            declaration_bounds
        ) = getUpperLowerDecBounds(lines)
        try:
            lines_within_bounds = getLinesWithinBounds(lines, upper_bounds[1], lower_bounds[1])
        except TypeError:
            logging.error(f"{file} == Required bounds cannot be achieved!")
            sys.exit(0)

        candidate_lines = allCandidateLines(lines_within_bounds)
        reference_y, x_filter_candidate_votes = candidate_lines[-1]['bounding_box'][1:3]

        if not (upper_bounds and lower_bounds):
            logging.error(f"{file} == Candidate vote bounds not found!")
            sys.exit(0)
        votes: List[Line] = [line for line in lines if line['possible_vote']]

        (
            candidate_votes_total,
            other_votes_total
        ) = getVotesInCriticalSection(votes, upper_bounds,lower_bounds, declaration_bounds, x_filter_candidate_votes)
        image = getImage(file)
        len_candidate_votes_total = len(candidate_votes_total)
        len_other_votes_total = len(other_votes_total)
        final_votes: Dict[str, int] = InitCandidateVotes()
        final_stats: Dict[str, int] = initVotesStats()
        candidate_votes_sorted = sortVotesByY(candidate_votes_total)
        other_votes_sorted = sortVotesByY(other_votes_total)
        
        primary_votes = [int(i['text']) for i in candidate_votes_sorted]
        secondary_votes = [int(i['text']) for i in other_votes_sorted]
        total_individual = sumAllVotes(allIndividualVotesPresent(candidate_votes_sorted, reference_y + 100))

        votes_passed = True
        stats_passed = True
        checks = {
            "05": False,
            "04": False,
            "15": False,
            "14": False
            }
        if len(candidate_votes_sorted) == 5:
            final_votes = CandidatesVotes5(candidate_votes_sorted, final_votes)
            final_votes_check = individualEqualsTotal(final_votes)
            checks['05'] = not final_votes_check
        elif len(candidate_votes_sorted) == 4:
            final_votes, erronous_candidate = CandidateVotes4(candidate_lines, final_votes, candidate_votes_sorted, reference_y + 100)
            final_votes_check = individualEqualsTotal(final_votes)
            checks['04'] = not final_votes_check
        else:
            logging.warning(f"{file} == Votes Irrepairable!")
            votes_passed = False

        if len(other_votes_sorted) == 5:
            final_stats = OtherVotes5(other_votes_sorted, final_stats)
            checks['15'] = True
        elif len(other_votes_sorted) == 4:
            final_stats, erronous_stat = OtherVotes4(lines, lower_bounds, declaration_bounds, other_votes_sorted, final_stats)
            checks['14'] = True
        else:
            stats_passed = False
            logging.warning(f"{file} == Stats Irrepairable!")

        if checks['05']:
            final_votes = correctCandidatesTotal(final_votes, final_stats, total_individual)
        else:
            final_stats = correctStatsTotal(final_votes, final_stats, total_individual)

        if checks['04']:
            if checkTwoTotals(final_votes, final_stats):
                remaining = final_votes['total'] - total_individual
                key_to_correct = list(final_votes.keys())[erronous_candidate]
                final_votes[key_to_correct] = remaining 
            final_votes = correctCandidatesTotal(final_votes, final_stats, total_individual)
        else:
            final_stats = correctStatsTotal(final_votes, final_stats, total_individual)
        if checks['14']:
            if erronous_stat == 4:
                key_to_correct = list(final_stats.keys())[erronous_stat]
                final_stats[key_to_correct] = final_votes["total"]


        if votes_passed and stats_passed:
            print(f"{file.split('/')[-1][:-4].upper()} ==")
            print(final_votes)
            print(f"{ file.split('/')[-1][:-4].upper()} ==")
            print(final_stats)
            lines_within_bounds = getLinesWithinBounds(lines, lower_bounds[1], declaration_bounds[1])
            stat_lines = allStatsLines(lines_within_bounds)
            drawOnImage(image, candidate_lines)
            drawOnImage(image, stat_lines)
            drawOnImage(image, candidate_votes_sorted)
            drawOnImage(image, other_votes_sorted)
            cv2.imwrite(f"./py_outputs/{file.split('/')[-1][:-4]}.{image_extension}", image)
            print("Visualized image saved to ==> ./py_outputs/")
except FileNotFoundError:
    logging.error(f"Check if file path {file} is correct!")