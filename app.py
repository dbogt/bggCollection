# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 23:34:24 2020

@author: Bogdan Tudose
"""

#%% Import Packages
import pandas as pd
import streamlit as st
import altair as alt
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

#%% Import Data and Functions
def make_clickable(link, text):
    # target _blank to open new window
    # extract clickable text to display for your link
    # text = link.split('=')[1]
    # text = "BGG Link"
    return f'<a target="_blank" href="{link}">{text}</a>'

@st.cache
def load_data(userN):
    df = pd.read_json("https://bgg-json.azurewebsites.net/collection/" + userN)
    df['Desc'] = df.apply(lambda x:x['name'] + ";  " +
                      "Plrs: " + str(x['minPlayers']) + ' - ' + str(x['maxPlayers']) + ';  ' +
                      "Time: "+ str(x['playingTime']) + ';  ' +
                       x['userComment'], axis=1)
    df['imgLink'] = df['image'].apply(make_clickable, args=('Img Link',))
    df['bggLink'] = df.apply(lambda x: "https://boardgamegeek.com/boardgame/" + str(x['gameId']), axis=1)
    df['bggLink'] = df['bggLink'].apply(make_clickable, args=('BGG Link',))
    
    return df

def fnAccessSite(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, 'xml') #parsing as xml
    return soup

@st.cache
def getUserInfo(user):
    url = "https://www.boardgamegeek.com/xmlapi2/user?name={}".format(user)
    bggLink = "https://boardgamegeek.com/user/" + user
    xmlObj = fnAccessSite(url)
    fName = xmlObj.find("firstname").get("value")
    lName = xmlObj.find("lastname").get("value")
    avatar = xmlObj.find("avatarlink").get("value")  
    state = xmlObj.find("stateorprovince").get("value")  
    country = xmlObj.find("country").get("value")  
    location =  (state + ", " + country).strip(", ")
    yearReg = xmlObj.find("yearregistered").get('value')    
    userDict = {"First":fName, "Last":lName, "Avatar":avatar,"Location":location,"Year":yearReg,"URL":bggLink}
    return userDict

#%% Grab BGG Data
user_input = st.text_input("Enter user name here", "canadude")
df = load_data(user_input)
# df = load_data("canadude")
# userInfo = getUserInfo("Hermokrates")
userInfo = getUserInfo(user_input)

userText = """+ User: **{}**
+ Name: **{} {}**
+ Location: {}
+ Year Registered: {}
+ BGG Link: {}
""".format(user_input,userInfo['First'],userInfo['Last'],userInfo['Location'],userInfo['Year'],userInfo['URL'])

if len(userInfo['Avatar']) > 5:
    avatar = """
    ![Avatar]({})
    """.format(userInfo['Avatar'])
else:
    avatar = ""
st.markdown(userText)
st.markdown(avatar)



#%%


allComments = set(", ".join(df['userComment'].unique()).split(","))
games = set(x.strip() for x in allComments)
gameTypes =[x for x in games]
gameTypes.remove("")
gameTypes.sort()
# gameTypes = ['Adult', 'Betting', 'Bluffing', 'Card', 'Children', 'City Building', 'Competitive', 'Cooperative', 'Deck Building', 'Dexterity', 'Dice Game', 'Drawing', 'Euro', 'Party', 'Puzzle', 'Word', 'Worker placement']

# st.image("http://danawerpny.com/game-directory/img/logo_agame.jpeg", width=200)



#%% Side Bar Controls

gamesSearch = st.sidebar.multiselect('What game are you looking for?',df['name'])
gameFilter = "|".join(gamesSearch)

options = st.sidebar.multiselect('What type of game are you looking for?',gameTypes)
filterOptions = "|".join(options)



# df2 = df[df['userComment'].str.contains("Dice|Adult", regex=True)]
#Filter for game type
df2 = df[df['name'].str.contains(gameFilter, regex=True)]
df2 = df2[df2['userComment'].str.contains(filterOptions, regex=True)]

#Filter for time taken
timeFilter = st.sidebar.checkbox("Filter for playing time")
if timeFilter:
    timeMin, timeMax = st.sidebar.slider("Playing time (minutes)",0,int(df['playingTime'].max()),(0,120))
    df2 = df2[(df2['playingTime']>=timeMin) & (df2['playingTime']<=timeMax)]
else:
    df2 = df2.copy()

#Filter for num of players
numPlFilter = st.sidebar.checkbox("Filter for # of players")
if numPlFilter:
    # streamlit.slider(element, label, min_value=None, max_value=None, value=None, step=None, format=None, key=None)
    minPl, maxPl = st.sidebar.slider('Select number of players', 1, 12, (2, 4))
    df2 = df2[(df2['maxPlayers']>=maxPl) & (df2['minPlayers']<=minPl)]
else:    
    df2 = df2.copy()


# ownedRadio = st.sidebar.checkbox("Only Owned Games")
ownedRadio = st.sidebar.radio("Ownership criteria:", ['All','Only Owned Games','Owned + Prev Owned'])

if ownedRadio == 'Only Owned Games':
    df2 = df2[df2['owned']==True]
elif ownedRadio == "Owned + Prev Owned":
    df2 = df2[(df2['owned']==True) | (df2['previousOwned']==True) ]

images = list(df2['image'])
names = list(df2['Desc'])

summaryDF = df2[['name','numPlays','minPlayers','maxPlayers','playingTime','yearPublished','averageRating','userComment']]
summaryDF = summaryDF.reset_index(drop=True)
selection = st.sidebar.radio("Go to", ['Game Pics','Table','Num Plays','Wall of Shame'])

playsDF = df2[['name','numPlays']]
playsDF.sort_values(['numPlays','name'], ascending=[False,True], inplace=True)
playsDF['counts'] = playsDF.apply(lambda x: (playsDF['numPlays'] >= x['numPlays']).sum(), axis=1)
playsDF['min'] = playsDF[['numPlays','counts']].min(axis=1)
hindex = playsDF['min'].max()

# playsDF.set_index(['name'],inplace=True)
# hIndex = [15] * playsDF.shape[0]

neverPlayedDF = df[(df['numPlays']==0) & (df['owned']==True)]
images2 = list(neverPlayedDF['image'])
names2 = list(neverPlayedDF['Desc'])
 

if selection == "Game Pics":
    st.markdown("<h1 style='text-align: center; color: orange;'>Game Collection</h1>", unsafe_allow_html=True)
    st.write("Results:" + str(len(images)))
    st.write([x for x in images if x==''])
    st.image(images, width=150, caption=names)
elif selection == "Wall of Shame":
    st.markdown("<h1 style='text-align: center; color: orange;'>Owned Games Never Played</h1>", unsafe_allow_html=True)
    st.write("Results:" + str(len(images2)))
    st.image(images2, width=150, caption=names2)
elif selection == "Num Plays":
    minPlays = int(st.text_input("Enter minimum # of plays", 0))
    playsDF = playsDF[playsDF['numPlays']>=minPlays]
    st.write("Results: " + str(playsDF.shape[0]))
    playsDF.reset_index(inplace=True, drop=True)
    playsDF
    st.header("Number of Plays by Game")
    st.write("H-Index: " + str(hindex))
    hOrV = st.radio("Chart Orientation",['Vertical','Horizontal'])
    if hOrV == 'Horizontal':
        barGraph = alt.Chart(playsDF[playsDF['numPlays']>0]).mark_bar().encode(
            x=alt.X('name', title="Boardgame",sort=None),
            y=alt.Y('numPlays',title="# of Plays") )
        playsDF['hIndex'] = hindex
        rule = alt.Chart(playsDF).mark_rule(color='red').encode(y='hIndex')
        text = barGraph.mark_text(align='center', baseline='middle',
                              dy=-10  # Nudges text to right so it doesn't appear on top of the bar
                              ).encode(
                                  text='numPlays')
    else:
        barGraph = alt.Chart(playsDF[playsDF['numPlays']>0]).mark_bar().encode(
            y=alt.Y('name', title="Boardgame",sort=None),
            x=alt.X('numPlays',title="# of Plays") )
        playsDF['hIndex'] = hindex
        rule = alt.Chart(playsDF).mark_rule(color='red').encode(x='hIndex')
        text = barGraph.mark_text(align='left', baseline='middle',
                              dx=3  # Nudges text to right so it doesn't appear on top of the bar
                              ).encode(
                                  text='numPlays')
        
    st.write((barGraph + text + rule).properties(width=600))
else:
    st.write("Results: " + str(summaryDF.shape[0]))
    summaryDF
    clickDF = df2[['gameId','name','imgLink','bggLink','numPlays']].copy()
    clickDF = clickDF.to_html(escape=False)

# link is the column with hyperlinks
    st.write(clickDF, unsafe_allow_html=True)
