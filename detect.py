# https://pyimagesearch.com/2020/05/25/tesseract-ocr-text-localization-and-detection/
from pytesseract import Output
import pytesseract
import cv2

import math

MIN_CONF = 0

image = cv2.imread("gatundu-south.png")
rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
results = pytesseract.image_to_data(rgb, output_type=Output.DICT)


coords = {
    "title": {
        "left": [],
        "right": [],
    },
    "candidates": [],
    "stats": {
        "left": [],
        "right": []
    },
}

def dist(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def slope(x1, y1, x2, y2):
    if x1 == x2:
        raise Exception("infinite slope")
    return (y2-y1)/(x2-x1)

def getcoords(result):
    return result["coords"]["x"], result["coords"]["y"]

def get_page_slope():
    tl0_x, tl0_y = getcoords(coords["title"]["left"][0])
    tr0_x, tr0_y = getcoords(coords["title"]["right"][0])
    m_title = slope(tl0_x, tl0_y, tr0_x, tr0_y)

    sl0_x, sl0_y = getcoords(coords["stats"]["left"][0])
    sr0_x, sr0_y = getcoords(coords["stats"]["right"][0])
    m_stats = slope(sl0_x, sl0_y, sr0_x, sr0_y)

    return (m_title + m_stats) / 2

distances = {
    "PRESIDENTIAL_Decision": 11.7,
    "PRESIDENTIAL_dispute": 12.8,

    "ELECTION_Decision": 10.3,
    "ELECTION_dispute": 11.0,

    "Polling_POLLING": 15.0,
    "Polling_STATION": 16.5,

    "Station_POLLING": 14.2,
    "Station_STATION": 14.8,

    "WILLIAM_mid": 12.3,
    "DAVID_mid": 11.8,
    "GEORGE_mid": 11.1,

    "Polling_mid": 6.95,
    "Station_mid": 5.9,
    "mid_Decision": 2.2,
    "mid_dispute": 4.3,

    "Vote_Width": 4.0,
    "Stats_Width": 1.9,
    "SV_Height_Ratio": 1.3/1.5,
}

def get_scale():
    estimates = []
    # top left to bottom right
    for tl in coords["title"]["left"]:
        for br in coords["stats"]["right"]:
            tl_x, tl_y = getcoords(tl)
            br_x, br_y = getcoords(br)
            delta = dist(tl_x, tl_y, br_x, br_y)
            tln, brn = tl["text"], br["text"] 
            measured = distances[f"{tln}_{brn}"]
            estimates += [delta/measured]

    # bottom left to top right
    for bl in coords["stats"]["left"]:
        for tr in coords["title"]["right"]:
            bl_x, bl_y = getcoords(bl)
            tr_x, tr_y = getcoords(tr)
            delta = dist(bl_x, bl_y, tr_x, tr_y)
            bln, trn = bl["text"], tr["text"] 
            measured = distances[f"{bln}_{trn}"]
            estimates += [delta/measured]

    return sum(estimates)/len(estimates)


def get_stat_boxes(height):
    scale = get_scale()
    m = get_page_slope()

    y_est = []
    x_est = []

    for left in coords["stats"]["left"]:
        x, y = getcoords(left)
        name = left["text"]
        delta = distances[f"{name}_mid"]*scale
        x_est += [x + delta]
        y_est += [y + (delta * m)]

    for right in coords["stats"]["right"]:
        x, cy = getcoords(right)
        name = right["text"]
        delta = distances[f"mid_{name}"]*scale
        x_est += [x - delta]
        y_est += [y - (delta * m)]


    w = int(distances["Stats_Width"]*scale)
    x = int(sum(x_est) / len(x_est))
    y = int((sum(y_est) / len(y_est))-0.05*scale)
    h = int(height*distances["SV_Height_Ratio"])

    boxes = {}
    field_heights = {
        "registered": y + h,
        "rejected": y + 2*h,
        "rejobj": y + 3*h,
        "disputed": y + 4*h,
        "cast": y + 5*h,
    }
    h_adj = int(h+0.1*scale)
    for field in field_heights:
        boxes[field] = (x, field_heights[field], w, h_adj)

    boxes["stats"] = (x, field_heights["registered"], w, int(h*5+0.1*scale))

    return boxes

def get_vote_boxes():
    scale = get_scale()
    m = get_page_slope()

    x_est = []
    h_est = []

    y = 0

    for cand in coords["candidates"]:
        h_est += [cand["dimensions"]["h"]]
        cx, cy = getcoords(cand)
        name = cand["text"]
        delta = distances[f"{name}_mid"]*scale
        x_est += [cx + delta]
        y = int(cy + (delta * m) - 0.05*scale)

    w = int(distances["Vote_Width"]*scale)
    x = int(sum(x_est) / len(x_est))
    h = int((sum(h_est) / len(h_est)))

    boxes = {}
    cand_heights = {
        "raila": y - 3*h,
        "ruto": y - 2*h,
        "mwaure": y - h,
        "wajackoyah": y,
    }
    h_adj = int(h+0.1*scale)
    for cand in cand_heights:
        boxes[cand] = (x, cand_heights[cand], w, h_adj) 

    boxes["votes"] = (x, cand_heights["raila"], w, int(h*4+0.1*scale))

    return boxes, h



def surreq(reqfunc, st):
    def _state(result):
        if not reqfunc(result):
            return _state, False
        return st(result)
    return _state


def blockreq(levels):
    def _blockreq(result):
        l = result["levels"]
        for s in ["block", "par", "line"]:
            if levels[s] != result["levels"][s]:
                return False
        return True
    return _blockreq


def permit(s, nextst):
    def _permit(result):
        if result["text"].startswith(s):
            result["text"] = s
            return nextst, True
        nextst2, should_draw = nextst(result)
        if should_draw:
            return nextst2, True
        return _permit, False
    return _permit

def st_right_title(result):
    if result["text"].startswith("POLLING"):
        result["text"] = "POLLING"
        coords["title"]["right"] += [result]
        return surreq(blockreq(result["levels"]), permit("STATION", st_candidates)), True

    if result["text"].startswith("STATION"):
        result["text"] = "STATION"
        coords["title"]["right"] += [result]
        return st_candidates, True

    return st_right_title, False

def st_title(result):
    if result["text"].startswith("PRESIDENTIAL"):
        result["text"] = "PRESIDENTIAL"
        coords["title"]["left"] += [result]
        return surreq(blockreq(result["levels"]), permit("ELECTION", st_right_title)), True

    if result["text"].startswith("ELECTION"):
        result["text"] = "ELECTION"
        coords["title"]["left"] += [result]
        return surreq(blockreq(result["levels"]), st_right_title), True

    return st_title, False

def st_george(result):
    if result["text"].startswith("GEORGE"):
        result["text"] = "GEORGE"
        coords["candidates"] += [result]
        return st_stats, True
    return st_george, False

def st_candidates(result):
    l = result["levels"]
    nl = {"block": l["block"], "par": l["par"], "line": l["line"] + 1}

    if result["text"].startswith("WILLIAM"):
        result["text"] = "WILLIAM"
        coords["candidates"] += [result]
        return surreq(blockreq(nl), permit("DAVID", st_george)), True

    if result["text"].startswith("DAVID"):
        result["text"] = "DAVID"
        coords["candidates"] += [result]
        return surreq(blockreq(nl), st_george), True

    return st_candidates, False

def st_votes(result):
    for s in ["votes", "if", "any"]:
        if result["text"].startswith(s):
            return None, False # no printing at the end
    return st_votes, False

def st_disputes(result):
    if result["text"].startswith("Decision"):
        result["text"] = "Decision"
        coords["stats"]["right"] += [result]
        return surreq(blockreq(result["levels"]), permit("dispute", st_votes)), True

    if result["text"].startswith("dispute"):
        result["text"] = "dispute"
        coords["stats"]["right"] += [result]
        return surreq(blockreq(result["levels"]), st_votes), True

    return st_disputes, False

def st_stats(result):
    if result["text"].startswith("Polling"):
        result["text"] = "Polling"
        coords["stats"]["left"] += [result]
        return surreq(blockreq(result["levels"]), permit("Station", st_disputes)), True

    if result["text"].startswith("Station"):
        result["text"] = "Station"
        coords["stats"]["left"] += [result]
        return surreq(blockreq(result["levels"]), st_disputes), True

    return st_stats, False




def draw(image, x, y, w, h, txt):
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(image, txt, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)


state = st_title

# loop over each of the individual text localizations
for i in range(0, len(results["text"])):
    conf = float(results["conf"][i])

    if conf <= MIN_CONF:
        continue

    text = "".join([c if ord(c) < 128 else "" for c in results["text"][i]]).strip()

    result = {
        "coords": {
            "x": results["left"][i],
            "y": results["top"][i],
        },
        "dimensions": {
            "w": results["width"][i],
            "h": results["height"][i],
        },
        "levels": {
            "block": results["block_num"][i],
            "par":   results["par_num"][i],
            "line":  results["line_num"][i],
        },
        "text": text,
        "conf": conf,
    }

    state, should_draw = state(result)
    if should_draw:
        x, y = result["coords"]["x"], result["coords"]["y"]
        w, h = result["dimensions"]["w"], result["dimensions"]["h"]
        l = result["levels"]
        text = result["text"]
        print(f"{text} — {conf} at ({x}, {y}) dim ({w}, {h}) on {l}")
        draw(image, x, y, w, h, text)

    if state is None:
        break

if state is not None:
    raise Exception(f"unable to conclude state {state}")

vote_boxes, height = get_vote_boxes()

for box_name in vote_boxes:
    (x, y, w, h) = vote_boxes[box_name]
    crop_img = image[y:y+h, x:x+w]
    cv2.imwrite(f"votes-{box_name}.png", crop_img)

stat_boxes = get_stat_boxes(height)

for box_name in stat_boxes:
    (x, y, w, h) = stat_boxes[box_name]
    crop_img = image[y:y+h, x:x+w]
    cv2.imwrite(f"stats-{box_name}.png", crop_img)
