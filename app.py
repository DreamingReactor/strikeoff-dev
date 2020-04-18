from flask import Flask, jsonify, request, Response
from flask_pymongo import PyMongo
import json

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/strikeoff'

mongo = PyMongo(app)

@app.route('/test')
def test():
    return jsonify('A Test.')
    
@app.route('/register', methods = ['POST'])
def register():
    body = request.get_json()
    user_no = str(mongo.db.users.find().count())
    print(user_no)
    email = body.get('email', '')
    password = body.get('password', '')
    name = body.get('name', '')
    mobile = body.get('mobile')
    if not name:
        name = 'User_'+user_no
    email_exists_count = mongo.db.users.find({"email": email}).count() if email else 0
    mobile_exists_count = mongo.db.users.find({"mobile": mobile}).count() if mobile else 0
    if email == '' or password == '':
        response = json.dumps({'sucess': False, 'message': 'Email and password are required.'})
        status_code = 400
    elif email_exists_count > 0:
        response = json.dumps({'sucess': False, 'message': 'Email already exists.'})
        status_code = 409
    elif mobile_exists_count > 0:
        response = json.dumps({'sucess': False, 'message': 'Mobile already exists.'})
        status_code = 409
    else:
        data = {'email': email, "password": password, 'name': name}
        if mobile: data.update({'mobile': mobile})
        user_id = mongo.db.users.insert(data)
        response = json.dumps({'sucess': True, 'id': str(user_id)})
        status_code = 201
    return Response(response, status=status_code, mimetype='application/json')
