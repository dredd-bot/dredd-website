from discord import Embed
from functools import wraps
from contextlib import suppress
from quart_rate_limiter import rate_limit
from datetime import timedelta, datetime
from quart import Blueprint, jsonify, make_response, request, current_app

from time import time
from scripts.caching import Cache as cache

api = Blueprint('api', __name__, url_prefix='/api')


# List of supported bot lists
BOT_LISTS = {
    "dservices": 'https://discordservices.net/bot/dredd',
    "dbl": 'https://discord.ly/dredd',
    "dbots": 'https://dboats.cc/dredd',
    "dboats": 'https://discord.boats/bot/667117267405766696',
    "void": 'https://voidbots.net/bot/667117267405766696',
    "discords": 'https://discords.com/bots/bot/667117267405766696',
    "topcord": 'https://topcord.xyz/bot/667117267405766696',
    "shitgg": 'https://top.gg/bot/667117267405766696',
}


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
    try:
        content = await request.get_json(force=True)
        url_args = request.args.get("list", None)
        bot_list = BOT_LISTS.get(url_args, None) if url_args else None

        user_id = content.get("user") or content.get("id") or content.get("uid") or content.get("User")
        if isinstance(user_id, dict):
            user_id = user_id.get("ClientID") or user_id.get("id")

        user = await current_app.main_bot.fetch_user(int(user_id))
        current_time = int(time())
        embed = Embed(title="New vote received!", url=bot_list or None, color=0x5E82AC)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/638902095520464908/659611283443941376/upvote.png?width=180&height=180")
        embed.set_author(name=user, icon_url=user.avatar_url)
        embed.description = f"**{user}** has voted for me on [{url_args}]({bot_list}) - <t:{current_time}:R> (<t:{current_time}>)"
        channel = current_app.main_bot.get_channel(679647378210291832)
        await channel.send(embed=embed, content=None if bot_list else "<@345457928972533773> Vote posted from unknown site")

        db_check = current_app.db.find_one({"user_id": user.id})
        if db_check:
            current_app.db.update_one({"user_id": user.id}, {"$push": {
                {
                    "votes": {
                        "time": current_time + 43200,  # a vote it valid for 12 hours
                        "bot_list": bot_list
                    }
                }
            }})
        else:
            current_app.db.insert_one({
                "user_id": user.id,
                "votes": [
                    {"time": current_time + 43200, "bot_list": bot_list}  # a vote it valid for 12 hours
                ]
            })

        return await make_response({"message": "Success"}, 200)
    except Exception:
        return await make_response({"message": "Error occured!", "status": 500}, 500)


@api.route("/upvotes/<int:uid>", methods=["GET"])
@verify_token
@rate_limit(60, timedelta(seconds=20))
async def upvote(uid):
    get_vote = current_app.db.find_one({"user_id": uid})

    if not get_vote:
        return await make_response({"message": "Vote not found.", "status": 404}, 404)

    valid_votes = [vote for vote in get_vote if vote["time"] > time()]
    expiry = time()
    for vote in valid_votes:
        if vote["time"] > expiry:
            expiry = vote["time"]
        else:
            continue

    user_dict = {
        "user_id": uid,
        "voted": len(valid_votes) >= 1,
        "expire": expiry,
        "votes": valid_votes,
    }

    return make_response(jsonify(user_dict), 200)


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
