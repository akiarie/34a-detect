### Azure AI[^1] System for Analysis of Form34As 
 _Scripts for converting IEBC Form 34As into JSON_

#### Developed by :
##### Amisi Kiarie [![linkedin](https://img.shields.io/badge/LinkedIn-166FC5?style=border-radius:3px&logo=LinkedIn&logoColor=white)](https://www.linkedin.com/in/akiarie/) [![github](https://img.shields.io/badge/GitHub-000000?style=border-radius:3px&logo=GitHub&logoColor=white)](https://github.com/akiarie/) 
##### Marvin Mboya [![linkedin](https://img.shields.io/badge/LinkedIn-166FC5?style=border-radius:3px&logo=LinkedIn&logoColor=white)](https://www.linkedin.com/in/marvin-mboya-b7bb81195/) [![github](https://img.shields.io/badge/GitHub-000000?style=border-radius:3px&logo=GitHub&logoColor=white)](https://github.com/Marvin-desmond) 

![frameworkflowchart](https://i.imgur.com/SDgIhqh.png)

#### Project Structure :
![ProjectStructure](https://i.imgur.com/s7LbWSo.png)

__*Run processing on sample of the inputs :*__

1. Python scripts

Requirements:

```bash
pip3 install -r requirements.txt
```

Include your Azure credentials in an .env file:
```bash
ENDPOINT=         # Azure instance endpoint
SUBSCRIPTION_KEY= # Azure subcription key
```

Then run the pre-processor as follows:
```bash
python3 azure_process.py [input image] [output image]
```
You should get a JSON array of the lines with their bounding boxes and text.

#### OR 

```bash
cd pyproc/
```
_Input images to Azure Read API, pipe output streams to ./py_txts folder_
```bash
ls py_images | sed 's/jpg//g' | parallel python dumps.py -i ./py_images/{}jpg '>./py_txts/{}txt'
```
_Piped text streams to candidate votes and statistics and image mappings_
```bash
ls ./py_txts | parallel python temp.py -f ./py_txts/{} -i ./py_images -e "jpg"

```
_**Key takeaways from building this system :**_
+ _Practical usage of Azure Cognitive Service API. And I can say it's really good! Considering some images were blurry._
+ _Implementing system without regards to language bounds. Hence focus more on logic to accomplish a modularized task._
+ _As much as Azure API was good, this system required a more specific model, pretrained on separate Form34As from earlier years to achieve optimal solution, and to generalize on diverse Form34A images._
+ _There were a lot of edge cases i.e. geometric constraints were becoming too specific_

_**Improvements :**_
+ _Cropping of background from images of Form34As_
+ _Adjustment of orientation of images to be more front facing_
+ _Denoising of images_
+ _Second stage inference of irrepairable images (from Azure API system) to Google Cloud API_
+ _Recursive process of critical sections of image to AI APIs_
+ _Ensemble processing of Azure Cognitive Service Read API and Google Cloud API_
+ _Full software development cycle, from labeling of significant subset of Form34A images to transfer learning using a SOTA (State-of-the-art) pretrained transformer model_

[^1]: [Azure Cognitive Services Read API](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/quickstarts-sdk/client-library?tabs=visual-studio&pivots=programming-language-python)
