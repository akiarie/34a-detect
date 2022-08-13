package proc

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

type VoteStats struct {
	Registered       int `json:"registered"`
	Rejected         int `json:"rejected"`
	RejectedObjected int `json:"rejected_objected"`
	Disputed         int `json:"disputed"`
	ValidCast        int `json:"valid_cast"`
}

func (s *VoteStats) totalcast() int {
	return s.Rejected + s.RejectedObjected + s.Disputed + s.ValidCast
}

func getVoteStatsRegionBounds(lines []line) (*bounds, *line, error) {
	toptxt := "Polling Station Counts"
	tops := filterLines(lines, func(l line) bool {
		return stringHasSeqMin(l.Text, 3, toptxt)
	})
	if len(tops) < 1 {
		return nil, nil, fmt.Errorf("cannot find upper bound")
	}
	bots := filterLines(lines, func(l line) bool {
		return strings.Contains(l.Text, "Declaration")
	})
	if len(bots) != 1 {
		return nil, nil, fmt.Errorf("cannot find lower bound")
	}
	return &bounds{
		tops[0].Box.topleft().y,
		bots[0].Box.topleft().y,
	}, &tops[0], nil
}

func getVoteStats(cv *CandidateVotes, lines []line) (*VoteStats, error) {
	bounds, pscLine, err := getVoteStatsRegionBounds(lines)
	if err != nil {
		return nil, err
	}
	// filter for numeric values with greater x-coordinate
	flines := filterLines(lines, func(l line) bool {
		if _, err := strconv.Atoi(l.Text); err != nil {
			return false
		}
		tl := l.Box.topleft()
		return pscLine.Box.topright().x < tl.x &&
			bounds.top <= tl.y && tl.y <= bounds.bot
	})
	sort.Slice(flines, func(i, j int) bool {
		return flines[i].Box.topleft().x < flines[j].Box.topleft().x
	})
	if len(flines) > 5 {
		flines = flines[:5]
	}
	sort.Slice(flines, func(i, j int) bool {
		return flines[i].Box.topleft().y < flines[j].Box.topleft().y
	})
	results, err := linesToPosInts(flines)
	if err != nil {
		panic(err)
	}
	if len(results) < 5 {
		if cv.total == -1 || len(results) < 4 {
			return nil, fmt.Errorf("no possible total value")
		}
		results[4] = cv.total
	} else if cv.total != -1 {
		if cv.sum() != results[4] {
			results[4] = cv.total
		}
	}
	return &VoteStats{
		Registered:       results[0],
		Rejected:         results[1],
		RejectedObjected: results[2],
		Disputed:         results[3],
		ValidCast:        results[4],
	}, nil
}
