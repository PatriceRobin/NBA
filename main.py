import bs4 as bs4
import requests
import pandas as pd
import re
import shutil
import os
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import players, teams


def load_data(year):
    url = "https://www.basketball-reference.com/leagues/NBA_" + str(year) + "_per_game.html"
    html = pd.read_html(url, header = 0)
    df = html[0]
    raw = df.drop(df[df.Age == 'Age'].index) # Deletes repeating headers in content
    raw = raw.fillna(0)
    playerstats = raw.drop(['Rk'], axis=1)
    return (playerstats,url)

def get_player_image(player_name):
    url = "https://www.basketball-reference.com/players/" + player_name.split()[1][:1].lower()
    res = requests.get(url)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    link = soup.find("a", string=player_name)
    ref = link.get('href')
    player_url = "https://www.basketball-reference.com/" + str(ref)

    r = requests.get(player_url)
    player_soup = bs4.BeautifulSoup(r.content, 'html.parser')
    player_link = player_soup.find(alt=re.compile("^Photo of"))
    image_url = player_link.get('src')

    if not os.path.exists('images'):
        os.makedirs('images')

    img_comps = "./images/", player_name.replace(" ", ""), ".jpg"
    save_url = "".join(img_comps)

    res = requests.get(image_url, stream = True)

    if res.status_code == 200:
        with open(save_url, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        print('Image successfully Downloaded: ', save_url)
    else:
        print('%s image could not be retrieved' % player_name)


def get_player_id(player_name):
    player_dict = players.get_players()

    player_id = [player for player in player_dict if player['full_name'] == player_name][0].get('id')
    return(player_id)

def get_team_id(team_name):
    teams_dict = teams.get_teams()
    if len(team_name) == 3:
        team_id = [x for x in teams_dict if x['abbreviation'] == team_name.upper()][0].get('id')
    else:
        team_id = [x for x in teams_dict if x['full_name'] == team_name][0].get('id')
    return team_id


def create_court(ax, color):
    # Short corner 3PT lines
    ax.plot([-220, -220], [0, 140], linewidth=2, color=color)
    ax.plot([220, 220], [0, 140], linewidth=2, color=color)

    # 3PT Arc
    ax.add_artist(mpl.patches.Arc((0, 140), 440, 315, theta1=0, theta2=180, facecolor='none', edgecolor=color, lw=2))

    # Lane and Key
    ax.plot([-80, -80], [0, 190], linewidth=2, color=color)
    ax.plot([80, 80], [0, 190], linewidth=2, color=color)
    ax.plot([-60, -60], [0, 190], linewidth=2, color=color)
    ax.plot([60, 60], [0, 190], linewidth=2, color=color)
    ax.plot([-80, 80], [190, 190], linewidth=2, color=color)
    ax.add_artist(mpl.patches.Circle((0, 190), 60, facecolor='none', edgecolor=color, lw=2))

    # Rim
    ax.add_artist(mpl.patches.Circle((0, 60), 15, facecolor='none', edgecolor=color, lw=2))

    # Backboard
    ax.plot([-30, 30], [40, 40], linewidth=2, color=color)

    # Remove ticks
    ax.set_xticks([])
    ax.set_yticks([])

    # Set axis limits
    ax.set_xlim(-250, 250)
    ax.set_ylim(0, 470)

    return ax

def get_player_data(player_name, team_name, season_type, **kwargs):
    if "season" in kwargs:
        season = kwargs.get("season")
    else:
        season = 0

    if "context_measure" in kwargs:
        context_measure = kwargs.get("context_measure")
    else:
        context_measure = "PTS"
    shot_json = shotchartdetail.ShotChartDetail(
                team_id = get_team_id(team_name),
                player_id = get_player_id(player_name),
                context_measure_simple = context_measure,
                season_nullable = season,
                season_type_all_star = season_type)

    shot_data = json.loads(shot_json.get_json())

    relevant_data = shot_data['resultSets'][0]
    headers = relevant_data['headers']
    rows = relevant_data['rowSet']

    # Create pandas DataFrame
    player_data = pd.DataFrame(rows)
    player_data.columns = headers

    return player_data

def plot_court(player_name, team_name, season_type, **kwargs):
    player_data = get_player_data(player_name, team_name, season_type, **kwargs)

    mpl.rcParams['font.size'] = 18
    mpl.rcParams['axes.linewidth'] = 2
    # Create figure and axes
    fig = plt.figure(figsize=(4, 3.76))
    ax = fig.add_axes([0, 0, 1, 1])

    # Draw court
    ax = create_court(ax, 'black')

    # Plot hexbin of shots
    ax.hexbin(player_data['LOC_X'], player_data['LOC_Y'] + 60, gridsize=(30, 30), extent=(-300, 300, 0, 940), bins='log',
              cmap='Blues')

    # Annotate player name and season
    if "season" in kwargs:
        season = kwargs.get("season")
    else:
        season = "all season"
    plot_text = "%s\n%s %s" % (player_name, season, season_type)
    ax.text(0, 1.05, plot_text, transform=ax.transAxes, ha='left', va='baseline')

    # Save and show figure
    #plt.savefig('ShotChart.png', dpi=300, bbox_inches='tight')
    plt.show()


