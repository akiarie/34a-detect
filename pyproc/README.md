__*Run processing on sample of the inputs :*__

1. Python scripts

+ Ensure GNU Parallel is installed
+ Ensure argparse installed 
```bash
pip3 install argparse
```
+ _Input images to Azure Read API, pipe output streams to ./py_txts folder_
```bash
ls py_images | sed 's/jpg//g' | parallel python3 dumps.py -i ./py_images/{}jpg '>./py_txts/{}txt'
```
+ _Piped text streams to candidate votes and statistics and image mappings_
```bash
ls ./py_txts | parallel python3 temp.py -f ./py_txts/{} -i ./py_images -e "jpg"
```
