from typing import List, Dict 

def InitCandidateVotes() -> Dict[str, int]:
	return {
	"Odinga": 0,
	"Ruto": 0, 
	"Waihiga": 0,
	"Wajackoyah": 0,
	"total": 0
}

def fillCandidateVotes(
	primary_votes: List[int], 
	candidates: Dict[str, int]
	) -> Dict[str, int]:
	candidates["Odinga"] = primary_votes[0]
	candidates["Ruto"] = primary_votes[1]
	candidates["Waihiga"] = primary_votes[2]
	candidates["Wajackoyah"] = primary_votes[3]
	candidates["total"] = primary_votes[4]
	return candidates

def isCandidateVotesEqualsSum(candidate_votes: List[int], total: int) -> bool:
	return sum(candidate_votes) == total
