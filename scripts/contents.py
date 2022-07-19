import discord

from datetime import datetime
from contextlib import suppress
from scripts.caching import Cache as cache
from discord_webhook import DiscordEmbed, DiscordWebhook
from contextlib import suppress


async def log_app(bot, user, response, db):
    embed = discord.Embed(title='New application submitted', color=1800669)
    embed.description = f"""**User:** {user.mention} {user.id}"""
    embed.add_field(name="Why do you want to become a staff member?", value=response['reason'][:500] + '...' if len(response['reason']) > 500 else response['reason'], inline=False)
    embed.add_field(name="How old are you?", value=response['age'] if response['age'] else "Didn't say", inline=False)
    embed.add_field(name="Do you have any experience being staff?", value=response['experience'][:500] + '...' if len(response['experience']) > 500 else response['experience'], inline=False)
    embed.add_field(name="What languages do you speak?", value=response['languages'][:500] + '...' if len(response['languages']) > 500 else response['languages'], inline=False)
    embed.add_field(name="What country do you reside in and what is your timezone?", value=response['reside'][:500] + '...' if len(response['reside']) > 500 else response['reside'], inline=False)
    embed.add_field(name="Why should we choose you over another applicant?", value=response['choose'][:500] + '...' if len(response['choose']) > 500 else response['choose'], inline=False)
    embed.add_field(name="Is Dredd open sourced?", value=response['openSrc'])
    embed.add_field(name="Does Dredd have a web-dashboard?", value=response['webdash'])
    embed.add_field(name="Can you send NSFW stuff in the server?", value=response['nsfw'])
    embed.add_field(name="A member is mini-modding, what would you do?", value=response['mini-mod'][:500] + '...' if len(response['mini-mod']) > 500 else response['mini-mod'], inline=False)
    embed.add_field(name="You punished the wrong member, what do you do?", value=response['wrong-member'][:500] + '...' if len(response['wrong-member']) > 500 else response['wrong-member'], inline=False)
    embed.add_field(name="User opened a ticket and has concerns about the data stored, what do you do?", value=response['privacy'][:500] + '...' if len(response['privacy']) > 500 else response['privacy'], inline=False)
    embed.add_field(name="User opened a ticket and wants to partner their bot or server, what do you do?", value=response['partner'][:500] + '...' if len(response['partner']) > 500 else response['partner'], inline=False)
    channel = bot.get_channel(809015898811400252)
    db.apps.insert_one({
        "userID": user.id,
        "reason": response['reason'],
        "age": response['age'],
        "experience": response['experience'],
        "languages": response['languages'],
        "reside": response['reside'],
        "choose": response['choose'],
        "openSrc": response['openSrc'],
        "webdash": response['webdash'],
        "nsfw": response['nsfw'],
        "mini-mod": response['mini-mod'],
        "wrong-member": response['wrong-member'],
        "privacy": response['privacy'],
        "partner": response['partner'],
        "status": 0,
        "staff_reason": '',
        "updated_at": datetime.utcnow()
    })
    message = await channel.send(embed=embed, content="<@&674940101801017344>", allowed_mentions=discord.AllowedMentions(roles=True))
    await message.add_reaction("<:PGCyes:809035120353869834>")
    await message.add_reaction("<:PGCno:809035137651965982>")
    with suppress(Exception):
        await user.send(content="Thank you for applying, our administration team will look into your application soon. *Please don't ask for status of your application, if you do, it will be instantly declined.*")


def update_apps(db, response):
    success = ''
    if cache.get_from_cache('staff_open') and response['staff_apps'] == 'disabled':
        db.apps.update_one({'open': True}, {'$set': {
            'open': False
        }})
        cache.update_cache('staff_open', False)
        success += ' disabled the applications'
    elif not cache.get_from_cache('staff_open') and response['staff_apps'] == 'enabled':
        db.apps.update_one({'open': False}, {'$set': {
            'open': True
        }})
        cache.update_cache('staff_open', True)
        success += ' enabled the applications'

    return success


def update_announcement(response):
    success = ''
    if cache.get_from_cache('announcement') and response['announcement'] != cache.get_from_cache('announcement') and response['announcement'] != '' or not cache.get_from_cache('announcement') and response['announcement'] != '':
        cache.update_cache('announcement', response['announcement'])
        with suppress(Exception):
            cache.update_cache('announcement_color', response['color'])
        success += f" set the announcement to {cache.get_from_cache('announcement')}"
    elif cache.get_from_cache('announcement') and response['announcement'] == '':
        cache.update_cache('announcement_color', None)
        cache.update_cache('announcement', None)
        success += ' reset the announcement'
    elif cache.get_from_cache('announcement') and response['announcement'] == cache.get_from_cache('announcement') and cache.get_from_cache('announcement_color') != response['color']:
        cache.update_cache('announcement_color', response['color'])
        success += ' set the color to {0}'.format(response['color'])

    return success


def block_invites(response):
    success = ''
    reason = cache.get_from_cache('reason')
    if reason and response['bot-invite'] != reason and response['bot-invite'] != '' or not reason and response['bot-invite'] != '':
        cache.update_cache('allow_invite', False)
        cache.update_cache('reason', response['bot-invite'])
        success += f' disabled new invitations for {response["bot-invite"]}'
    elif not cache.get_from_cache('allow_invite') and response['bot-invite'] == '':
        cache.update_cache('allow_invite', True)
        cache.update_cache('reason', response['bot-invite'])
        success += " enabled new invitations"

    return success


def verify_staff(db, user):
    if user:
        is_staff = True if db.auth.find_one({"user_id": user.id}) else False
        return is_staff
    else:
        return False


async def application_manage(response, logged_in_user, userid, bot, db):
    user = bot.get_guild(671078170874740756).get_member(int(userid))
    message = ''
    if response['app_review'] == 'accept':
        message += f"{logged_in_user} acceped {user} ({userid}) application"
        db.apps.update_one({'userID': int(userid)}, {'$set': {
            "status": 1,
            "staff_reason": response['reason']
        }})
        cache.update_cache('staff_apps', list(db.apps.find()))
        if user:
            roles = [bot.get_guild(671078170874740756).get_role(776530530346205244), bot.get_guild(671078170874740756).get_role(679647636479148050)]
            for role in roles:
                await user.add_roles(role, reason="Staff application was approved.")
            await user.send("Congratulations! Your staff application for Dredd Support has been approved!")
    elif response['app_review'] == 'decline':
        message += f"{logged_in_user} declined {user} ({userid}) application for {response['reason']}"
        db.apps.update_one({'userID': int(userid)}, {'$set': {
            "status": 2,
            "staff_reason": response['reason']
        }})
        cache.update_cache('staff_apps', list(db.apps.find()))
        if user:
            await user.send(f"Unfortunatelly your staff application for Dredd Support has been declined at this time for: {response['reason']}")
    elif response['app_review'] == 'delete':
        message += f"{logged_in_user} deleted {user} ({userid}) application for {response['reason']}"
        db.apps.delete_one({'userID': int(userid)})
        if user:
            await user.send(f"Unfortunatelly your staff application for Dredd Support has been deleted at this time for: {response['reason']}")
        cache.update_cache('staff_apps', list(db.apps.find()))

    return message


async def leave_a_message(bot, response, db):
    channel = bot.get_channel(854659639688691752)
    if response.get('anonymous'):
        response.pop('username')
    db.message.insert_one({
        "user": response.get("username", 'Anonymous'),
        "message": response.get("message")
    })
    await channel.send(f"{response.get('username', 'Anonymous')}:\n{response.get('message')}", allowed_mentions=discord.AllowedMentions.none())
