# -*- coding:utf-8 -*-
from flask import Flask,request,jsonify
import os
import json

app = Flask(__name__)

tasks = [
   {
        'done': True
    }
]

@app.route('/push',methods=['GET','POST'])
def push_api():
     if request.method == 'POST':
     	data = request.get_data()
     	data = json.loads(data)
     	image = data.get('image')
     	os.system("docker push {}".format(image))
     return jsonify({'tasks': tasks})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5678,debug=True)
