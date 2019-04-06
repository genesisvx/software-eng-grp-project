import functools 
import search_server
import json
from wtforms import Form, StringField, SelectField
from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for ,jsonify ,Response ,send_file
)
from search_server import searchDoc
from flask_cors import cross_origin

	
class Search(Form):
    search = StringField('')
	
bp = Blueprint('search', __name__,template_folder="templates",static_folder="static",static_url_path="/static")
	
@bp.route('/', methods=('GET','POST'))
def my_form():
    #search = Search(request.form)
    # if request.method == 'POST':
    #     return my_form_post(search)
    return render_template('index.html')

@bp.route('/results', methods=['POST','GET'])
def my_form_post(search):
        results = []
        search_string = request.form['search']
        print("search string is " + search_string)
        results = search_server.searchDoc(search_string)
        print(results)
        #return result
        return render_template('results.html', form = search , output=results)

@bp.route('/query' , methods = ['GET','POST'])
@cross_origin()
def query():
    query = request.json['query']
    results = search_server.searchDoc(query)
    print(results)
    response = Response(json.dumps(results),mimetype="application/json")
    return response

@bp.route('/getfile' , methods = ['GET','POST'])
@cross_origin()
def getfile():
    print('called')
    filepath = request.json
    print(filepath)
    #filepath=r'C:\Users\Acer\Desktop\Nottingham\Year 2\Group Project\NLP\software-eng-grp-project\test texts 2\Test2.pdf'
    return send_file(filepath , mimetype="application/pdf")