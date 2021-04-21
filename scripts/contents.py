import discord

from discord_webhook import DiscordEmbed, DiscordWebhook


class Contents:
    footer = """<body class="d-flex flex-column min-vh-100">
            <div class="wrapper flex-grow-1"></div>
            <footer id="footer" class="bg-dark text-white text-center">
                <p style="margin: 10px;">© 2021 <a class="text-light" href="https://github.com/dredd-bot/dredd-website/blob/master/LICENSE">Dredd</a></p>
            </footer>
        </body>"""


class Featured:
    icon = 'tet'


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
        "userID": response['userID'],
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
        "staff_reason": ''
    })
    await channel.send(embed=embed)
    await user.send(content="Thank you for applying, our administration team will look into your application soon. *Please don't ask for status of your application, if you do, it will be instantly declined.*")


async def get_partners(bot, partners):
    all_partners = []
    for partner in partners:
        the_bot = bot.get_user(partner['partner_bot'])
        short_message = partner['short_msg']
        partnered_since = partner['partner_since']
        website = partner['website']

        all_partners.append({'bot': the_bot, 'msg': short_message, 'since': partnered_since, 'website': website})

    return all_partners
