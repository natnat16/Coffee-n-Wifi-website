from flask import Flask, render_template, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, BooleanField, DecimalField
from wtforms.validators import DataRequired, URL, Optional
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ah'


#Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=True)
    map_url = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(50), nullable=False)
    coffee_price = db.Column(db.String(50), nullable=False)  # string £0.00
    has_sockets = db.Column(db.Boolean)
    has_toilet = db.Column(db.Boolean)
    has_wifi = db.Column(db.Boolean)
    can_take_calls = db.Column(db.Boolean)

# Create forms
class CafeForm(FlaskForm):
    name = StringField(label='Cafe Name', validators=[DataRequired()])
    location = StringField(label='Cafe Location', validators=[DataRequired()])
    img_url = URLField(label='Image URL', validators=[Optional(), URL()])
    map_url = URLField(label='Map URL', validators=[DataRequired(), URL()])
    seats = StringField(label='No. of Seats', validators=[DataRequired()])
    coffee_price = DecimalField(label='Coffee Price in £', number_format='%.2f', validators=[DataRequired()])
    has_sockets = BooleanField(label='Sockets')
    has_toilet = BooleanField(label='Toilet')
    has_wifi = BooleanField(label='Wifi')
    can_take_calls = BooleanField(label='Calls')
    submit = SubmitField('Add')

class SearchCafeForm(FlaskForm):
    name = StringField(label='Cafe Name')
    location = StringField(label='Cafe Location')
    has_sockets = BooleanField(label='Sockets')
    has_toilet = BooleanField(label='Toilet')
    has_wifi = BooleanField(label='Wifi')
    can_take_calls = BooleanField(label='Calls')
    submit = SubmitField('Search')

filters = []

@app.route("/")
def home():
    year = datetime.now().year
    return render_template('index.html', year=year)

@app.route("/cafes/")
def show_cafes():
    year = datetime.now().year
    cafes = db.session.query(Cafe).all()
    return render_template('cafes.html', cafes=cafes, year=year)

# no API key or wrong API key entered
@app.errorhandler(400)
def api_key_required(error):
    return render_template('400.html' , err=error), 400

def check_api(api_key):
    if api_key != app.config['SECRET_KEY']:
        abort(400)

## add, update & delete pages will need API key -> /?api_key=
@app.route("/cafes/add/", methods=['GET','POST'])
def add_cafe():
    api_key = request.args.get('api_key')
    if request.method == 'GET':
        check_api(api_key)
    year = datetime.now().year
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
                    name = form.name.data.title(),
                    location = form.location.data.title(),
                    img_url = form.img_url.data,
                    map_url = form.map_url.data,
                    seats = form.seats.data,
                    coffee_price = f'£{form.coffee_price.data:.2f}',
                    has_sockets = form.has_sockets.data,
                    has_toilet = form.has_toilet.data,
                    has_wifi = form.has_wifi.data,
                    can_take_calls = form.can_take_calls.data
                    )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('show_cafes', _anchor=new_cafe.id))
    return render_template('form.html', form=form, year=year, is_add=True)


@app.route("/cafes/search/update/", methods=['GET','POST'])
@app.route("/cafes/update/", methods=['GET','POST'])
def update_cafe():
    api_key = request.args.get('api_key')
    if request.method == 'GET':
        check_api(api_key)

    year = datetime.now().year
    cafe_id = request.args.get('id')
    is_closed = request.args.get('cafe_closed')

    # Delete Cafe
    if is_closed is not None:
        cafe_to_delete = Cafe.query.get(cafe_id)
        db.session.delete(cafe_to_delete)
        db.session.commit()
        return redirect(url_for('update_cafe', api_key=api_key))

    # Update cafe info
    elif cafe_id:
        cafe_info = Cafe.query.get(cafe_id)
        edit_cafe_info = CafeForm(
                    name = cafe_info.name,
                    location = cafe_info.location,
                    img_url = cafe_info.img_url,
                    map_url = cafe_info.map_url,
                    seats = cafe_info.seats,
                    coffee_price = float(cafe_info.coffee_price.strip('£')),
                    has_sockets = cafe_info.has_sockets,
                    has_toilet = cafe_info.has_toilet,
                    has_wifi = cafe_info.has_wifi,
                    can_take_calls = cafe_info.can_take_calls
                    )
        edit_cafe_info.submit.label.text = 'Update'
        if request.method == 'GET':
            return render_template('form.html', form=edit_cafe_info, year=year, cafe_id=cafe_info.id, is_update=True, key=api_key)

        if  edit_cafe_info.validate_on_submit():
            cafe_info.name = edit_cafe_info.name.data
            cafe_info.location = edit_cafe_info.location.data
            cafe_info.img_url = edit_cafe_info.img_url.data
            cafe_info.map_url = edit_cafe_info.map_url.data
            cafe_info.seats = edit_cafe_info.seats.data
            cafe_info.coffee_price = f'£{edit_cafe_info.coffee_price.data:.2f}'
            cafe_info.has_sockets = edit_cafe_info.has_sockets.data
            cafe_info.has_toilet = edit_cafe_info.has_toilet.data
            cafe_info.has_wifi = edit_cafe_info.has_wifi.data
            cafe_info.can_take_calls = edit_cafe_info.can_take_calls.data
            db.session.commit()
            return redirect(url_for('update_cafe', api_key=api_key, _anchor=cafe_id))

    # load update page with delete & update buttons
    if '/cafes/update' in request.path or filters==[]:
        cafes = db.session.query(Cafe).all()
    else:
        cafes = db.session.query(Cafe).filter(and_(*filters)).all()
    return render_template('cafes.html', cafes=cafes, year=year, can_update=True, key=api_key)


@app.route("/cafes/search/", methods=['GET','POST'])
def search_cafe():
    year = datetime.now().year
    search_form = SearchCafeForm()
    keys = ['name', 'location', 'has_wifi', 'has_toilet', 'has_sockets', 'can_take_calls']
    if search_form.validate_on_submit():
            search_pars = { k:search_form.data[k] for k in keys if search_form.data[k] }
            if search_pars.get('name'):
                search_pars['name'] = search_pars['name'].title()
            if search_pars.get('location'):
                search_pars['location'] = search_pars['location'].title()

            global filters
            filters = [getattr(Cafe, parameter)==value  for parameter, value in search_pars.items()]

            cafes = db.session.query(Cafe).filter(and_(*filters)).all()
            return render_template('cafes.html', cafes=cafes, year=year)


    return render_template('form.html', form=search_form, year=year, is_search=True)


if __name__=='__main__':
    app.run(debug=True)
