from typing import List, Dict 

def initVotesStats() -> Dict[str, int]:
    return {
        "registered": 0,
        "rejected": 0,
        "rejectedObjected": 0, 
        "disputed": 0,
        "validcast": 0,
    }

def fillVotesStats(
    results: List[int],
    stats: Dict[str, int]) -> Dict[str, int]:
    stats["registered"] = results[0]
    stats["rejected"] = results[1]
    stats["rejectedObjected"] = results[2]
    stats["disputed"] = results[3]
    stats["validcast"] = results[4]
    return stats

def assignToRegistered() -> int:
    return 5

