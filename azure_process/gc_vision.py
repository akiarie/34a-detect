import io
import itertools
import json
import os
import sys
from google.cloud import vision

def detect_document(path):
    """Detects document features in an image."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)

    lines = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:

                words = []
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    words += [word_text]

                vertices = [[v.x, v.y] for v in paragraph.bounding_box.vertices]
                lines += [{
                    "bounding_box": list(itertools.chain.from_iterable(vertices)),
                    "text": ' '.join(words),
                }]

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return lines


if len(sys.argv) != 2:
    sys.exit("must give input file path")

input_path = sys.argv[1]

if not os.path.exists(input_path):
    sys.exit("input file does not exist")

lines = detect_document(input_path)

print(json.dumps(lines))
