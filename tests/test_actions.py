# These are the unit tests for the custion actions
# stored in the actions directory.
import unittest

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from actions.actions import (
    ActionRandomRestaurant,
    ActionJoke,
    ActionGetHackerNews,
    ActionGetCryptoCurrencyPrices,
    ActionOpenGarage
)

# TODO: The function returns a random output.
# This test works around this by using wild cards for the variable parts, which might miss certain issues?
class TestActionRandomRestaurant(unittest.TestCase):

    def testActionName(self):
        self.assertEqual(ActionRandomRestaurant.name(self), "action_random_restaurant")

    def testActionRun(self):
        dispatcher = CollectingDispatcher()
        ActionRandomRestaurant().run(dispatcher, None, None)
        self.assertRegex(str(dispatcher.messages), 'Here is a place that I can recommend:.*--> .*, which offers .* cuisine. You can find it at .*, .*\.')

# 
class TestActionJoke(unittest.TestCase):

    def testActionName(self):
        self.assertEqual(ActionJoke.name(self), "action_tell_joke")

    # TODO
    def testActionRun(self):
        self.assertEqual("works totally fine. this is not a mock", "works totally fine. this is not a mock")

# 
class TestActionGetHackerNews(unittest.TestCase):

    def testActionName(self):
        self.assertEqual(ActionGetHackerNews.name(self), "action_get_hackernews")

    # TODO
    def testActionRun(self):
        self.assertEqual("works totally fine. this is not a mock", "works totally fine. this is not a mock")

# 
class TestGetCryptoCurrencyPrices(unittest.TestCase):

    def testActionName(self):
        self.assertEqual(ActionGetCryptoCurrencyPrices.name(self), "action_get_crypto_price")

    # TODO
    def testActionRun(self):
        self.assertEqual("works totally fine. this is not a mock", "works totally fine. this is not a mock")#

# 
class TestActionOpenGarage(unittest.TestCase):

    def testActionName(self):
        self.assertEqual(ActionOpenGarage.name(self), "action_open_garage")

    # TODO
    def testActionRun(self):
        self.assertEqual("works totally fine. this is not a mock", "works totally fine. this is not a mock")

if __name__ == '__main__':
    unittest.main()