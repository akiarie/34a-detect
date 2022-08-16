from typing import Optional, Any, TypedDict

class Line(TypedDict):
	bounding_box: list[int]
	text: str
	possible_vote: bool

def stringHasSeqMin(s: str, word: str, min: int = 3) -> int:
	found = 0
	current_index = 0
	result = False
	search_words = s.split(" ")
	split_words = word.split(" ")
	for search_word in search_words:
		try:
			index = split_words.index(search_word)
			if index < current_index:
				return result
			found += 1
			current_index = index
			if found >= min:
				result = True
				return result
		except ValueError:
			index = -1
	return result

def getBounds(search_words: str, line: Line, min:int = 5) -> Optional[list[int]]:
	bound: Optional[list[int]] = None
	suffices = stringHasSeqMin(
	search_words.lower(), 
	(line['text']).lower(),
	min = min)
	if suffices:
		bound = [int(i) for i in line['bounding_box']]
	return bound

def TopLeftandBottomRight(bound: Line) -> \
		list[list[int]]:
	top_left = [int(i) for i in bound['bounding_box'][:2]]
	bottom_right = [int(i) for i in bound['bounding_box'][4:6]]
	return [top_left, bottom_right]

def sortVotesByY(votes: list[Line]) -> list[Line]:
	sorted_votes = sorted(votes, key=lambda x: x['bounding_box'][1])
	return sorted_votes

def getCandidateVotesTotal(
	votes: list[Line],
	upper_bounds: Any,
	lower_bounds: Any,
	x_filter_candidate_votes: int
	) -> list[Line]:
	upper_bottom_right_y = upper_bounds[5]
	lower_bottom_right_y = lower_bounds[5]
	votes_within_bounds: list[Line] = []
	for vote in votes:
		vote_top_left, vote_bottom_right = TopLeftandBottomRight(vote)
		if (
			upper_bottom_right_y <
			vote_bottom_right[1] <
			lower_bottom_right_y
		) and vote_top_left[0] > x_filter_candidate_votes:
			votes_within_bounds.append(vote)
	return votes_within_bounds


def getOtherVotesTotal(
	votes: list[Line],
	lower_bounds: Any,
	declaration_bounds: Any
	) -> list[Line]:
	lower_bottom_right_y = lower_bounds[5]
	declaration_bottom_right_x = declaration_bounds[4]
	declaration_bottom_right_y = declaration_bounds[5]
	votes_within_bounds: list[Line] = []
	for vote in votes:
		_, vote_bottom_right = TopLeftandBottomRight(vote)
		if (
			lower_bottom_right_y <
			vote_bottom_right[1] <
			declaration_bottom_right_y
		) and (
			declaration_bottom_right_x <
			vote_bottom_right[0] <
			lower_bounds[0]
			):
			votes_within_bounds.append(vote)
	return votes_within_bounds


if __name__ == "__main__":
	s =  "number votes cast favour each candidate"
	words = [
		"number of votes in favour of each candidate",
		"votes candidate",
		"candidate votes",
		"number of each votes candidate",
		"of votes of each candidate",
		"number favour candidate",
		"number votes cast favour each candidate"
	]
	for word in words:
		print(stringHasSeqMin(s, word, 3))