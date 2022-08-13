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
	Confidence float64         `json:"confidence"`
}

func (f *form34A) verify() bool {
	return f.Candidates.sum() == f.Statistics.ValidCast &&
		f.Statistics.totalcast() < f.Statistics.Registered
}

func (f *form34A) verifyAndTryFix(lines []line) error {
	if f.verify() {
		return nil
	}
	return fmt.Errorf("form not verified: %v, %v", *f.Candidates, *f.Statistics)
	// Wajackoyah holds the final value
	if f.Statistics.ValidCast == f.Candidates.Wajackoyah {
		// second pass
		cv, err := getCandidateVotes2(f.Statistics.ValidCast, lines)
		if err != nil {
			return fmt.Errorf("cannot get candidate votes: %s", err)
		}
		// TODO: update confidence
		f.Candidates = cv
		if f.verify() {
			return nil
		}
	}
	return fmt.Errorf("form not verified")
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
	f := &form34A{cv, stats, 1.0}
	if err := f.verifyAndTryFix(lines); err != nil {
		return nil, fmt.Errorf("cannot build form: %s", err)
	}
	return f, nil
}
