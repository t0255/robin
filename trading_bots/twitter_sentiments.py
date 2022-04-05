import pandas as pd
import robin_stocks as robinhood
import tweepy

from base import OrderType, TradeBot
from config import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class TradeBotSentimentAnalysis(TradeBot):

    def __init__(self, username, password):
        """Logs user into their Robinhood account."""
        
        super().__init__(username, password)

    def retrieve_tweets(self, ticker, max_count=100):
        """
        Retrieves tweets from Twitter about ticker.

        ticker: A company's ticker symbol as a string
        :param max_count: The maximum number of tweets to retrieve
        :return: A list of strings of the retrieved tweets
        """

        searched_tweets = []

        if not ticker:
            print("ERROR: Parameters cannot have null values.")
            return searched_tweets

        if max_count <= 0:
            print("ERROR: max_count must be a positive number.")
            return searched_tweets

        # Connect to the Twitter API.
        auth = tweepy.AppAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        api = tweepy.API(auth)

        # Retrieve the company name represented by ticker.
        company_name = robinhood.stocks.get_name_by_symbol(ticker)
        query = f"#{company_name} OR ${ticker}"

        # Search for max_counts tweets mentioning the company.
        public_tweets = tweepy.Cursor(api.search_tweets,
                                      q=query,
                                      lang="en",
                                      result_type="recent",
                                      tweet_mode="extended").items(max_count)

        # Extract the text body of each tweet.
        searched_tweets = []

        for tweet in public_tweets:

            try:
                searched_tweets.append(tweet.retweeted_status.full_text)

            # Not a Retweet    
            except AttributeError:
                searched_tweets.append(tweet.full_text)

        return searched_tweets

    def analyze_tweet_sentiments(self, tweets):
        """
        Analyzes the sentiments of each tweet and returns the average
        sentiment.

        :param tweets: A list of strings containing the text from tweets
        :return: The mean of all the sentiment scores from the list of tweets
        """

        if not tweets:
            print("ERROR: Parameters cannot have null values.")
            return 0

        analyzer = SentimentIntensityAnalyzer()

        # Initialize an empty DataFrame.
        column_names = ["tweet", "sentiment_score"]
        tweet_sentiments_df = pd.DataFrame(columns=column_names)

        # Get the sentiment score for each tweet and append the text
        # and sentiment_score into the DataFrame.
        for tweet in tweets:
            score = analyzer.polarity_scores(tweet)["compound"]
            tweet_sentiment = {"tweet": tweet, "sentiment_score": score}
            tweet_sentiments_df = tweet_sentiments_df.append(
                tweet_sentiment, ignore_index=True
            )

        # Calculate the average sentiment score.
        average_sentiment_score = tweet_sentiments_df["sentiment_score"].mean()

        return average_sentiment_score

    def make_order_recommendation(self, ticker):
        """
        Makes an order recommendation based on the sentiment of
        max_count tweets about ticker.

        :param ticker: A company's ticker symbol as a string
        :return: OrderType recommendation
        """

        if not ticker:
            print("ERROR: Parameters cannot have null values.")
            return None

        public_tweets = self.retrieve_tweets(ticker)
        consensus_score = self.analyze_tweet_sentiments(public_tweets)

        # Determine the order recommendation.
        if consensus_score >= 0.05:
            return OrderType.BUY_RECOMMENDATION

        elif consensus_score <= -0.05:
            return OrderType.SELL_RECOMMENDATION

        else:
            return OrderType.HOLD_RECOMMENDATION

