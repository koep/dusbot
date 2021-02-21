import requests
import json
import random
import os

from rasa_sdk import Action # https://github.com/RasaHQ/rasa-sdk/blob/master/rasa_sdk/interfaces.py#L308
from rasa_sdk.events import SlotSet # https://github.com/RasaHQ/rasa-sdk/blob/master/rasa_sdk/events.py#L44

# Returns a joke from the Chuck Norris API
class ActionJoke(Action):
    def name(self):
        return "action_tell_joke"

    def run(self, dispatcher, tracker, domain):
        r = requests.get('http://api.chucknorris.io/jokes/random')
        if r.status_code == 200:
            dispatcher.utter_message(str(r.json()['value']))
            return []
        else:
            dispatcher.utter_message("Something went wrong when contacting the joke API. Sorry about that.")
            return []

# Returns the headline and url of the current top 5 Hacker News posts
class ActionGetHackerNews(Action):
    def name(self):
        return "action_get_hackernews"

    def run(self, dispatcher, tracker, domain):
        r = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
        if r.status_code == 200:
            limit = 0
            message = 'Here are the current top 5 posts from Hacker News:\n'
            for postid in r.json():
                # Can we make this more efficient, as in send requests concurrently?
                if limit < 5:
                    r = requests.get('https://hacker-news.firebaseio.com/v0/item/' + str(postid) + '.json')
                    if r.status_code == 200:
                        message += "--> "
                        message += str(r.json()["title"])
                        message += " ("
                        message += str(r.json()["url"])
                        message += ")\n"
                        limit += 1
                    else:
                        dispatcher.utter_message("Something went wrong when contacting the Hacker News API. Sorry about that.")
                        return []
            dispatcher.utter_message(message)
            return []
        else:
            dispatcher.utter_message("Something went wrong when contacting the Hacker News API. Sorry about that.")
            return []

# Randomly returns a random restaurant and it's details from the local 'database'
class ActionRandomRestaurant(Action):
    def name(self):
        return "action_random_restaurant"

    def run(self, dispatcher, tracker, domain):
        with open('actions/data/restaurants_dusseldorf.json', 'r') as db:
            restaurants = db.read()
        data = json.loads(restaurants)
        message = 'Here is a place that I can recommend:\n'
        for x in range(0, 1): # TODO: Might extend to more recommendations, but I have to make sure that restaurants don't show up twice.
            restaurantID = random.randint(0,len(data["restaurants"])-1)
            message += "--> "
            message += data["restaurants"][restaurantID]["name"]
            message += ", which offers "
            message += data["restaurants"][restaurantID]["cuisine"]
            message += " cuisine. You can find it at "
            message += data["restaurants"][restaurantID]["address"]
            message += ".\n"
        dispatcher.utter_message(message)
        return []

# Returns the current value (in EUR) of the cryptocurrencies listed in cryptocurrencies.json
class ActionGetCryptoCurrencyPrices(Action):
    def name(self):
        return "action_get_crypto_price"

    def run(self, dispatcher, tracker, domain):
        with open('actions/data/cryptocurrencies.json', 'r') as db:
             currencies = db.read()
        data = json.loads(currencies)
        if "CRYPTOCOMPARE_APIKEY" in os.environ:
            apikey = os.getenv('CRYPTOCOMPARE_APIKEY') # the action-server needs to know about this
            message = 'I can\'t tell you if you should buy the dip or hodl. But maybe this helps:\n'
            # TODO: Can we make this more efficient, as in send requests concurrently?
            for x in range(0, len(data["cryptocurrencies"])): # loop through the "database"
                r = requests.get('https://min-api.cryptocompare.com/data/price?fsym=' + data["cryptocurrencies"][x]["shortname"] + '&tsyms=EUR&api_key=' + str(apikey))
                if r.status_code == 200:
                    message += "--> "
                    message += data["cryptocurrencies"][x]["name"]
                    message += " is currently worth "
                    message += str(r.json()["EUR"])
                    message += " Euros.\n"
                else:
                    dispatcher.utter_message("Something went wrong when contacting the Cryptocompare API. Sorry about that.")
                    return []
        else:
            dispatcher.utter_message("Please tell you admin to get an API key from cryptocompare.com and set it in the CRYPTOCOMPARE_APIKEY environment variable in the action-server container. Otherwise I might get rate limited and can't get you what you need.")
            return []
        dispatcher.utter_message(message)
        return []

# Interacts with the garage door of the Duesseldorf Office
class ActionOpenGarage(Action):
    def name(self):
        return "action_open_garage"

    def run(self, dispatcher, tracker, domain):
        if "DUSGARAGE_CREDENTIALS" in os.environ:
            credentials = os.getenv('DUSGARAGE_CREDENTIALS')
            message =''
            # TODO: We probably shouldn't hard-code URLs :-)
            r = requests.get('http://' + str(credentials) + '@rhdus.freedns.io:8000/dus/garagetest/value')
            if r.status_code == 200:
                r = requests.get('http://' + str(credentials) + '@rhdus.freedns.io:8000/dus/garagetest/value/1')
                message += "Done! You should be able to enter the garage momentarily. Please only use the parking space that you have previously booked via http://dusgarage.openshift.me/"
            else:
                dispatcher.utter_message("Unfortunately I'm unable to contact the Duesseldorf garage's backend. I won't be able to open sesame for you today.")
                return []
        else:
            dispatcher.utter_message("Please tell your admin to provide the Duesseldorf garage credentials via the DUSGARAGE_CREDENTIALS environment variable in the action-server container.")
            return []
        dispatcher.utter_message(message)
        return []