ls ./py_txts | parallel python temp.py -f ./py_txts/{} -i ./py_images -e ".jpg"
