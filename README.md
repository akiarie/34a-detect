# 34a-detect
_Scripts for converting IEBC Form 34As into JSON._

Requirements:

```bash
pip3 install -r requirements.json
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
