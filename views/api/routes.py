from discord import Embed
from functools import wraps
from contextlib import suppress
from quart_rate_limiter import rate_limit
from datetime import timedelta
from quart import Blueprint, jsonify, make_response, request, current_app

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

        valid_token = cache.get_from_cache(cache, 'api_token')
        if token and token != valid_token:
            return await make_response(jsonify({'message': 'The token is invalid!', 'status': 403}), 403)
        elif token and token == valid_token:
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

    user_id = content.get("user") or content.get("id") or content.get("uid") or content.get("User")

    if isinstance(user_id, dict):
        user_id = user_id.get("ClientID") or user_id.get("id")

    user = await current_app.main_bot.fetch_user(int(user_id))
    print(user)
    embed = Embed(title="New vote received!", url="https://dredd-bot.xyz")
    embed.set_image(url="https://media.discordapp.net/attachments/638902095520464908/659611283443941376/upvote.png?width=180&height=180")
    embed.set_author(name=user, icon_url=user.avatar_url)
    channel = current_app.main_bot.get_channel(679647378210291832)
    print((channel, embed.to_dict()))
    await channel.send(embed=embed)

    return await make_response({"message": "Success"}, 200)


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
