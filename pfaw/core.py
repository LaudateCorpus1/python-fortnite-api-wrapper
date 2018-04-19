from . import constants
from . import objects
import requests


class Fortnite:
    def __init__(self, fortnite_token, launcher_token, password, email):
        password_response = requests.post(constants.token, headers={'Authorization': 'basic {}'.format(launcher_token)},
                                          data={'grant_type': 'password', 'username': '{}'.format(email),
                                                'password': '{}'.format(password), 'includePerms': True}).json()
        access_token = password_response.get('access_token')

        exchange_response = requests.get(constants.exchange,
                                         headers={'Authorization': 'bearer {}'.format(access_token)}).json()
        code = exchange_response.get('code')

        token_response = requests.post(constants.token, headers={'Authorization': 'basic {}'.format(fortnite_token)},
                                       data={'grant_type': 'exchange_code', 'exchange_code': '{}'.format(code),
                                             'includePerms': True, 'token_type': 'egl'}).json()

        self.access_token = token_response.get('access_token')
        self.refresh_token = token_response.get('refresh_token')
        self.expires_at = token_response.get('expires_at')
        self.session = Session(self.access_token)

    def player(self, username):
        """Return object containing player name and id"""
        response = self.session.get(constants.player.format(username))
        return objects.Player(response)

    def battle_royale_stats(self, username, platform):
        """Return object containing Battle Royale stats"""
        player_id = self.player(username).id
        response = self.session.get(constants.battle_royale.format(player_id))
        return objects.BattleRoyale(response=response, platform=platform)

    def friends(self, username):
        """Return list of player ids. This method only works for the authenticated account."""
        player_id = self.player(username).id
        response = self.session.get(constants.friends.format(player_id))
        return [friend.get('accountId') for friend in response]

    def store(self, rw=-1):
        """Return current store items. This method only works for the authenticated account."""
        response = self.session.get(constants.store.format(rw))
        return objects.Store(response)

    def leaderboard(self, count=50, platform=constants.Platform.pc, mode=constants.Mode.solo):
        """Return list of leaderboard objects. Object attributes include id, name, rank, and value."""
        params = {'ownertype': '1', 'itemsPerPage': count}
        leaderboard_response = self.session.post(endpoint=constants.leaderboard.format(platform, mode), params=params)
        for entry in leaderboard_response.get('entries'):
            for key, value in entry.items():
                if key == 'accountId':
                    entry[key] = value.replace('-', '')
        account_ids = '&accountId='.join([entry.get('accountId') for entry in leaderboard_response.get('entries')])
        account_response = self.session.get(endpoint=constants.account.format(account_ids))
        players = []
        for player in leaderboard_response.get('entries'):
            for account in account_response:
                if player.get('accountId') == account.get('id'):
                    players.append({'id': player.get('accountId'), 'name': account.get('displayName'),
                                    'value': player.get('value'), 'rank': player.get('rank')})
        return [objects.Leaderboard(player) for player in players]

    @staticmethod
    def news():
        """Get the current news on fortnite."""
        response = requests.get(constants.news, headers={'Accept-Language': 'en'})
        return objects.News(response=response.json())

    @staticmethod
    def server_status():
        """Check the status of the Fortnite servers. Returns True if up and False if down."""
        response = requests.get(constants.status)
        if response.json()[0]['status'] == 'UP':
            return True
        else:
            return False

    @staticmethod
    def patch_notes(posts_per_page=5, offset=0, locale='en-US', category='patch notes'):
        """Get a list of recent patch notes for fortnite. Can return other blogs from epicgames.com"""
        params = {'category': category, 'postsPerPage': posts_per_page, 'offset': offset, 'locale': locale}
        response = requests.get(constants.patch_notes, params=params)
        return objects.PatchNotes(status=response.status_code, response=response.json())


class Session:
    def __init__(self, access_token):
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'bearer {}'.format(access_token)})

    def get(self, endpoint, params=None):
        if params:
            response = self.session.get(endpoint, params=params)
        else:
            response = self.session.get(endpoint)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def post(self, endpoint, params=None):
        if params:
            response = self.session.post(endpoint, params=params)
        else:
            response = self.session.post(endpoint)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()
