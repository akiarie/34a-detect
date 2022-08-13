package proc

import (
	"encoding/json"
	"fmt"
	"math"
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

func (l *line) containsAny(ss []string) bool {
	for _, s := range ss {
		if strings.Contains(l.Text, s) {
			return true
		}
	}
	return false
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

func abs(n int) int {
	if n > 0 {
		return n
	}
	return -n
}

func linesToPosInts(lines []line) ([]int, error) {
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
