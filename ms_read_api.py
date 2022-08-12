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
    cv2.destroyAllWindows()
    
class ReadApi():
    def __init__(self, image_url = "./image_data/sample.jpg"):
        super(ReadApi, self).__init__()
        config = dotenv_values(".env")
        computervision_client = ComputerVisionClient(config['endpoint'], CognitiveServicesCredentials(config['subscription_key']))

        self.image_url = image_url
        self.computervision_client = computervision_client


    def process_image(self):
        with open(self.image_url, "rb") as image_stream:
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

    def visualize_results(self, image, read_result, result_image_name = "result", results = False):
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
        if results:
            return image
        else:
            print(result_image_name)
            cv2.imwrite(f"{result_image_name}.jpg", image)
            return None


if __name__ == "__main__":
    image_url = "./image_data/sample.jpg"
    image = read_image(image_url)
    readApi = ReadApi(image_url = image_url)
    read_result = readApi.process_image()
    image = readApi.visualize_results(image, read_result, results=True)
    show_image(image)
