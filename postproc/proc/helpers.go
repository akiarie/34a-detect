package proc

import "strings"

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
