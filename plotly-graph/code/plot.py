import pandas as pd
from collections import Counter
from plotly import graph_objs as go

file = "https://cdn.rawgit.com/dtemkin/blog/66b12f0d/data/nba_data.csv"
df = pd.read_csv(file, index_col=0)
subdf = df[df.year>=2010]
teams = set(subdf.away_team)
fig = go.Figure()    
buttons = [{"label": "Select Team: ", "method": "update", 
            "args": [{'visible': [False for tm in teams]}]}]

# games = {}
for team in teams:
    # games.update({team: {"wins": Counter(), 'losses': Counter()}})
    teamwins = []
    teamlosses = []
    
    for row in subdf.index:
        if subdf.loc[row].away_team == team:
            if subdf.loc[row].winner == 'away':
                teamwins.append(subdf.loc[row].home_team)
            else:
                teamlosses.append(subdf.loc[row].home_team)
        elif subdf.loc[row].home_team == team:
            if subdf.loc[row].winner == 'home':
                teamwins.append(subdf.loc[row].away_team)
            else:
                teamlosses.append(subdf.loc[row].away_team)
        else:
            pass
    
    # games[team]['wins'].update(teamwins)
    # games[team]['losses'].update(teamlosses)
    wins_dict = dict(Counter(teamwins))
    losses_dict = dict(Counter(teamlosses))

    
    wins_dict.update({team: 0})
    wins_dict.update({tx: 0 for tx in teams if tx not in wins_dict})
    
    losses_dict.update({team: 1})
    losses_dict.update({tx: 1 for tx in teams if tx not in losses_dict})

    tot_games = {t: wins_dict[t]+losses_dict[t] for t in teams}
    pct_winloss = {t: round((wins_dict[t]-losses_dict[t])/tot_games[t], 4) for t in teams}
    colors = ("#57eb77", "#e6575e")
    win_loss_colors = [(colors[0] if pct_winloss[t] > 0 else colors[1]) for t in pct_winloss]

    trace = go.Bar(x=list(pct_winloss.keys()), y=list(pct_winloss.values()),
                   name=team + " win/loss percent", visible=False, hoverinfo="text",
                   hovertext=[f"{team} VS. {tm1}</br>"
                              f"</br>Wins: {wins_dict[tm1]}"
                              f"</br>Losses: {losses_dict[tm1]}"
                              f"</br>Total:{tot_games[tm1]}"
                              f"</br>Win/Loss Pct: {pct_winloss[tm1]}"
                              for tm1 in teams],
                   marker_color=win_loss_colors)
    
    btnx = {"label": team, 'method': 'update',
            "args": [{'visible': [True if team == tmx else False 
                                  for tmx in teams]}]}
    fig.add_trace(trace)
    
    buttons.append(btnx)

fig.update_layout(
    {"updatemenus":[
        go.layout.Updatemenu(buttons=buttons, direction="down",
                             pad={"r": 5, "t": 0}, showactive=True,
                             xanchor="right", x=1.3, yanchor="top", y=1.10)],
        'title_text': 'NBA Win/Loss Percentage by Team',
        'xaxis': dict(title='Opponent', tickangle=45),
        'yaxis_title_text': 'Win/Loss Percent',
        "width": 740, "height": 750,
        "autosize": True})

config = {"displayModeBar": False}

fig.write_html('plot.html', include_plotlyjs=False, config=config)
fig.show()
