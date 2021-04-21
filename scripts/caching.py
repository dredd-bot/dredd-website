class Cache:
    def __init__(self):
        self.moksej = None
        self.zenpa = None
        self.duck = None
        self.me = None
        self.staff = []

        self.partners = list()
        self.top_partner = dict()

    async def load_cache(self, bot):
        self.moksej = bot.get_guild(671078170874740756).get_member(345457928972533773)
        self.zenpa = bot.get_guild(671078170874740756).get_member(373863656607318018)
        self.duck = bot.get_guild(671078170874740756).get_member(443217277580738571)
        self.me = bot.get_guild(671078170874740756).get_member(667117267405766696)

        self.staff = [x for x in bot.get_guild(671078170874740756).get_role(679647636479148050).members if bot.get_guild(671078170874740756).get_role(674929900674875413) not in x.roles]
        print("Loaded Cache")

    def get_from_cache(self, stuff):
        return getattr(self, stuff)
