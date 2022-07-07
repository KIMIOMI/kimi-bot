import requests
import json
import os.path

class twitter_util():
    # mainpath = os.getcwd()
    # filename = os.path.join(mainpath, 'data.json')

    with open('./data.json') as f:
        d1 = json.load(f)

    def __init__(self):
        self.bearer_token = self.d1["BEARER_TOKEN"]

    def create_headers(self):
        headers = {"Authorization": "Bearer {}".format(self.bearer_token)}
        return headers

    def create_tweet_lookup_url(self, tweet_id):
        tweet_fields = "tweet.fields=lang,author_id"
        # Tweet fields are adjustable.
        # Options include:
        # attachments, author_id, context_annotations,
        # conversation_id, created_at, entities, geo, id,
        # in_reply_to_user_id, lang, non_public_metrics, organic_metrics,
        # possibly_sensitive, promoted_metrics, public_metrics, referenced_tweets,
        # source, text, and withheld
        query_params = {
            'user.fields': 'id,name,username,created_at,description,public_metrics,verified',
            'tweet.fields': 'lang,author_id',
            'media.fields': 'url'
        }
        # You can adjust ids to include a single Tweets.
        # Or you can add to up to 100 comma-separated IDs
        url = "https://api.twitter.com/2/{}".format(tweet_id)
        return url, query_params

    def create_get_user_url(self, username):
        # Specify the usernames that you want to lookup below
        # You can enter up to 100 comma-separated values.
        # user_fields = "user.fields=description,created_at"
        # User fields are adjustable, options include:
        # created_at, description, entities, id, location, name,
        # pinned_tweet_id, profile_image_url, protected,
        # public_metrics, url, username, verified, and withheld
        url = "https://api.twitter.com/2/users/by/username/{}".format(username)
        query_params = {
            'user.fields': 'id,name,username,created_at,description,public_metrics,verified',
        }
        return url, query_params

    def create_user_timeline_url(self, user_id):
        # Replace with user ID below
        url = "https://api.twitter.com/2/users/{}/tweets".format(user_id)
        query_params = {
            'tweet.fields': 'created_at',
            'user.fields': 'created_at',
            'max_results': 5,
        }
        return url, query_params

    def create_url(self, keyword, start_date, end_date, max_results=10):
        search_url = "https://api.twitter.com/2/tweets/search/all"
        # Change to the endpoint you want to collect data from

        # change params based on the endpoint you are using
        query_params = {'query': keyword,
                        'start_time': start_date,
                        'end_time': end_date,
                        'max_results': max_results,
                        'expansions': 'author_id,in_reply_to_user_id,geo.place_id',
                        'tweet.fields': 'id,text,author_id,in_reply_to_user_id,geo,conversation_id,created_at,lang,public_metrics,referenced_tweets,reply_settings,source',
                        'user.fields': 'id,name,username,created_at,description,public_metrics,verified',
                        'place.fields': 'full_name,id,country,country_code,geo,name,place_type',
                        'next_token': {}}
        return search_url, query_params

    def connect_to_endpoint(self, url, headers, params, next_token=None):
        params['next_token'] = next_token  # params object received from create_url function
        response = requests.get(url, headers=headers, params=params)
        # print("Endpoint Response Code: " + str(response.status_code))
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()
