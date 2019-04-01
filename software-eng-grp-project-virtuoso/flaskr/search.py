import functools
import search_server

from wtforms import Form, StringField, SelectField
from flask import(
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from search_server import searchDoc

	
class Search(Form):
    search = StringField('')
	
bp = Blueprint('search', __name__, url_prefix='/search')
	
@bp.route('/', methods=('GET','POST'))
def my_form():
    search = Search(request.form)
    if request.method == 'POST':
        return my_form_post(search)
    return render_template('searchBar.js', form=search)

@bp.route('/', methods=['POST','GET'])
def my_form_post(search):
        results = []
        search_string = request.form['search']
        print("search string is " + search_string)
        results = search_server.searchDoc(search_string)
        print(results)
        #return result
        return render_template('App.js', form = search , output=results)