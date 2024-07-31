import tweepy

def twitter_auth ():
    
    auth = tweepy.OAuthHandler('2bqgyafUPQSSRDB9IFLN1I7Ah','Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24')
    api = tweepy.API(auth)


def set_twitter_tokens (oauth_token, oauth_token_secret, access_token):

    auth = twitter_auth()
    
    # auth.request_token = {'oauth_token': request.session.get('request_token'),
    #                       'oauth_token_secret': request.session.get('oauth_verifier')}

    auth.request_token = {'oauth_token': oauth_token,
                          'oauth_token_secret': oauth_token_secret}

    auth.set_access_token(access_token[0], access_token[1])
    
    return auth
                