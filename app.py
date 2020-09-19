from flask import Flask, render_template, url_for, request, redirect
import random

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        uploaded = request.files['imgUpload']
        if uploaded.filename != '':
            fileName = uploaded.filename.split(".")
            filePath = 'img/'+fileName[0]+str(random.random())+"."+fileName[1]
            uploaded.save('static/'+filePath)
        return render_template('uploaded.html', filePath=filePath)
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
