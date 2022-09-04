import re 
from helpers import Line 
from typing import Optional, List, Tuple
from helpers import getBounds

from pprint import pprint

stats_names = [
    "total number of registered voters in the polling station",
    "total number of rejected ballot papers",
    "total number of rejection objected to ballot papers",
    "total number of disputed votes",
    "total numer of valid votes cast"
]

candidate_names = [
		"ODINGA RAILA",
		"RUTO WILLIAM SAMOEI",
		"WAIHIGA DAVID MWAURE",
		"WAJACKOYAH GEORGE LUCHIRI",
]

def getLine(box: Optional[List[int]], text: str, possible: bool) -> Line:
	line = {
		"bounding_box": box, 
		"text" : text,
		"possible_vote" : possible
	}
	return line

def getLinesWithinBounds(
	lines: List[Line], 
	upper_top_y: int, 
	lower_top_y: int) -> List[Line]:
	line_within_bounds: List[Line] = []
	for line in lines:
		if (
			upper_top_y <
			line['bounding_box'][1] <
			lower_top_y
			) and (
				not line['text'].isdigit()
			) and re.sub('[^a-zA-Z\s]+', '', line['text']):
			line_within_bounds.append(line)
	return line_within_bounds

def getRequiredLines(
	lines_within_bounds: List[Line], 
	candidate_name: str,
	idx: int,
	min: int
	) -> Tuple[Optional[List[int]], int]:
	return_index = -1
	candidate_bounds: Optional[List[int]] = None
	for index, line in enumerate(lines_within_bounds[idx:]):
		bound = getBounds(candidate_name, line, min = min)
		if bound is not None:
			candidate_bounds = bound
			return_index = index + idx
			return candidate_bounds, return_index
	return candidate_bounds, return_index

def allCandidateLines(lines_within_bounds: List[Line], min: int = 2) -> List[Line]:
	search_index = 0
	candidate_lines: List[Line] = []
	for name in candidate_names:
		bound, i = getRequiredLines(
			lines_within_bounds, 
			name, 
			search_index,
			min)
		if i != -1:
			line = getLine(bound, name, False)
			candidate_lines.append(line)
			search_index = i
	return candidate_lines


def allStatsLines(lines_within_bounds: List[Line], min:int = 4):
	search_index = 0
	candidate_lines: List[Line] = []
	for name in stats_names:
		bound, i = getRequiredLines(
			lines_within_bounds, 
			name, 
			search_index,
			min)
		if i != -1:
			line = getLine(bound, name, False)
			candidate_lines.append(line)
			search_index = i
	return candidate_lines

def getNearestVote(
	candidate: Line, votes: List[Line]) -> Line:
	sorted_y = sorted(votes, key = lambda x: abs(
		candidate['bounding_box'][1] - x['bounding_box'][1]
		))
	return sorted_y[0]

def getNearestVotes(
	lines: List[Line], 
	votes: List[Line]):
	candidate_corresponding_vote:List[Tuple[Line, Line]] = []
	for line in lines:
		min_vote = getNearestVote(line, votes)
		candidate_corresponding_vote.append( 
			(line, min_vote)
		)
	return candidate_corresponding_vote

def getErroneousVote(
	candidates: List[Line], 
	votes: List[Line]
) -> Line:
	corresponding_vote = getNearestVotes(candidates, votes)
	erroneous_vote = sorted(
		corresponding_vote, 
		key = lambda x: abs(x[0]['bounding_box'][1] - x[1]['bounding_box'][1]),
		reverse = True)
	return erroneous_vote[0][0]

def allIndividualVotesPresent(votes: List[Line], threshold: int) -> List[Line]:
	filter_votes = lambda x: x['bounding_box'][1] < threshold
	filtered =  list(filter(filter_votes, votes))
	return filtered

def sumAllVotes(all_votes: List[Line]) -> int:
	return sum([int(i['text']) for i in all_votes])

