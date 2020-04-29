from flask import Flask, jsonify, request, Response
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, get_jwt_identity, get_raw_jwt
from passlib.hash import pbkdf2_sha256 as sha256
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson import json_util

def generate_hash(password):
    return sha256.hash(password)
def verify_hash(password, hash):
    return sha256.verify(password, hash)

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/strikeoff'
app.config['JWT_SECRET_KEY'] = 'strike-off'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh_token'
jwt = JWTManager(app)

mongo = PyMongo(app)

@app.route('/test')
def test():
    return jsonify('A Test.')
    
@app.route('/register', methods = ['POST'])
def register():
    body = request.get_json()
    user_no = str(mongo.db.users.find().count())
    email = body.get('email', '')
    password = body.get('password', '')
    name = body.get('name', '')
    mobile = body.get('mobile')
    if not name:
        name = 'User_'+user_no
    email_exists_count = mongo.db.users.find({"email": email}).count() if email else 0
    mobile_exists_count = mongo.db.users.find({"mobile": mobile}).count() if mobile else 0
    if email == '' or password == '':
        response = jsonify({'sucess': False, 'msg': 'Email and password are required.'})
        status_code = 400
    elif email_exists_count > 0:
        response = jsonify({'sucess': False, 'msg': 'Email already exists.'})
        status_code = 409
    elif mobile_exists_count > 0:
        response = jsonify({'sucess': False, 'msg': 'Mobile already exists.'})
        status_code = 409
    else:
        data = {'email': email, "password": generate_hash(password), 'name': name}
        if mobile: data.update({'mobile': mobile})
        user_id = mongo.db.users.insert(data)
        access_token = create_access_token(identity = str(user_id))
        refresh_token = create_refresh_token(identity= str(user_id))
        response = jsonify({'sucess': True, 'id': str(user_id)})
        status_code = 201
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
    return response, status_code

@app.route('/login', methods = ['POST'])
def login():
    body = request.get_json()
    username = body.get('username', '')
    password = body.get('password', '')
    if username == '' or password == '':
        response = jsonify({'sucess': False, 'msg': 'User ID and password are required.'})
        status_code = 400
    else:
        if username.isdigit():
            user = mongo.db.users.find_one({"mobile": username})
        else:
            user = mongo.db.users.find_one({"email": username})
        if user:
            if verify_hash(password, user["password"]):
                # user['_id'] = str(user['_id'])
                # del(user['password'])
                access_token = create_access_token(identity = str(user["_id"]))
                refresh_token = create_refresh_token(identity= str(user["_id"]))
                response = jsonify({'sucess': True, 'msg': 'Successfully logged in.'})
                status_code = 200
                set_access_cookies(response, access_token)
                set_refresh_cookies(response, refresh_token)
            else:
                response = jsonify({'sucess': False, 'msg': 'Wrong Password.'})
                status_code = 403
        else:
            response = jsonify({'sucess': False, 'msg': 'User doesn\'t exist.'})
            status_code = 404
    return response, status_code

@app.route('/refresh_token', methods = ['GET'])
@jwt_refresh_token_required
def refresh_token():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity = current_user)
    response = jsonify({'refresh': True})
    set_access_cookies(response, access_token)
    return response, 200


@app.route('/user_detail', methods = ['GET'])
@jwt_required
def user_detail():
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    mobile = None
    if 'mobile' in user:
        mobile = user['mobile']
    response = jsonify({'name': user['name'],'email': user['email'], 'mobile': mobile})
    return response, 200

@app.route('/logout', methods = ['GET'])
def logout():
    response = jsonify({'sucess': True, 'msg': 'Successfully logged out.'})
    unset_jwt_cookies(response)
    return response, 200
