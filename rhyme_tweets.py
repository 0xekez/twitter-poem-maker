import pronouncing
import tweepy
import json
import requests
import random
import re
from num2words import num2words

# check if two words rhyme
def rhymes(a, b):
    a_last_word = a.split()[-1].split('-')[-1]
    b_last_word = b.split()[-1].split('-')[-1]

    if (a_last_word.lower() in pronouncing.rhymes(b_last_word)):
        return True

    return False

def starts_with(str, start):
    return str[0:len(start)] == start

def is_number(num):
    try:
        float(num)
        return True

    except ValueError:
        return False

# https://www.sitepoint.com/community/t/printing-the-number-of-syllables-in-a-word/206809
def num_syllables(word):
    word = word.lower()

    # count the syllables in the word.
    syllables = 0
    for i in range(len(word)):
        # if the first letter in the word is a vowel then it is a syllable.
        if i == 0 and word[i] in "aeiouy" :
            syllables += 1

        # else if the previous letter is not a vowel.
        elif word[i - 1] not in "aeiouy" :
            # if it is no the last letter in the word and it is a vowel.
            if i < len(word) - 1 and word[i] in "aeiouy" :
                syllables += 1

            # else if it is the last letter and it is a vowel that is not e.
            elif i == len(word) - 1 and word[i] in "aiouy" :
                syllables += 1

    # adjust syllables from 0 to 1.
    if len(word) > 0 and syllables == 0 :
        syllables = 1

    return syllables

def cleanup_text(text, exclusions = []):
    # remove exclusions
    text = text.lower()
    for e in exclusions:
        text = text.replace(e, '')

    # remove punc except '
    text = re.sub(r"[^a-z0-9- ]",'', text)

    # replace numbers with words
    words = text.split()
    for i in range(len(words)):
        if is_number(words[i]):
            words[i] = num2words(int(words[i]))
    return ' '.join(word for word in words)

def check_tweet(text, exclusions = []):
    lower = text.lower()
    # remove newline
    lower = lower.replace('\n', ' ')

    # dont include retweets or @ mentions
    if(starts_with(lower, 'rt') or starts_with(lower, '@') or starts_with(lower, '.')):
        return False

    # throw out tweets with links
    if('http' in lower):
        return False

    lower = cleanup_text(lower, exclusions)

    # make sure things stay reasonably short
    if num_syllables(lower) > 16:
        return False

    # check to be sure that the last word can be rhymed to
    last_word = lower.split()[-1].split('-')[-1]
    if len(pronouncing.rhymes(last_word)) == 0:
        return False

    return True

# returns new verses and updated list of tweets
def make_poem(s):
    added = []
    for i in range(len(s)-1):
        start = s[i]
        for tweet in s[i:]:
            if rhymes(start, tweet):
                add = start + '\n' + tweet + '\n'
                # make sure we don't add any duplicates
                if add not in added:
                    # print('adding ""{}"" and ""{}""'.format(start, tweet))
                    added.append(add)
    return ''.join(line for line in added)


# tweets per batch
n_tweets = 1000
tweets = []
poem_finished = False
poem = ''

# load twitter auth
with open('keys.json', encoding='utf-8') as data:
    keys = json.loads(data.read())

auth = tweepy.OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
auth.set_access_token(keys['access_token'], keys['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True,wait_on_rate_limit_notify=True)

# get a list of every english word
word_site = "http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain"
response = requests.get(word_site)
eng_words = response.content.splitlines()
print('GOT english dict')

# load text emojis
with open('smileys.txt', encoding='utf-8') as f:
    smileys = f.readlines()
    smileys = [s.strip().lower() for s in smileys]
    print("GOT text emojis")

while not poem_finished:
    # download tweet batch
    # writing to text file is done so that between it breaking we still store tweets
    with open('all_tweets.txt','a') as f:
        for tweet in tweepy.Cursor(api.search, q=random.choice(eng_words), lang='en').items(n_tweets):
            if check_tweet(tweet.text, smileys):
                f.write(cleanup_text(tweet.text, smileys)+'\n')
    with open('all_tweets.txt') as f:
        tweets = f.readlines()
        tweets = [tweet.strip() for tweet in tweets]
    print("{} tweets in database".format(len(tweets)))
    # try to make poem
    poem = make_poem(tweets)
    print(poem)
