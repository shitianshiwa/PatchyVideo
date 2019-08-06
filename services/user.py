import time
import os
import binascii
import re
from datetime import datetime
from bson.json_util import dumps

from init import app, rdb
from utils.jsontools import *
from utils.dbtools import makeUserMeta

from spiders import dispatch
from db import tagdb, db

from utils.crypto import *

from bson import ObjectId
import redis_lock

EXPIRE_TIME = 30 * 60
LOGIN_EXPIRE_TIME = 24 * 60 * 60

def query_user_basic_info(uid) :
    obj = db.users.find_one({"_id": ObjectId(uid)})
    if obj is None :
        return None
    return obj['profile']

def verify_session(sid, stype) :
    ret = rdb.get(sid) == stype.encode()
    return ret

def require_session(session_type) :
    # TODO: add challenge code to redis
    sid = binascii.hexlify(bytearray(random_bytes(16))).decode()
    rdb.set(sid, session_type, ex = int(time.time() + EXPIRE_TIME))
    return sid

def logout(sid) :
    rdb.delete(sid)

# we allow the same user to login multiple times and all of his login sessions are valid
def login(username, password, challenge, login_session_id) :
    if verify_session(login_session_id, 'LOGIN') :
        user_obj = db.users.find_one({'profile.username': username})
        if not user_obj :
            return "USER_NOT_EXIST", None
        if not verify_password_PBKDF2(password, user_obj['crypto']['salt1'], user_obj['crypto']['password_hashed']) :
            return "INCORRECT_PASSWORD", None
        common_user_obj = {
            '_id': user_obj['_id'],
            'profile': {
                'username': user_obj['profile']['username'],
                'image': user_obj['profile']['image'],
                'desc': user_obj['profile']['desc']
            },
            'access_control': user_obj['access_control']
        }
        redis_user_value = dumps(common_user_obj)
        redis_user_key = binascii.hexlify(bytearray(random_bytes(128))).decode()
        rdb.set(redis_user_key, redis_user_value, ex = int(time.time() + LOGIN_EXPIRE_TIME))
        return "SUCCEED", redis_user_key
    return "INCORRECT_SESSION", None

def query_user(uid) :
    return db.users.find_one({'_id': ObjectId(uid)})

def signup(username, password, email, challenge, signup_session_id) :
    if verify_session(signup_session_id, 'SIGNUP') :
        if email :
            if len(email) > 128 or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return "INCORRECT_EMAIL", None
        crypto_method, password_hashed, salt1, salt2, master_key_encryptyed = generate_user_crypto_PBKDF2(password)
        with redis_lock.Lock(rdb, 'signup:' + username) :
            user_obj_find = db.users.find_one({'profile.username': username})
            if user_obj_find is not None :
                return "USER_EXIST", None
            user_obj = {
                'profile': {
                    'username': username,
                    'desc': 'Write something here',
                    'pubkey': '',
                    'image': 'default',
                    'email': email
                },
                'crypto': {
                    'crypto_method': crypto_method,
                    'password_hashed': password_hashed,
                    'salt1': salt1,
                    'salt2': salt2,
                    'master_key_encryptyed': master_key_encryptyed
                },
                'access_control': {
                    'status': 'normal',
                    'access_mode': 'blacklist',
                    'allowed_ops': [],
                    'denied_ops': []
                },
                'meta': {
                    'created_at': datetime.now()
                }
            }
            return "SUCCEED", db.users.insert_one(user_obj).inserted_id
    return "INCORRECT_SESSION", None

def update_desc(redis_user_key, user_id, new_desc) :
    if len(new_desc) > 2048 :
        return "DESC_LENGTH"
    obj = db.users.find_one({'_id': ObjectId(user_id)})
    if obj is None :
        return 'USER_NOT_EXIST'
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'profile.desc': new_desc}})
    common_user_obj = {
            '_id': ObjectId(obj['_id']),
            'profile': {
                'username': obj['profile']['username'],
                'image': obj['profile']['image'],
                'desc': obj['profile']['desc']
            },
            'access_control': obj['access_control']
        }
    redis_user_value = dumps(common_user_obj)
    rdb.set(redis_user_key, redis_user_value, ex = int(time.time() + LOGIN_EXPIRE_TIME))
    return 'SUCCEED'

def update_password(user_id, old_pass, new_pass) :
    if len(old_pass) > 64 or len(old_pass) < 8:
        return "PASSWORD_LENGTH"
    if len(new_pass) > 64 or len(new_pass) < 8:
        return "PASSWORD_LENGTH"
    obj = db.users.find_one({'_id': ObjectId(user_id)})
    if obj is None :
        return 'USER_NOT_EXIST'
    if not verify_password_PBKDF2(old_pass, obj['crypto']['salt1'], obj['crypto']['password_hashed']) :
        return 'INCORRECT_PASSWORD'
    crypto_method, password_hashed, salt1, salt2, master_key_encryptyed = update_crypto_PBKDF2(old_pass, new_pass, obj['crypto']['salt2'], obj['crypto']['master_key_encryptyed'])
    crypto = {
        'crypto_method': crypto_method,
        'password_hashed': password_hashed,
        'salt1': salt1,
        'salt2': salt2,
        'master_key_encryptyed': master_key_encryptyed
    }
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'crypto': crypto}})
    return 'SUCCEED'
