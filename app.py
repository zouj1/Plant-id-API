import random
import base64
import requests
import wikipedia
import re

from flask import Flask, render_template, url_for, request, redirect

app = Flask(__name__)


def identify(img_path, thresh=0.6):
    # jasmine's api key: only used 3 id
    your_api_key = "E66BiKTPRCUdCczIgRzOBhg8U6NKjymYrM288lFmzCMKxl8Nx7"

    '''img_path(str): path to image to be identified
        thresh(float): probability for which we are confident enought in our classification
        RETURNS: dictionary of info if thresh is met, str saying try again if not'''
    with open(img_path, "rb") as file:
        images = [base64.b64encode(file.read()).decode("ascii")]

    json_data = {
        "images": images,
        "modifiers": ["similar_images"],
        "plant_details": ["common_names", "url"]
    }

    response = requests.post(
        "https://api.plant.id/v2/identify",
        json=json_data,
        headers={
            "Content-Type": "application/json",
            "Api-Key": your_api_key
        }).json()

    if response['suggestions'][0]['probability'] < thresh:
        return 'We are having difficulty classifying your image. Please try a different picture!'

    return response


def scrape(name, filtered_sections=False):
    ''' name (str): name of plant
        filtered_sections: False if you want info from all sections, or list of strings if you only want some info
        RETURNS: dict of '''
    top_wiki = wikipedia.search(name)[0]
    all_content = wikipedia.page(top_wiki).content
    section_split = re.split(
        '\n\n\n== ' + '([a-zA-Z0-9\s]*)' + ' ==\n', all_content)

    content_dict = {'Summary': section_split[0]}
    for i in range(len(section_split)):
        if i % 2 == 1:
            content_dict[section_split[i]] = section_split[i+1]

    if filtered_sections == False:
        return content_dict
    else:
        filtered = {}
        for section in filtered_sections:
            try:
                filtered[section] = content_dict[section]
            except KeyError:
                print('the section: ' + section +
                      ' does not exist for ' + name)

        return filtered

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        uploaded = request.files['imgUpload']
        if uploaded.filename != '':
            fileName = uploaded.filename.split(".")
            filePath = 'img/'+fileName[0]+str(random.random())+"."+fileName[1]
            uploaded.save('static/'+filePath)

            info = identify('static/'+filePath)
            if isinstance(info, dict):
                name = info['suggestions'][0]['plant_name']
                common_names = info['suggestions'][0]["plant_details"]["common_names"][0]
                url = info['suggestions'][0]["plant_details"]["url"]
                fact = "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book."
                # scrape(name)
                return render_template('uploaded.html', filePath=filePath, name=name, commonName=common_names, url=url, fact=fact)
            elif isinstance(info, str):
                print(info)
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)