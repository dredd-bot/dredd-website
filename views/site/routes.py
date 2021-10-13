import quart
import os
import discord
import config

from datetime import timedelta
from discord.ext import commands
from quart_rate_limiter import rate_limit
from discord_webhook import DiscordWebhook
from quart_discord import requires_authorization, models
from quart import Blueprint, render_template, redirect, request, url_for, make_response, abort, flash, current_app

from scripts.theme import WebsiteTheme
from scripts.caching import Cache as cache
from scripts.contents import log_app, update_apps, update_announcement, verify_staff, block_invites, application_manage

site = Blueprint('site', __name__)
bot = commands.Bot(intents=discord.Intents.all(), command_prefix='r?')
intents = discord.Intents.none()
intents.members = False
intents.guilds = True
main_bot = commands.Bot(intents=intents, command_prefix='dredd??', status=discord.Status.offline)

AVATARS_FOLDER = os.path.join('/static/images')
image = os.path.join(AVATARS_FOLDER, WebsiteTheme.icon)
not_found_icon = os.path.join(AVATARS_FOLDER, 'not_found.png')

from __init__ import discord_session, db


@site.route('/')
@site.route('/home')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def main_page():
    user = models.User.get_from_cache()
    return await render_template('index.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 dredd=cache.get_from_cache(cache, 'me'),
                                 discord=discord,
                                 user=user,
                                 guild_count=cache.get_from_cache(cache, 'guilds'),
                                 user_count=cache.get_from_cache(cache, 'users'))


@site.route('/about/')
@site.route('/about')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def about_page():
    user = models.User.get_from_cache()
    return await render_template('about.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 moksej=cache.get_from_cache(cache, 'moksej'),
                                 zenpa=cache.get_from_cache(cache, 'zenpa'),
                                 duck=cache.get_from_cache(cache, 'duck'),
                                 support=cache.get_from_cache(cache, 'staff'),
                                 discord=discord,
                                 on_leave=cache.get_from_cache(cache, 'on_leave'),
                                 user=user,
                                 guild_count=cache.get_from_cache(cache, 'guilds'),
                                 user_count=cache.get_from_cache(cache, 'users'))


@site.route('/invite/')
@site.route('/invite')
@rate_limit(limit=30, period=timedelta(seconds=10))
async def bot_invite():
    user = models.User.get_from_cache()
    if user:
        guilds = user.guilds if user.guilds else await user.fetch_guilds()
    else:
        guilds = None
    return await render_template('invite.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 allow_invite=cache.get_from_cache(cache, 'allow_invite'),
                                 reason=cache.get_from_cache(cache, 'reason'),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user,
                                 guilds=guilds,
                                 bot=main_bot)


@site.route('/invite/<int:guild>')
@rate_limit(limit=60, period=timedelta(seconds=10))
async def bot_invite_guild(guild):
    if not cache.get_from_cache(cache, 'allow_invite'):
        return redirect('/invite')
    else:
        return await discord_session.create_session(
            scope=["bot"], permissions=485977335, guild_id=guild, disable_guild_select=True
        )


@site.route('/support/')
@site.route('/support')
@rate_limit(limit=60, period=timedelta(seconds=10))
async def bot_support():
    return redirect('https://discord.gg/f3MaASW')


@site.route('/legal/')
@site.route('/legal')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def legal():
    user = models.User.get_from_cache()
    return await render_template('legal.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user)


@site.route('/privacy-policy/')
@site.route('/privacy-policy')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def legal_privacy():
    return redirect('/legal/#privacy-policy')


@site.route('/terms/')
@site.route('/terms-of-use/')
@site.route('/terms')
@site.route('/terms-of-use')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def legal_tos():
    return redirect('/legal/#terms')


@site.route('/bot-lists/')
@site.route('/bot-lists')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def bot_lists():
    user = models.User.get_from_cache()
    return await render_template('lists.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user)


@site.route('/affiliates/')
@site.route('/partners/')
@site.route('/affiliates')
@site.route('/partners')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def affiliates():
    user = models.User.get_from_cache()
    if not bot.is_ready():
        return "Partners are not yet cached :/ Should be cached in the next few seconds, if not please report this to us <a href='/support/'>here</a>"
    return await render_template('affiliates.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 all_partners=cache.get_from_cache(cache, 'partners'),
                                 top_partner=cache.get_from_cache(cache, 'top_partner'),
                                 bot=bot,
                                 cache=cache,
                                 user=user)


@site.route('/apply/', methods=['GET', 'POST'])
@site.route('/apply', methods=['GET', 'POST'])
@rate_limit(limit=50, period=timedelta(seconds=10))
async def apply():
    user = models.User.get_from_cache()
    if user:
        if not user.guilds:
            await user.fetch_guilds()
        guilds = [x.name for x in user.guilds]
    else:
        guilds = None

    apps_closed, submitted, saw_success = False, False, False
    if not cache.get_from_cache(cache, 'staff_open'):
        apps_closed = True
    elif cache.get_from_cache(cache, 'staff_open'):
        if request.method == 'GET':
            if user:
                db_check = db.apps.find_one({'userID': user.id})
                if db_check and not request.args.get('submitted'):
                    saw_success, submitted = True, True
                elif db_check and request.args.get('submitted'):
                    submitted = True
        elif request.method == 'POST':
            submitted = True
            response = await request.form
            user = bot.get_user(int(user.id))
            await log_app(bot, user, response, db)
            cache.update_cache(cache, 'staff_apps', list(db.apps.find()))
            return redirect(url_for('.apply', submitted=submitted))

    return await render_template('applications.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 submitted=submitted,
                                 saw_success=saw_success,
                                 apps_closed=apps_closed,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user,
                                 guilds=guilds)


@site.route('/me/')
@site.route('/me')
@requires_authorization
@rate_limit(limit=30, period=timedelta(seconds=10))
async def my_profile():
    user = models.User.get_from_cache()
    guilds = user.guilds if user.guilds else await user.fetch_guilds()
    apps = list(db.apps.find({'userID': user.id}))
    return await render_template('profile.html',
                                 color=WebsiteTheme.color,
                                 icon=image,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 applications=apps,
                                 user=user,
                                 guilds=guilds,
                                 bot=main_bot,
                                 allow_invites=cache.get_from_cache(cache, 'allow_invite'),
                                 reason=cache.get_from_cache(cache, 'reason'))


@site.route('/view/<int:guild>')
@requires_authorization
@rate_limit(limit=30, period=timedelta(seconds=10))
async def view_guild(guild):
    user = models.User.get_from_cache()
    guild = main_bot.get_guild(guild)
    return await render_template('guildinfo.html',
                                 color=WebsiteTheme.color,
                                 icon=image,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 user=user,
                                 bot=main_bot,
                                 guild=guild)


@site.route('/login/')
@site.route('/login')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def login():
    return await discord_session.create_session(scope=['identify', 'guilds'])


@site.route('/logout/')
@site.route('/logout')
@rate_limit(limit=50, period=timedelta(seconds=10))
async def logout():
    discord_session.revoke()
    return redirect('/' if not request.referrer else request.referrer)


@site.route('/staff/', methods=['GET', 'POST'])
@site.route('/staff', methods=['GET', 'POST'])
@requires_authorization
@rate_limit(limit=50, period=timedelta(seconds=10))
async def staff():
    user = models.User.get_from_cache()
    if not verify_staff(db, user):
        abort(403)
    success = request.args.get('success')
    response = await request.form
    if request.method == 'POST' and response:
        success = f'{user}'
        # Staff apps
        success += update_apps(db, response)
        # Website announcement
        success += update_announcement(response)
        # Invites
        success += block_invites(response)

        if len(success) > len(str(user)):
            webhook = DiscordWebhook(url=config.WEBHOOK_TOKEN, content=f"UPDATE: {success}")
            webhook.execute()
        success = success[len(str(user)):]
        return redirect(url_for('.staff', success=success))

    return await render_template('staff/main.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 success=success,
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 applications=list(db.apps.find({'status': 0})),
                                 reason=cache.get_from_cache(cache, 'reason'),
                                 user=user)


@site.route('/staff/applications/')
@site.route('/staff/applications')
@requires_authorization
@rate_limit(limit=50, period=timedelta(seconds=10))
async def staff_apps():
    user = models.User.get_from_cache()
    if not verify_staff(db, user):
        abort(403)
    success = None
    return await render_template('staff/applications.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 success=success,
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 applications=cache.get_from_cache(cache, 'staff_apps'),
                                 bot=bot,
                                 user=user)


@site.route('/me/application/')
@site.route('/me/application')
@requires_authorization
@rate_limit(limit=50, period=timedelta(seconds=10))
async def my_application():
    user = models.User.get_from_cache()
    return await render_template('staff/apps.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 application=db.apps.find_one({'userID': user.id}),
                                 bot=bot,
                                 user=user)


@site.route('/staff/applications/<userid>', methods=['GET', 'POST'])
@requires_authorization
@rate_limit(limit=30, period=timedelta(seconds=10))
async def user_app(userid):
    logged_in_user = models.User.get_from_cache()
    if not verify_staff(db, logged_in_user):
        abort(403)
    success = None
    if request.method == 'POST':
        message = ''
        response = await request.form
        message += await application_manage(response, logged_in_user, userid, bot, db)
        webhook = DiscordWebhook(url=config.WEBHOOK_TOKEN, content=f"UPDATE: {message}")
        webhook.execute()
        return redirect('/staff/applications/')

    return await render_template('staff/apps.html',
                                 icon=image,
                                 color=WebsiteTheme.color,
                                 staff=cache.get_from_cache(cache, 'staff_open'),
                                 success=success,
                                 logged_in=await discord_session.authorized,
                                 is_staff=verify_staff(db, logged_in_user),
                                 announcement=cache.get_from_cache(cache, 'announcement'),
                                 announcement_color=cache.get_from_cache(cache, 'announcement_color'),
                                 application=db.apps.find_one({'userID': int(userid)}),
                                 bot=bot,
                                 user=logged_in_user)


@site.route("/callback")
@rate_limit(limit=50, period=timedelta(seconds=10))
async def callback():
    data = await discord_session.callback()
    await discord_session.fetch_user()
    return redirect("/" if not request.referrer else request.referrer)
