# https://pyimagesearch.com/2020/05/25/tesseract-ocr-text-localization-and-detection/
from pytesseract import Output
import pytesseract
import cv2

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
    "disputes": {
        "left": [],
        "right": []
    },
}

def permit(s, nextst):
    def _permit(result):
        if result["text"] == s:
            return nextst, True
        return nextst(result)

def st_right_title(result):
    if result["text"] == "STATION":
        coords["title"]["right"] += [result]
        return st_candidates, True

    if result["text"] == "POLLING":
        coords["title"]["right"] += [result]
        return permit("STATION", st_candidates), True

    return st_right_title, False

def st_title(result):
    if result["text"] == "ELECTION":
        coords["title"]["left"] += [result]
        return st_right_title, True

    if result["text"] == "PRESIDENTIAL":
        coords["title"]["left"] += [result]
        return permit("ELECTION", st_right_title), True

    return st_title, False

def st_george(result):
    if result["text"] == "GEORGE":
        coords["candidates"] += [result]
        return st_stats, True
    return st_george, False

def st_candidates(result):
    if result["text"] == "WILLIAM":
        coords["candidates"] += [result]
        return permit("DAVID", st_george), True

    if result["text"] == "DAVID":
        coords["candidates"] += [result]
        return st_george, True

    return st_candidates, False


def st_disputes(result):
    if result["text"] == "Decision":
        coords["dispute"] += [result]
        return permit("disputed", None), True

    if result["text"] == "disputed":
        coords["dispute"] += [result]
        return None, True

    return st_disputes, False

def st_stats(result):
    if result["text"] == "Polling":
        coords["stats"] += [result]
        return permit("Station", st_disputes), True

    if result["text"] == "Station":
        coords["stats"] += [result]
        return st_disputes, True

    return st_stats, False

state = st_title

def draw(image, x, y, w, h):
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)


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

    nextst, should_draw = state(result)
    if should_draw:
        x, y = result["coords"]["x"], result["coords"]["y"]
        w, h = result["dimensions"]["w"], result["dimensions"]["h"]
        draw(image, x, y, w, h)

    state = nextst

    if state is None:
        break

if state is not None:
    raise

# show the output image
cv2.imshow("Image", image)
cv2.waitKey(0)
