import quart
import os
import secrets
import random
import asyncio
import discord
import config
import traceback
import mystbin

from contextlib import suppress
from collections import Counter
from pymongo import MongoClient
from discord.ext import commands, tasks
from discord_webhook import DiscordEmbed, DiscordWebhook
from quart import Quart, render_template, render_template_string, redirect, request
from quart_auth import AuthManager, AuthUser, login_user, login_required, Unauthorized, current_user

from scripts.theme import WebsiteTheme
from scripts.contents import Contents, log_app, get_partners
from scripts.caching import Cache

# main
app = Quart(import_name='Dredd Website', template_folder='website/templates', static_folder='website/static')
app.secret_key = secrets.token_hex(16)
AuthManager(app)
AVATARS_FOLDER = os.path.join('/static')
image = os.path.join(AVATARS_FOLDER, WebsiteTheme.icon)
not_found_icon = os.path.join(AVATARS_FOLDER, 'not_found.png')

# Database
db_client = MongoClient(config.MONGO)
db = db_client.get_database('website')

# Bot
bot = commands.Bot(intents=discord.Intents.all(), command_prefix='r!')

# cache
staff_applications = db.apps.find_one({'open': True})
count_submissions = Counter()
website_announcement = None
announcement_color = None
allow_invite, reason = True, None

partners_list = list(db.partners.find())
top_partner = None


@app.before_serving
async def run():
    loop = asyncio.get_event_loop()
    await bot.login(config.BOT_TOKEN)
    loop.create_task(bot.connect())
    await bot.wait_until_ready()
    await Cache.load_cache(Cache, bot)
    bot.load_extension('jishaku')


@tasks.loop(hours=1)  # update every hour
async def update_partners():
    global top_partner, partners_list
    top_partner = random.choice(partners_list)
    partners_list = list(db.partners.find())


@update_partners.before_loop
async def before_update_partners():
    await bot.wait_until_ready()
    print("Started randomizing partners")


@app.route('/')
@app.route('/home')
async def main_page():
    return await render_template('index.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 dredd=Cache.get_from_cache(Cache, 'me'),
                                 discord=discord)


@app.route('/about/')
@app.route('/about')
async def about_page():
    return await render_template('about.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 moksej=Cache.get_from_cache(Cache, 'moksej'),
                                 zenpa=Cache.get_from_cache(Cache, 'zenpa'),
                                 duck=Cache.get_from_cache(Cache, 'duck'),
                                 support=Cache.get_from_cache(Cache, 'staff'),
                                 discord=discord)


@app.route('/invite/')
@app.route('/invite')
async def bot_invite():
    if allow_invite:
        return redirect('https://discord.com/oauth2/authorize?client_id=667117267405766696&scope=bot&permissions=477588727&redirect_uri=https%3A%2F%2Fdiscord.gg%2Ff3MaASW&response_type=code')
    else:
        return await render_template('invite.html',
                                     icon=image,
                                     color=WebsiteTheme.color,
                                     footer=Contents.footer,
                                     reason=reason,
                                     staff=staff_applications,
                                     logged_in=await current_user.is_authenticated,
                                     announcement=website_announcement,
                                     announcement_color=announcement_color)


@app.route('/support/')
@app.route('/support')
async def bot_support():
    return redirect('https://discord.gg/f3MaASW')


@app.route('/legal/')
@app.route('/legal')
async def legal():
    return await render_template('legal.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color)


@app.route('/privacy-policy/')
@app.route('/privacy-policy')
async def legal_privacy():
    return redirect('/legal/#privacy-policy')


@app.route('/terms/')
@app.route('/terms-of-use/')
@app.route('/terms')
@app.route('/terms-of-use')
async def legal_tos():
    return redirect('/legal/#terms')


@app.route('/bot-lists/')
@app.route('/bot-lists')
async def bot_lists():
    return await render_template('lists.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color)


@app.route('/affiliates/')
@app.route('/partners/')
@app.route('/affiliates')
@app.route('/partners')
async def affiliates():
    if not bot.is_ready():
        return "Please refresh in a bit."
    return await render_template('affiliates.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 all_partners=await get_partners(bot, partners_list),
                                 top_partner=top_partner,
                                 bot=bot)


@app.route('/apply/', methods=['GET', 'POST'])
@app.route('/apply', methods=['GET', 'POST'])
async def apply():
    apps_closed, submitted, saw_success, valid = False, False, False, True

    if not staff_applications:
        apps_closed = True
    elif staff_applications:
        if request.method == 'GET':
            pass
        elif request.method == 'POST':
            response = await request.form
            db_check = db.apps.find_one({'userID': response['userID']})
            if not db_check:
                user = bot.get_user(int(response['userID']))
                if user:
                    valid, submitted = True, True
                    await log_app(bot, user, response, db)
                elif not user:
                    valid = False
                if valid:
                    submitted, saw_success, valid = True, False, True
            elif db_check:
                submitted, saw_success = True, True

    return await render_template('applications.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 submitted=submitted,
                                 saw_success=saw_success,
                                 apps_closed=apps_closed,
                                 staff=staff_applications,
                                 valid=valid,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 count=count_submissions)


@app.route('/staff/login/', methods=['GET', 'POST'])
@app.route('/staff/login', methods=['GET', 'POST'])
async def login():
    error = False
    if request.method == 'POST':
        response = await request.form
        staff_login = db.auth.find_one({'user': response['username']})
        if not staff_login:
            error = True
        elif staff_login:
            if response['password'] != staff_login['password']:
                error = True
            elif response['password'] == staff_login['password']:
                login_user(AuthUser(response['username']))
                webhook = DiscordWebhook(url=config.WEBHOOK_TOKEN, content=f"New login:\nUsername - {response['username']}")
                webhook.execute()
                return redirect('/staff/')

    return await render_template('staff/login.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 error=error,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color)


@app.route('/staff/', methods=['GET', 'POST'])
@app.route('/staff', methods=['GET', 'POST'])
@login_required
async def staff():
    success = None
    global staff_applications
    global website_announcement
    global announcement_color
    global allow_invite
    global reason
    response = await request.form
    if request.method == 'POST' and response:
        success = f'{current_user.auth_id}'
        # Staff apps
        if staff_applications and response['staff_apps'] == 'disabled':
            db.apps.update_one({'open': True}, {'$set': {
                'open': False
            }})
            staff_applications = False
            success += ' disabled the applications'
        elif not staff_applications and response['staff_apps'] == 'enabled':
            db.apps.update_one({'open': False}, {'$set': {
                'open': True
            }})
            staff_applications = True
            success += ' enabled the applications'
        # Website announcement
        if website_announcement and response['announcement'] != website_announcement and response['announcement'] != '' or not website_announcement and response['announcement'] != '':
            website_announcement = response['announcement']
            with suppress(Exception):
                announcement_color = response['color']
            success += f' set the announcement to {website_announcement}'
        elif website_announcement and response['announcement'] == '':
            website_announcement = None
            success += ' reset the announcement'
        # Invites
        if reason and response['bot-invite'] != reason and response['bot-invite'] != '' or not reason and response['bot-invite'] != '':
            allow_invite = False
            reason = response['bot-invite']
            success += f' disabled new invitations for {reason}'
        elif not allow_invite and response['bot-invite'] == '':
            allow_invite = True
            reason = ''
            success += " enabled new invitations"
        if len(success) > len(current_user.auth_id):
            webhook = DiscordWebhook(url=config.WEBHOOK_TOKEN, content=f"UPDATE: {success}")
            webhook.execute()
        success = success[len(current_user.auth_id):]

    request.method = 'GET'
    request.forms = ''
    return await render_template('staff/main.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 success=success,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 applications=list(db.apps.find({'status': 0})),
                                 reason=reason)


@app.route('/staff/applications/')
@app.route('/staff/applications')
@login_required
async def staff_apps():
    success = None
    return await render_template('staff/applications.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 success=success,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 applications=list(db.apps.find()),
                                 bot=bot)


@app.route('/staff/applications/<userid>', methods=['GET', 'POST'])
@login_required
async def user_app(userid):
    success = None
    if request.method == 'POST':
        message = ''
        response = await request.form
        user = bot.get_guild(671078170874740756).get_member(int(userid))
        if response['app_review'] == 'accept':
            message += f"{current_user.auth_id} acceped {user} ({userid}) application"
            db.apps.update_one({'userID': f"{userid}"}, {'$set': {
                "status": 1,
                "staff_reason": response['reason']
            }})
            if user:
                roles = [bot.get_guild(671078170874740756).get_role(776530530346205244), bot.get_guild(671078170874740756).get_role(679647636479148050)]
                for role in roles:
                    await user.add_roles(role, reason="Staff application was approved.")
                await user.send("Congratulations! Your staff application for Dredd Support has been approved!")
        elif response['app_review'] == 'decline':
            message += f"{current_user.auth_id} declined {user} ({userid}) application for {response['reason']}"
            db.apps.update_one({'userID': f"{userid}"}, {'$set': {
                "status": 2,
                "staff_reason": response['reason']
            }})
            if user:
                await user.send(f"Unfortunatelly your staff application for Dredd Support has been declined at this time for: {response['reason']}")
        elif response['app_review'] == 'delete':
            message += f"{current_user.auth_id} deleted {user} ({userid}) application for {response['reason']}"
            db.apps.delete_one({'userID': f"{userid}"})
            if user:
                await user.send(f"Unfortunatelly your staff application for Dredd Support has been deleted at this time for: {response['reason']}")
        webhook = DiscordWebhook(url=config.WEBHOOK_TOKEN, content=f"UPDATE: {message}")
        webhook.execute()
        return redirect('/staff/applications/')

    return await render_template('staff/apps.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 success=success,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 application=db.apps.find_one({'userID': f"{userid}"}),
                                 bot=bot)


@app.errorhandler(404)
async def not_found(e):
    return await render_template('errors/404.html',
                                 not_found_icon=not_found_icon,
                                 color=WebsiteTheme.color,
                                 icon=image,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color)


@app.errorhandler(500)
async def error_occured(e):
    return await render_template('errors/500.html',
                                 not_found_icon=not_found_icon,
                                 color=WebsiteTheme.color,
                                 icon=image,
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color)


@app.errorhandler(Unauthorized)
async def not_logged_in(e):
    return redirect('/staff/login')


@app.errorhandler(Exception)
async def exc(e):
    error_channel = bot.get_channel(703627099180630068)

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
                                 footer=Contents.footer,
                                 staff=staff_applications,
                                 logged_in=await current_user.is_authenticated,
                                 announcement=website_announcement,
                                 announcement_color=announcement_color,
                                 error=e)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    update_partners.start()
    app.run(debug=True, use_reloader=True, loop=loop, host='0.0.0.0', port=10224)
    loop.create_task(app)
