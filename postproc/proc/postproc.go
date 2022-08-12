package proc

import (
	"encoding/json"
	"fmt"
)

type bounds struct {
	top, bot float64
}

type form34A struct {
	Candidates *CandidateVotes `json:"candidate_votes"`
	Statistics *VoteStats      `json:"statistics"`
}

func (f *form34A) verify() bool {
	return f.Candidates.sum() == f.Statistics.ValidCast &&
		f.Statistics.totalcast() < f.Statistics.Registered
}

func Parse34A(result []byte) (*form34A, error) {
	var lines []line
	if err := json.Unmarshal(result, &lines); err != nil {
		return nil, fmt.Errorf("marshal error: %s", err)
	}
	cv, err := getCandidateVotes(lines)
	if err != nil {
		return nil, fmt.Errorf("cannot get candidate votes: %s", err)
	}
	stats, err := getVoteStats(cv, lines)
	if err != nil {
		return nil, fmt.Errorf("cannot get vote stats: %s", err)
	}
	f := &form34A{cv, stats}
	if !f.verify() {
		return nil, fmt.Errorf("form not verified")
	}
	return f, nil

}
