from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Votes:
    user: int
    type: Optional[str]


class Cache:
    # users, bot & staff
    moksej = None
    zenpa = None
    duck = None
    josh = None
    me = None
    staff = []
    on_leave = None

    guilds = None
    users = None

    # partners
    partners = []
    top_partner = {}

    # applications
    staff_open = False
    staff_apps = None

    # site caching (announcements, invite stuff)
    announcement = None
    announcement_color = None
    allow_invite = True
    reason = None

    testing = None

    # api
    api_token = None
    api_client = None

    @classmethod
    async def load_cache(cls, bot, main_bot, db):
        cls.moksej = bot.get_guild(671078170874740756).get_member(345457928972533773)
        cls.zenpa = bot.get_guild(671078170874740756).get_member(373863656607318018)
        cls.duck = bot.get_guild(671078170874740756).get_member(443217277580738571)
        cls.josh = bot.get_guild(671078170874740756).get_member(843866750131109909)
        cls.me = bot.get_guild(671078170874740756).get_member(667117267405766696)

        stats = list(db.stats.find({"type": "UserGuildCount"}))
        cls.guilds = stats[0]['guilds']
        cls.users = "{:,}".format(stats[0]['users'])

        cls.staff = [x for x in bot.get_guild(671078170874740756).get_role(679647636479148050).members if bot.get_guild(671078170874740756).get_role(674940101801017344) not in x.roles]
        cls.on_leave = [x.id for x in bot.get_guild(671078170874740756).get_role(803366965262549062).members]

        # partners
        partners_list = list(db.partners.find())
        the_partners = []
        for partner in partners_list:
            the_bot = await bot.fetch_user(partner['partner_bot'])
            short_message = partner['short_msg']
            partnered_since = partner['partner_since']
            website = partner['website']
            long_desc = partner['html']
            the_partners.append({'bot': the_bot, 'msg': short_message, 'since': partnered_since, 'website': website, 'html': long_desc})

        cls.partners = the_partners

        # staff apps
        cls.staff_apps = list(db.apps.find())
        cls.staff_open = True if db.apps.find_one({"open": True}) else False

        # api
        tokens = list(db.stats.find({"to_find": '1'}))
        cls.api_token = tokens[0]['token']
        cls.api_client = tokens[0]['client']

        print("Loaded Cache")

    @classmethod
    def get_from_cache(cls: Any, stuff):
        try:
            return getattr(cls, stuff)
        except Exception:
            return 'Not Found'

    @classmethod
    def update_cache(cls, stuff, new_value):
        if hasattr(cls, stuff):
            setattr(cls, stuff, new_value)
