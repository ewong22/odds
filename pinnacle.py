from flask import Flask
from flask_cors import CORS
from selenium.webdriver.common.by import By
from selenium import webdriver 
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta, date
import boto3
from pprint import pprint
from boto3.dynamodb.conditions import Key
import botocore
import pandas as pd
import flask
import os
import time
from flask import send_file
import json
from flask import jsonify


app = Flask(__name__, static_url_path='', static_folder='response-app/src')
CORS(app)


def get_game_odds(game_title, table):
    response = table.query(KeyConditionExpression=Key('Game').eq(game_title))
    odds = response['Items']
    return odds


def add_game(game, time, date, away_odds, home_odds, game_date, game_time, ttl, table):
    table.put_item(
        Item={
            'Game': game,
            'Time': time,
            'Away': away_odds,
            'Home': home_odds,
            'Date': date,
            'Game_date': game_date,
            'Game Time': game_time,
            'ttl': ttl
        }
    )

def convert_date(date):
    num_date = ""
 
    num_date += date[9:11] + "/"

    
    if "JAN" in date:
        num_date += "01"
    if "FEB" in date:
        num_date += "02"
    if "MAR" in date:
        num_date += "03"
    if "APR" in date:
        num_date += "04"
    if "MAY" in date:
        num_date += "05"
    if "JUN" in date:
        num_date +="06"
    if "JUL" in date:
        num_date += "07"
    if "AUG" in date:
        num_date += "08"
    if "SEP" in date:
        num_date += "09"
    if "OCT" in date:
        num_date += "10"
    if "NOV" in date:
        num_date += "11"
    if "DEC" in date:
        num_date += "12"


    num_date += "/" + date[13:17]
    return num_date

def check_date(date):
    if "TODAY" == date:
        today = datetime.now()
        return today.strftime("%d/%m/%Y")
    elif "TOMORROW" == date:
        today = datetime.now()
        tomorrow = today + timedelta(1)
        return tomorrow.strftime("%d/%m/%Y")
    elif "MON" in date:
        return convert_date(date)
    elif "TUE" in date:
        return convert_date(date)
    elif "WED" in date:
        return convert_date(date)
    elif "THU" in date:
        return convert_date(date)
    elif "FRI" in date:
        return convert_date(date)
    elif "SAT" in date:
        return convert_date(date)
    elif "SUN" in date:
        return convert_date(date)
    else:
        return "invalid"


def update_odds(table):
    PATH = "/Users/ethanwong/work/odds/chromedriver/chromedriver"
    driver = webdriver.Chrome(PATH)

    driver.get("https://www.pinnacle.com/en/football/nfl/matchups#period:0")
    info = driver.find_elements_by_xpath("//div[@class='contentBlock square']")

    e = datetime.now()
    date = e.strftime("%d/%m/%Y")
    curr_time =  e.strftime("%I:%M:%S %p")
    ttl = int(time.time()) + 604800
    print(ttl)   


    book = []
    i = 0
    lines = info[0].text.splitlines(0)
    same_date = ""
    #create game dictionaries and store them in book
    
    while i < len(lines)-10:
        #print(lines[i])
        game = {}
        if check_date(lines[i]) != 'invalid':
            game["Game Date"] = check_date(lines[i])
            same_date = check_date(lines[i])
            if "TODAY" in lines[i]:
                i = i + 1
            i = i + 3
        else:
            game["Game Date"] = same_date

        game["Game"] = lines[i] + " @ " + lines[i+1]
        game["Game Time"] = lines[i+2]
        game["Away"] = lines[i+7]
        game["Home"] = lines[i+8]
        game["Date"] = date
        game["Time"] = curr_time
        game["ttl"] = ttl


        book.append(game)
        i = i + 10

    #place all the games in book into dynamodb table
    for game in book:
        add_game(game.get("Game"), game.get("Time"), game.get("Date"), game.get("Away"), game.get("Home"), game.get("Game Date"), game.get("Game Time"), game.get("ttl"), table)


    driver.quit()



@app.route('/get',methods=['GET'])

def home():
    db = boto3.resource('dynamodb', region_name="us-east-1")
    tables = list(db.tables.all())


    #table = dynamo(db)
    #if date.today().weekday() == 1:
    #    table.delete_table()
    #    table.create_table("odds")

   
    
    

    odds = db.Table('odds')
    response = odds.scan()
    items = response['Items']
    games = []
    for item in items: 
        if item.get('Game') not in games:
            games.append(item.get('Game'))


    # game_title = "Baltimore Ravens @ Cleveland Browns"
    # game = get_game_odds(game_title, odds)
    # data = pd.DataFrame(game)
    # file_name = game_title.replace(" ", "") + ".csv"
    # data.to_csv('/Users/ethanwong/pinnacle/' + file_name, index=False)
    
    update_odds(odds)
    #Upload the file
    

    #s3_client = boto3.client('s3')
    #response = s3_client.upload_file(file_name, "bucketfilestorage", game_title + ".csv")
    #os.remove("/Users/ethanwong/pinnacle/" + file_name)

    return  jsonify({
        'ok': True, 
        'msg':'Success',
        'data': games
    })
    
    # '''
    #     <html><body>
    #     Download Baltimore Ravens @ Cleveland Browns. <a href="/home/BaltimoreRavens@ClevelandBrowns">Click me.</a>
    #     </body></html>
    #     '''


@app.route('/home/<game>')
def getCSV(game):
    db = boto3.resource('dynamodb', region_name="us-east-1")
    odds = db.Table('odds')
    game_title = game
    game = get_game_odds(game_title, odds)
    data = pd.DataFrame(game)
    file_name = game_title.replace(" ", "") + ".csv"
    data.to_csv('/Users/ethanwong/pinnacle/' + file_name, index=False)
    return send_file(
        file_name,
    )



if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)

