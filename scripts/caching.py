class Cache:
    def __init__(self):

        # users, bot & staff
        self.moksej = None
        self.zenpa = None
        self.duck = None
        self.me = None
        self.staff = []
        self.on_leave = None

        self.guilds = None
        self.users = None

        # partners
        self.partners = []
        self.top_partner = dict()

        # applications
        self.staff_open = False
        self.staff_apps = None

        # site caching (announcements, invite stuff)
        self.announcement = None
        self.announcement_color = None
        self.allow_invite = True
        self.reason = None

        self.testing = None

        # api
        self.api_token = None
        self.api_client = None

    async def load_cache(self, bot, main_bot, db):
        self.moksej = bot.get_guild(671078170874740756).get_member(345457928972533773)
        self.zenpa = bot.get_guild(671078170874740756).get_member(373863656607318018)
        self.duck = bot.get_guild(671078170874740756).get_member(443217277580738571)
        self.me = bot.get_guild(671078170874740756).get_member(667117267405766696)

        stats = list(db.stats.find({"type": "UserGuildCount"}))
        self.guilds = stats[0]['guilds']
        self.users = "{:,}".format(stats[0]['users'])

        self.staff = [x for x in bot.get_guild(671078170874740756).get_role(679647636479148050).members if bot.get_guild(671078170874740756).get_role(674929900674875413) not in x.roles]
        self.on_leave = [x.id for x in bot.get_guild(671078170874740756).get_role(803366965262549062).members]

        # partners
        partners_list = list(db.partners.find())
        the_partners = []
        for partner in partners_list:
            the_bot = await bot.try_user(partner['partner_bot'])
            short_message = partner['short_msg']
            partnered_since = partner['partner_since']
            website = partner['website']
            long_desc = partner['html']
            the_partners.append({'bot': the_bot, 'msg': short_message, 'since': partnered_since, 'website': website, 'html': long_desc})

        self.partners = the_partners

        # staff apps
        self.staff_apps = list(db.apps.find())
        self.staff_open = True if db.apps.find_one({"open": True}) else False

        # api
        tokens = list(db.stats.find({"to_find": '1'}))
        self.api_token = tokens[0]['token']
        self.api_client = tokens[0]['client']

        print("Loaded Cache")

    def get_from_cache(self, stuff):
        try:
            return getattr(self, stuff)
        except Exception:
            return 'Not Found'

    def update_cache(self, stuff, new_value):
        if hasattr(self, stuff):
            setattr(self, stuff, new_value)
