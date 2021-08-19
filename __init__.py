import asyncio
import secrets
import config
import sys
import os
import discord
import time
import random
import mystbin
import traceback

from pymongo import MongoClient
from quart import Quart, request, render_template, redirect
from quart_rate_limiter import rate_limit, RateLimiter
from quart_discord import DiscordOAuth2Session, Unauthorized, AccessDenied, models

from datetime import timedelta
from scripts.theme import WebsiteTheme
from discord.ext import tasks, commands
from scripts.contents import verify_staff
from scripts.caching import Cache as cache
from views.site.routes import site, bot, main_bot
from views.api.routes import api


async def key_func():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    return ip


app = Quart(import_name=__name__, template_folder='templates', static_folder='static')
app.secret_key = secrets.token_hex(16)
app.config["DISCORD_CLIENT_ID"] = 667117267405766696
app.config["DISCORD_CLIENT_SECRET"] = config.SECRET
app.config["DISCORD_REDIRECT_URI"] = "http://dredd-bot.xyz/callback"
app.config["DISCORD_BOT_TOKEN"] = config.MAIN_TOKEN

discord_session = DiscordOAuth2Session(app)
rate_limiter = RateLimiter(app, key_function=key_func)

app.register_blueprint(site)
app.register_blueprint(api)

AVATARS_FOLDER = os.path.join('/static/images')
not_found_icon = os.path.join(AVATARS_FOLDER, 'not_found.png')
image = os.path.join(AVATARS_FOLDER, WebsiteTheme.icon)

db_client = MongoClient(config.MONGO)
db = db_client.get_database('website')


@app.before_serving
async def run():
    loop = asyncio.get_event_loop()
    start_time = time.time()
    await bot.login(config.BOT_TOKEN)
    await main_bot.login(config.MAIN_TOKEN)
    loop.create_task(bot.connect())
    loop.create_task(main_bot.connect())
    await bot.wait_until_ready()
    end_time = time.time() - start_time
    print("Took to boot: {0}".format(end_time))
    cache.__init__(cache)
    await cache.load_cache(cache, bot, main_bot, db)
    bot.load_extension('jishaku')
    update_partners.start()

bot = bot
main_bot = main_bot


@tasks.loop(hours=3)  # update every 3 hours
async def update_partners():
    await cache.load_cache(cache, bot, main_bot, db)
    partners_list = cache.get_from_cache(cache, 'partners')
    cache.update_cache(cache, 'top_partner', random.choice(partners_list))


@update_partners.before_loop
async def before_update_partners():
    await bot.wait_until_ready()
    print("Started randomizing partners")


@app.errorhandler(404)
@rate_limit(limit=50, period=timedelta(seconds=10))
async def not_found(e):
    user = models.User.get_from_cache()
    return await render_template('errors/404.html',
                                 not_found_icon=not_found_icon,
                                 color=WebsiteTheme.color,
                                 icon=image,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user)


@app.errorhandler(429)
async def ratelimited(e):
    user = models.User.get_from_cache()
    return await render_template('errors/custom.html',
                                 title="429 - Ratelimited",
                                 description="You're accessing this route too fast, please slow down!",
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user)


@app.errorhandler(403)
async def forbidden(e):
    user = models.User.get_from_cache()
    return await render_template('errors/custom.html',
                                 title="403 - Forbidden",
                                 description="The route you're trying to access is not accessible by you!",
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user)


@app.errorhandler(405)
async def forbidden(e):
    user = models.User.get_from_cache()
    return await render_template('errors/custom.html',
                                 title="405 - Method Not Allowed",
                                 description="The method is not allowed for the requested URL!",
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user)


@app.errorhandler(Exception)
@rate_limit(limit=1, period=timedelta(seconds=10))
async def exc(e):
    user = models.User.get_from_cache()
    error_channel = bot.get_channel(836993491485458454)

    emb = discord.Embed(color=discord.Color.red(), title="Error Occured!")
    error = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    if len(error) > 2000:
        mystbin_client = mystbin.Client()
        error = await mystbin_client.post(error, syntax='python')
    else:
        error = f"```py\n{error}```"
    emb.description = f"{error}"
    await error_channel.send(embed=emb, content="Error occured!")

    return await render_template('errors/exception.html',
                                 not_found_icon=not_found_icon,
                                 color=WebsiteTheme.color,
                                 icon=image,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 error=e,
                                 user=user)


@app.errorhandler(Unauthorized)
async def not_logged_in(e):
    return redirect('/login')


@app.errorhandler(AccessDenied)
async def accessdenied(e):
    return redirect('/' if not request.referrer else request.referrer)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    if str(sys.platform) == ('win32' or 'win64'):
        host = '127.0.0.1'
        port = 5000
    else:
        host = '0.0.0.0'
        port = 10224
    app.run(debug=True, use_reloader=True, loop=loop, host=host, port=port)
    loop.create_task(app)
