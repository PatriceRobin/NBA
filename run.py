from main import *

player_name = "Stephen Curry"

#plot_court(player_name, team_name="GSW", season_type="Regular Season", season ="2021-22")

data = get_player_data(player_name, team_name="GSW", season_type="Regular Season", season ="2021-22")
from IPython.display import display
with pd.option_context('display.max_columns', None):
    display(shot_df.head())