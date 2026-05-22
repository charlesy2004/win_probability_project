import requests
from pprint import pprint
url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    
response = requests.get(url, timeout=10)
response.raise_for_status()  # Raise an error for bad status codes
data = response.json()
events = data.get('events', [])
formatted_games = []
for event in events:
    competition = event['competitions'][0]
    competitors = competition['competitors']

    home_team = next(team for team in competitors if team['homeAway'] == 'home')
    away_team = next(team for team in competitors if team['homeAway'] == 'away')

    status_type = event['status']['type']
    odds_list = competition.get('odds', [])
    odds = odds_list[0] if odds_list else ()

    formatted_games.append(
        {
            "game_id": event['id'],
            "name": event['name'],
            "home_team": home_team['team']['displayName'],
            "away_team": away_team['team']['displayName'],
            "home_score": home_team.get('score', 'N/A'),
            "away_score": away_team.get('score', 'N/A'),
            "status": status_type['description'],
            "odds": odds.get('details', 'N/A') if odds else 'N/A'
        }
    )
