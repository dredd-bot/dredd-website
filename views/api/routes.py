from functools import wraps
from contextlib import suppress
from quart_rate_limiter import rate_limit
from datetime import timedelta
from quart import Blueprint, jsonify, make_response, request

from scripts.caching import Cache as cache

api = Blueprint('api', __name__, url_prefix='/api')


def verify_token(f):
    @wraps(f)
    async def token(*args, **kwargs):
        if not request.headers:
            return await make_response(jsonify({'message': 'Please provide the authorization token!', 'status': 401}), 401)

        if 'Authorization' in request.headers and request.headers['Authorization'] != '':
            token = request.headers['Authorization']
        else:
            return await make_response(jsonify({'message': 'The authorization is missing!', 'status': 401}), 401)

        if 'Client' in request.headers and request.headers['Client'] != '':
            client = request.headers['Client']
        else:
            return await make_response(jsonify({'message': 'Client information is missing!', 'status': 401}), 401)

        valid_token = cache.get_from_cache(cache, 'api_token')
        valid_client = cache.get_from_cache(cache, 'api_client')
        if token and token != valid_token or client != valid_client:
            return await make_response(jsonify({'message': 'The token or client is invalid!', 'status': 403}), 403)
        elif token and token == valid_token and client == valid_client:
            return await f(*args, **kwargs)
    return token


@api.route('/')
@api.route('')
async def index():
    return await make_response(jsonify({'message': 'Welcome!', 'status': 200}), 200)


@api.route('/upvotes/', methods=['POST'])
@api.route('/upvotes', methods=['POST'])
@verify_token
@rate_limit(3, timedelta(seconds=60))
async def upvotes():
    # gonna finish this next time
    content = await request.get_json(force=True)

    return content


@api.route('/stats/', methods=['POST'])
@api.route('/stats', methods=['POST'])
@verify_token
@rate_limit(30, timedelta(seconds=60))
async def stats():
    content = await request.get_json(force=True)

    with suppress(Exception):
        guilds = content['guilds']
        users = content['users']

    from __init__ import db

    db.stats.update_one({"type": 'UserGuildCount'}, {"$set": {
        "guilds": guilds,
        "users": users
    }})
    cache.update_cache(cache, 'guilds', guilds)
    cache.update_cache(cache, 'users', "{:,}".format(users))

    return content


@api.route('/get/stats/', methods=['GET'])
@api.route('/get/stats', methods=['GET'])
@verify_token
async def get_stats():
    return await make_response(jsonify({"guilds": cache.get_from_cache(cache, 'guilds'), "users": cache.get_from_cache(cache, 'users'), "status": 200}), 200)
