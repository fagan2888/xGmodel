import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from scipy.misc import imread

np.seterr(over='ignore', under='ignore')

def sigmoid(x):
    return 1/(1+np.exp(-x))

def myprob(distance, angle):
    x = distance*np.power((angle+1), 0.5)
    result = 1.0646383882981121*np.exp(-0.0247111*x)
    return result

def nn_prob(shot_data):
    theta1 = np.load('./Neural Net/xG_theta1.npy')
    theta2 = np.load('./Neural Net/xG_theta2.npy')
    X_cv = shot_data.as_matrix(columns=['x', 'y', 'Header',
                                        'Distance', 'Angle'])

    X_cv = np.c_[np.ones(X_cv.shape[0]), X_cv]

    m = X_cv.shape[0]

    a_1 = X_cv.T
    z_2 = np.dot(theta1, a_1)
    a_2 = sigmoid(z_2)
    # WILL ADD A BIAS UNIT SOON
    z_3 = np.dot(theta2, a_2)
    a_3 = sigmoid(z_3)
    h_theta = a_3
    return h_theta.T

def tidy_and_format_data(shot_data):
    '''
    takes shot data, adds distance, angle, colour and a probability
    :param shot_data:
    :return:
    '''
    for index, row in shot_data.iterrows():
        if row['x'] > 240:
            shot_data.set_value(index, 'x', 480 - row['x'])

    shot_data['y'] = shot_data['y'] - 366/2
    shot_data['y'] = shot_data['y'] * -1
    # calculate the angle and the distance from the goal
    shot_data['Angle'] = np.arctan((np.absolute(shot_data['y'])/shot_data['x']))
    shot_data['Distance'] = np.sqrt(shot_data['y']*shot_data['y'] + shot_data['x']*shot_data['x'])

    # assign colours and numbers based on whether the shots were scored or missed
    for index, row in shot_data.iterrows():
        if row['Scored'] == 'Scored':
            shot_data.set_value(index, 'Colour', 'b')
            shot_data.set_value(index, 'ScoredBinary', 1)
        else:
            shot_data.set_value(index, 'Colour', 'r')
            shot_data.set_value(index, 'ScoredBinary', 0)

    shot_data['Proba_exp'] = nn_prob(shot_data)

    return shot_data

def plot_data(shot_data, home_team, away_team, match_date):
    shot_data = tidy_and_format_data(shot_data)  # add xG values to each shot and a colour etc
    img = imread('./xG Plots/background3.jpg')
    shot_data['Colour'] = shot_data['Colour'].replace({'r': 'white', 'b': 'magenta'})
    shot_data['y'] = -1 * shot_data['y']
    xG_home = shot_data.loc[shot_data['Team'] == home_team, 'Proba_exp'].sum()
    xG_away = shot_data.loc[shot_data['Team'] == away_team, 'Proba_exp'].sum()

    home_goals, away_goals = calc_goals_scored(shot_data, home_team, away_team)

    for index, row in shot_data.iterrows():
        if row['Team'] == away_team:
            shot_data.set_value(index, 'x', 480 - row['x'])

    shot_data.sort_values(by=['Scored'], ascending=True, inplace=True)

    plt.scatter(shot_data[shot_data['Scored']=='Missed']['x'], shot_data[shot_data['Scored']=='Missed']['y'],
                s=shot_data[shot_data['Scored']=='Missed']['Proba_exp'] * 400, facecolors=shot_data[shot_data['Scored']=='Missed']['Colour'],
                alpha=0.6, edgecolors='black', linewidth=0.4)
    plt.scatter(shot_data[shot_data['Scored'] == 'Scored']['x'], shot_data[shot_data['Scored'] == 'Scored']['y'],
                s=shot_data[shot_data['Scored'] == 'Scored']['Proba_exp'] * 400,
                facecolors=shot_data[shot_data['Scored'] == 'Scored']['Colour'],
                alpha=1.0, edgecolors='black', linewidth=0.4)
    plt.ylim(-366 / 2, 366 / 2)
    plt.xlim(-10, 490)
    plt.imshow(img, zorder=0, extent=[0, 480, -366 / 2, 366 / 2])
    text = plt.text(240, 120, home_team + ' vs. ' + away_team + '\n'
                    + 'Score: ' + str(home_goals) + '  -  ' + str(away_goals) + '\n'
                    + 'xG: ' + str(np.round(xG_home, 2)) + '  -  ' + str(np.round(xG_away, 2)),
                    horizontalalignment='center',
                    color='white', alpha=0.8, fontsize=10, fontweight='bold')
    text.set_path_effects([path_effects.Stroke(linewidth=1, foreground='black'),
                           path_effects.Normal()])

    plt.subplots_adjust(left=0.01, bottom=0.01, right=0.99, top=0.99,
                        wspace=None, hspace=None)
    plt.axis('off')
    plt.savefig('./xG Plots/17-18/' + home_team + '-' + away_team + ' ' + match_date + '.png',
                bbox_inches=0, pad_inches=0)

def calc_goals_scored(shot_data, home_team, away_team):

    shot_data_team = shot_data[shot_data['Team']==home_team]
    try:
        home_goals = shot_data_team['Scored'].value_counts()['Scored']
    except KeyError:
        home_goals = 0

    shot_data_team = shot_data[shot_data['Team'] == away_team]
    try:
        away_goals = shot_data_team['Scored'].value_counts()['Scored']
    except KeyError:
        away_goals = 0

    return home_goals, away_goals

data = pd.read_csv('./All shots from 17-18/E0/shots.csv', index_col=0)
football_data = pd.read_csv('./Football-data.co.uk/E0/17-18.csv')
mappings = pd.read_csv('./All shots from 17-18/E0/mappings.csv', index_col=1, header=None)
data.replace(mappings[0], inplace=True)
img = imread('./xG Plots/background.jpg')

home_team = input('Input home team: ')
away_team = input('Input away team: ')

football_data['Date'] = pd.to_datetime(football_data['Date'])

for index, row in football_data.iterrows():
    if row['HomeTeam'] == home_team and row['AwayTeam'] == away_team:
        home_goals = row['FTHG']
        away_goals = row['FTAG']
        date = row['Date']
        match_no = index

data = data[data['Match No'] == match_no]

plot_data(data, home_team, away_team, date.strftime('%Y-%m-%d'))

