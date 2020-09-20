import random
import base64
import requests
import wikipedia
import re
from textblob import TextBlob
from nltk.tokenize import sent_tokenize

from flask import Flask, render_template, url_for, request, redirect

app = Flask(__name__)


def identify(img_path, thresh=0.3):
    # jasmine's api key: only used 3 id
    your_api_key = "rLGVjfad2327BNuznXIHsIttJzt1GEzqQpvU1cKoieAoUrkp7Q"

    '''img_path(str): path to image to be identified
        thresh(float): probability for which we are confident enought in our classification
        RETURNS: dictionary of info if thresh is met, str saying try again if not'''
    with open(img_path, "rb") as file:
        images = [base64.b64encode(file.read()).decode("ascii")]
    
    print("found image")
    
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

def rank_sentences(text_dict, top=5):
    '''
    text_dict(dict): a dictionary mapping different sections to some text. use the output from the scrape
                     function as an argument
    top(int): total number of sentences that will be returned by this function. Default is 5.

    Summary of the algorithm: Stitch all the text together and break them down into sentences.
    For each sentence, give a sentiment score. Take some number of sentences(specified by top)
    with the highest sentiment score(i.e. more positive sentiment) and return the cleaned version of them.
    '''

    all_text = ' '.join(text_dict[key] for key in text_dict)
    sentences = sent_tokenize(all_text)
    all_text = [(sent, TextBlob(sent).polarity) for sent in sentences]
    all_text_forward = sorted(all_text, key = lambda x: x[1], reverse=True)[:top]

    return [(clean_text(text), score) for text,score in all_text_forward]

def clean_text(text):
    '''clean up the ===title=== part of the text'''
    text = re.sub('e\.g\.', '', text)
    return re.sub(r'(=)+([a-zA-Z0-9\s]*)(=)+', '', text).strip()

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
                text_dict = scrape(name)
                top_sentences = rank_sentences(text_dict, top=2)
                
                nameSplit = common_names.split(" ")
                amazonQuery = "https://www.amazon.com/s?k="
                for word in nameSplit:
                    amazonQuery += word + "+"
                amazonQuery += "seeds+for+planting"
                # scrape(name)
                return render_template('uploaded.html', filePath=filePath, name=name, commonName=common_names, url=url, fact=top_sentences, amazon=amazonQuery)
            elif isinstance(info, str):
                return render_template('lowconf.html', filePath=filePath)
        else:
            return 
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
