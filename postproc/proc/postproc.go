package proc

import (
	"encoding/json"
	"fmt"
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
	Box  *boundingbox `json:"bounding_box"`
	Text string       `json:"text"`
}

type CandidateVotes struct {
	Odinga     int `json:"odinga"`
	Ruto       int `json:"ruto"`
	Waihiga    int `json:"waihiga"`
	Wajackoyah int `json:"wajackoyah"`
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

func getCandidateVotes(lines []line) (*CandidateVotes, error) {
	candidateLine, err := getLineContainingNames(lines)
	if err != nil {
		return nil, err
	}
	fmt.Println(candidateLine)
	return nil, fmt.Errorf("NOT IMPLEMENTED")
}

type form34A struct {
	Candidates CandidateVotes `json:"candidate_votes"`
	Statistics struct {
		Registered       int `json:"registered"`
		Rejected         int `json:"rejected"`
		RejectedObjected int `json:"rejected_objected"`
		Disputed         int `json:"disputed"`
		ValidCast        int `json:"valid_cast"`
	} `json:"statistics"`
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
	fmt.Println(cv)
	return nil, fmt.Errorf("NOT IMPLEMENTED")
}
