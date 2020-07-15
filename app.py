import os
from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId 
import bcrypt

from os import path  
if path.exists("env.py"):      
     import env 



app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'workspace_database'
app.config["MONGO_URI"] = os.getenv('MONGO_URI', 'mongodb://localhost')
app.config["SECRET_KEY"] = os.urandom(24)

mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/get_workspaces')
def get_workspaces():
    return render_template("workspaces.html", workspaces=mongo.db.workspaces.find().sort("_id", -1))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name': request.form['username'], 'password': hashpass})
            session['username'] = request.form['username']
            session['logged_in'] = True
            flash('Hello ' + session['username'] + ', you have been successfully registered and logged in', 'success')
            return redirect(url_for('get_workspaces'))

        else:
            flash('This username is already in use', 'warning')

    return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method =='POST':
        users = mongo.db.users
        login_user = users.find_one({'name': request.form['username']})

        if login_user:
            if bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['password']):
                session['username'] = login_user['name']
                flash('Hello ' + session['username'] + ', you have been logged in', 'success')
                session['logged_in'] = True
                return redirect(url_for('profile'))

        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/add_workspaces')
def add_workspaces():
    if 'username' not in session:
        flash('You need to be logged in to add workspace', 'warning')
        return redirect(url_for('login'))
    return render_template('addworkspaces.html', rooms=mongo.db.rooms.find(), ratings=mongo.db.ratings.find(),
                            preferences=mongo.db.preferences.find(), indexes=mongo.db.indexes.find(), session_username=session['username'])


@app.route('/insert_workspaces', methods=['POST'])
def insert_workspaces():
    if 'username' in session:
        if request.method == 'POST':
            workspaces = mongo.db.workspaces
            workspaces.insert(request.form.to_dict())
            flash('You have added a new workspace', 'success')
            return redirect(url_for('get_workspaces'))
        return render_template('addworkspaces.html', rooms=mongo.db.rooms.find(), ratings=mongo.db.ratings.find(),
                                preferences=mongo.db.preferences.find(), indexes=mongo.db.indexes.find(), 
                                session_username=session['username'])
    flash('You need to be logged in to add workspace', 'warning')
    return redirect(url_for('login'))


@app.route('/edit_workspaces/<workspace_id>')
def edit_workspaces(workspace_id):
    '''
    Check if user is logged in:
      Get the workspace by id.
      Check if username in session is the same as the username in the workspace:
         Return editworkspaces page
      else redirect to login page
    If user not logged in, redirect to login page
    '''
    if 'username'  in session:
        current_workspace = mongo.db.workspaces.find_one({'_id': ObjectId(workspace_id)})
        if session['username'] == current_workspace['username']:
            current_workspace = mongo.db.workspaces.find_one({'_id': ObjectId(workspace_id)})
            return render_template('editworkspaces.html', workspace=current_workspace, rooms=mongo.db.rooms.find(), 
                                    ratings=mongo.db.ratings.find(), preferences=mongo.db.preferences.find(), indexes=mongo.db.indexes.find(), 
                                    session_username=session['username'])
        flash('You need to be logged in to edit a workspace', 'danger')
        return redirect(url_for('login'))
    flash('You need to be logged in to edit a workspace', 'danger')
    return redirect(url_for('login'))


@app.route('/update_workspaces/<workspace_id>', methods=['POST'])
def update_workspaces(workspace_id):
    '''
    Check if user is logged:
      If yes, check if method is POST:
          If yes, get the workspace by id, update the workspace and redirect to workspaces page
          If no, return to editworkspaces page
    If not logged in, redirect to login page
    '''
    if 'username' in session:
        if request.method == 'POST':
            workspaces = mongo.db.workspaces
            workspaces.update({'_id': ObjectId(workspace_id)},
            {
                'workspace_room': request.form.get('workspace_room'),
                'workspace_rating': request.form.get('workspace_rating'),
                'workspace_preference': request.form.get('workspace_preference'),
                'happiness_index': request.form.get('happiness_index'),
                'image': request.form.get('image'),
                'comments': request.form.get('comments'),
                'username': session['username']
            })
            return redirect(url_for('get_workspaces'))
        return render_template('editworkspaces.html', workspace=current_workspace, rooms=mongo.db.rooms.find(), 
                                ratings=mongo.db.ratings.find(), preferences=mongo.db.preferences.find(), indexes=mongo.db.indexes.find(), 
                                session_username=session['username'])
    flash('You need to be logged in to edit workspace', 'warning')
    return redirect(url_for('login'))


@app.route('/delete_workspaces/<workspace_id>')
def delete_workspaces(workspace_id):
    if 'username' in session:
        current_workspace = mongo.db.workspaces.find_one({'_id': ObjectId(workspace_id)})
        if session['username'] == current_workspace['username']: 
            mongo.db.workspaces.remove({'_id': ObjectId(workspace_id)})
            return redirect(url_for('profile'))
        flash('You need to be logged in to edit a workspace', 'danger')
        return redirect(url_for('login'))
    flash('You need to be logged in to edit a workspace', 'danger')
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('You need to be logged in to add workspace', 'warning')
        return redirect(url_for('login'))
    return render_template("profile.html", workspaces=mongo.db.workspaces.find({'username': session['username']}).sort("_id", -1), 
    session_username=session['username'])


@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   flash('You have been logged out', 'warning')
   session['logged_in'] = False
   return redirect(url_for('get_workspaces'))


@app.errorhandler(404)
def error_404(error):
    return render_template('error_pages/404.html', error=error)


@app.errorhandler(500)
def error_500(error):
    return render_template('error_pages/500.html', error=error)


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)