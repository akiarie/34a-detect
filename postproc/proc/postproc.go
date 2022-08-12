package proc

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"
	"strconv"
	"strings"
)

type point struct {
	x, y float64
}

type boundingbox []float64

func (b *boundingbox) UnmarshalJSON(buf []byte) error {
	var arr []float64
	if err := json.Unmarshal(buf, &arr); err != nil {
		return err
	}
	if len(arr) != 8 {
		panic(fmt.Sprintf("invalid length bounding box %d", len(arr)))
	}
	*b = boundingbox(arr)
	return nil
}

func (b boundingbox) topleft() *point  { return &point{b[0], b[1]} }
func (b boundingbox) topright() *point { return &point{b[2], b[3]} }
func (b boundingbox) botright() *point { return &point{b[4], b[5]} }
func (b boundingbox) botleft() *point  { return &point{b[6], b[7]} }

type line struct {
	Box  boundingbox `json:"bounding_box"`
	Text string      `json:"text"`
}

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

func filterLines(lines []line, key func(line) bool) []line {
	sieved := []line{}
	for _, l := range lines {
		if key(l) {
			sieved = append(sieved, l)
		}
	}
	return sieved
}

func distXBR(l1, l2 *line) float64 {
	return math.Abs(l1.Box.botright().x - l2.Box.botright().x)
}

func distYBR(l1, l2 *line) float64 {
	return math.Abs(l1.Box.botright().y - l2.Box.botright().y)
}

func linesToPosInts(lines []line) ([]int, error) {
	abs := func(n int) int {
		if n > 0 {
			return n
		}
		return -n
	}
	results := make([]int, len(lines))
	for i, l := range lines[:len(lines)] {
		n, err := strconv.Atoi(l.Text)
		if err != nil {
			return nil, fmt.Errorf("cannot parse number %q", l.Text)
		}
		results[i] = abs(n)
	}
	return results, nil
}

// stringHasSeqMin: returns a value indicating whether s contains at least min
// of the provided words in whole in sequence
func stringHasSeqMin(s string, min int, whole string) bool {
	var last, found int
	seq := strings.Split(whole, " ")
	for _, elem := range seq {
		if i := strings.Index(s[last:], elem); i != -1 {
			found++
			last += i + len(elem)
		}
		if found >= min {
			return true
		}
	}
	return found >= min
}

type bounds struct {
	top, bot float64
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
	cv := &CandidateVotes{
		Odinga:     results[0],
		Ruto:       results[1],
		Waihiga:    results[2],
		Wajackoyah: results[3],
	}
	if len(results) == 5 {
		cv.total = results[4]
	} else {
		cv.total = -1
	}
	return cv, nil
}

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
	// here:
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
