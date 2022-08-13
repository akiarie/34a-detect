package proc

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

type CandidateVotes struct {
	Odinga     int `json:"odinga"`
	Ruto       int `json:"ruto"`
	Waihiga    int `json:"waihiga"`
	Wajackoyah int `json:"wajackoyah"`
	total      int
}

func (cv CandidateVotes) String() string {
	return fmt.Sprintf(
		"{Odinga: %d, Ruto: %d, Waihiga: %d, Wajackoyah: %d, total: %d}",
		cv.Odinga, cv.Ruto, cv.Waihiga, cv.Wajackoyah, cv.total)
}

func (cv *CandidateVotes) sum() int {
	return cv.Odinga + cv.Ruto + cv.Waihiga + cv.Wajackoyah
}

func getLineContainingNames(lines []line) (*line, error) {
	names := []string{
		"ODINGA", "RAILA",
		"RUTO", "WILLIAM", "SAMOEI",
		"WAIHIGA", "DAVID", "MWAURE",
		"WAJACKOYAH", "GEORGE", "LUCHIRI",
	}
	for _, line := range lines {
		for _, n := range names {
			if strings.Contains(line.Text, n) {
				return &line, nil
			}
		}
	}
	return nil, fmt.Errorf("cannot find line containing candidate names")
}

const topMatchMin = 3

func tryfindbot(lines []line) *line {
	bottxt := "Polling Station Counts"
	bots := filterLines(lines, func(l line) bool {
		return stringHasSeqMin(l.Text, topMatchMin, bottxt)
	})
	bottxt2 := "Decisions disputed votes"
	bots2 := filterLines(lines, func(l line) bool {
		return stringHasSeqMin(l.Text, topMatchMin, bottxt2)
	})
	var finalbot *line
	for _, b := range [][]line{bots, bots2} {
		if len(b) >= 1 {
			finalbot = &b[0]
			break
		}
	}
	return finalbot
}

func getCandidateRegionBounds(lines []line) (*bounds, error) {
	toptxt := "Number votes cast favour each candidate"
	tops := filterLines(lines, func(l line) bool {
		return stringHasSeqMin(l.Text, topMatchMin, toptxt)
	})
	if len(tops) < 1 {
		return nil, fmt.Errorf("cannot find upper bound")
	}
	bot := tryfindbot(lines)
	if bot == nil {
		return nil, fmt.Errorf("cannot find lower bound")
	}
	return &bounds{tops[0].Box.topleft().y, bot.Box.topleft().y}, nil
}

func getCVTotal(results []int) (int, error) {
	switch len(results) {
	case 5:
		fmt.Println(results[4])
		return results[4], nil
	case 4:
		return -1, nil
	default:
		return 0, fmt.Errorf("invalid candidate vote length %d", len(results))
	}
}

func getCandidateVotes(lines []line) (*CandidateVotes, error) {
	bounds, err := getCandidateRegionBounds(lines)
	if err != nil {
		return nil, err
	}
	candLine, err := getLineContainingNames(lines)
	if err != nil {
		return nil, err
	}
	// filter for numeric values with greater x-coordinate
	flines := filterLines(lines, func(l line) bool {
		if _, err := strconv.Atoi(l.Text); err != nil {
			return false
		}
		tl := l.Box.topleft()
		return candLine.Box.topleft().x < tl.x &&
			bounds.top <= tl.y && tl.y <= bounds.bot
	})
	if len(flines) < 4 {
		return nil, fmt.Errorf("cannot find 4 closest numeric values")
	}
	sort.Slice(flines, func(i, j int) bool {
		return flines[i].Box.topleft().y < flines[j].Box.topleft().y
	})
	results, err := linesToPosInts(flines)
	if err != nil {
		panic(err)
	}
	tot, err := getCVTotal(results)
	if err != nil {
		return nil, err
	}
	return &CandidateVotes{
		Odinga:     results[0],
		Ruto:       results[1],
		Waihiga:    results[2],
		Wajackoyah: results[3],
		total:      tot,
	}, nil
}

func getCandidateVotes2(total int, lines []line) (*CandidateVotes, error) {
	bounds, err := getCandidateRegionBounds(lines)
	if err != nil {
		return nil, err
	}
	numericlines := filterLines(lines, func(l line) bool {
		if _, err := strconv.Atoi(l.Text); err != nil {
			return false
		}
		tl := l.Box.topleft()
		return bounds.top <= tl.y && tl.y <= bounds.bot
	})

	sort.Slice(numericlines, func(i, j int) bool {
		return numericlines[i].Box.topleft().y < numericlines[j].Box.topleft().y
	})
	top3lines := numericlines[:3]

	fmt.Println(top3lines)

	return nil, fmt.Errorf("NOT IMPLEMENTED")
}
