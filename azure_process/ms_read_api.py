import cv2 
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import time
from tqdm import tqdm
from dotenv import dotenv_values

def read_image(image_path, resize = False):
    image = cv2.imread(image_path, 3)
    if resize:
        image = cv2.resize(image, (3400, 4900))
    return image 

def show_image(image, title="image"):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    
class ReadApi():
    def __init__(self, image_path):
        super(ReadApi, self).__init__()
        config = dotenv_values(".env")
        computervision_client = ComputerVisionClient(
            config['ENDPOINT'], 
            CognitiveServicesCredentials(config['SUBSCRIPTION_KEY'])
        )

        self.image_path = image_path
        self.computervision_client = computervision_client

    def process_image(self):
        with open(self.image_path, "rb") as image_stream:
            read_response = self.computervision_client.read_in_stream(
                image=image_stream,
                mode="Printed",
                raw=True
            )
        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]
        while True:
            read_result = self.computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)
        return read_result

    def visualize_results(self, read_result, result_image_name = "result"):
        image = read_image(self.image_path)
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in tqdm(text_result.lines):
                    top_left = [int(i) for i in line.bounding_box[:2]]
                    bottom_right = [int(i) for i in line.bounding_box[4:6]]
                    color = (0, 0, 255)
                    thickness = 5
                    image = cv2.rectangle(image, top_left, bottom_right, color, thickness)
                    image = cv2.putText(image, line.text, (top_left[0], top_left[1]), cv2.FONT_HERSHEY_SIMPLEX, 
                        2, (255,0,0), 2, cv2.LINE_AA)

            cv2.imwrite(f"{result_image_name}", image)
