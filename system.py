# -*- coding: utf-8 -*-

import sys
import ast
import os
import pprint
import operator
import re
from math import log10
import codecs
from itertools import izip
from urllib2 import Request, urlopen, URLError
from TwitterAPI import TwitterAPI
import json
from textstat.textstat import textstat
import operator

from get_tweets import process_tweet

#Twitter Application keys
api = TwitterAPI('6hckfkSBDEUJRxPATcCtcsdOp',
					'GduOLco0wL1pOTboeClVPmZe8PPXEYD0VKnmKWpb2of7UNTbrY',
					'399687253-xb9c6wdOQMBU8K2Jk3utxDLuqC21qRLTajkV9iel',
					'bXdT9ejraFk6O9bNExA2sD71jgixMFby8nqzQwfsTLXKa')

# Age Ranges	: dictionary key
# 	19- 		: 15
# 	20-24		: 20
# 	25-29		: 25
# 	30-34		: 30
# 	35-39		: 35
# 	40-44		: 40
# 	45-59		: 45
# 	50-54		: 50
# 	55-59		: 55
# 	60-64		: 60
# 	65+ 		: 65

def create_dictionaries():
	uniword = {}
	biword = {}
	syllab_avg = {}
	total_tweets = {}

	age = 15
	while age < 70:
		uniword[age] = {}
		biword[age] = {}
		syllab_avg[age] = 0.0
		age += 5

	return uniword, biword, syllab_avg

#Changes age to smallest value of coinciding bucket
def normalize_age(age):
	age /= 5
	age *= 5
	if age < 15:
		age = 15
	if age > 65:
		age = 65
	return age

#input: array of all tweets
#input: age of celebrity
#input: uniword dict
#input: biword dict
def train_system(tweets, age, uniword, biword):

	#cycle through tweets and add to uniword and biword dictionaries
	for tweet in tweets:
		prev_word = ""
		for word in tweet.split():
			both_words = str(prev_word + " " + word)
			uniword[age][word] = uniword[age].get(word, 0) + 1

			if prev_word != "":
				biword[age][both_words] = biword[age].get(both_words, 0) + 1
			prev_word = word

	return

def fetchSyllables(word):
	syll = 1.666666666	#average syll/word in Eng lang.
	syll = textstat.syllable_count(word)
	return syll

def train_system_syllables(tweets):
	syll_count = 0.0
	word_count = 0.0

	# dictionary to remember syllables
	# syllables[word] => num syllables in word
	syllables = {}
	for tweet in tweets:
		syll = 1.666666
		for word in tweet.split():
			if "\\" in word:
				continue
			elif word not in syllables:
				syll = fetchSyllables(word)
			else:
				syll = syllables[word]

			syllables[word] = syll

			word_count += 1.0
			syll_count += syll

	return syll_count/word_count

def load_dictionaries_from_files():
	with open("saved_dictionaries/uniword") as file:
		data = file.read()
	uniword = json.loads(data)
	with open("saved_dictionaries/biword") as file:
		data = file.read()
	biword = json.loads(data)
	with open("saved_dictionaries/syllab_avg") as file:
		data = file.read()
	syllab_avg = json.loads(data)

	return uniword, biword, syllab_avg

def demo(username, uniword, biword, syllab_avg):
	tweets = []

	try:
		results = api.request('statuses/user_timeline', {'screen_name': username, 'count': 200, 'include_rts': False})
		for item in results:
			tweets.append(item['text'])
	except:
		print "You either typed in your username wrong or you don't have a twitter\n"
		return

	if len(tweets) < 1:
		return

	estimate_age(tweets, uniword, biword, syllab_avg)


def estimate_age(tweets, uniword, biword, syllab_avg):
	probabilities = {}
	for tweet in tweets:
		prev_word = ""
		tweet = process_tweet(tweet)
		words = tweet.split(" ")

		for word in words:
			for age in uniword:
				if prev_word != "":
					if age in probabilities:
						count = float(biword[age].get(prev_word + " " + word, 0))
						uni_count = float(uniword[age].get(prev_word, 0))
						probabilities[age] += log10((count + 1) / (uni_count + 100))
					else:
						count = float(biword[age].get(prev_word + " " + word, 0))
						uni_count = float(uniword[age].get(prev_word, 0))
						probabilities[age] = log10((count + 1) / (uni_count + 100))
			prev_word = word

	probs_sorted = sorted(probabilities.items(), key=operator.itemgetter(1), reverse = True)
	# count = 1
	# print "Your predicted age based on your tweets is:"

	# for age_prob in probs_sorted:
	# 	if count > 3:
	# 		break
	# 	age = int(age_prob[0])
	# 	max_age = age + 4
	# 	print str(count) + ") " + str(age) + " - " + str(max_age)
	# 	count += 1

	# print probabilities
	# print probs_sorted
	return probs_sorted[0][0]


def test_system(test_data, uniword, biword, syllab_avg):
	total = 0.0
	correct = 0.0
	within_one = 0.0

	for age in test_data.keys():
		for handle in test_data[age].keys():

			predicted_age = int(estimate_age(test_data[age][handle], uniword, biword, syllab_avg))
			total += 1

			if predicted_age == int(age):
				correct += 1
			elif predicted_age == (int(age) - 5) or predicted_age == (int(age) + 5):
				within_one += 1

	accuracy = correct / total
	accuracy_within_one = (correct + within_one) / total

	print "Accuracy: " + str(accuracy)
	print "Within one: " + str(accuracy_within_one)

def test_syllables(test_data, syllab_avg):
	total = 0.0
	correct = 0.0
	within_one = 0.0

	for age in test_data.keys():
		for handle in test_data[age].keys():

			#Average syllable count for this test subject's tweets
			syll = train_system_syllables(test_data[age][handle])
			total += 1

			predicted_age = -1.0
			min_diff = 1000.0

			for age_avg in syllab_avg:
				if abs(syll - syllab_avg[age_avg]) < min_diff:
					predicted_age = int(age_avg)
					min_diff = abs(syll - syllab_avg[age_avg])

			if predicted_age == int(age):
				correct += 1
			elif predicted_age == (int(age) - 5) or predicted_age == (int(age) + 5):
				within_one += 1

			# print correct
			# print "(" + str(int(correct)) + "/" + str(int(total)) + ")"
			# print "Predicted age: " + str(predicted_age)

	accuracy = correct / total
	accuracy_within_one = (correct + within_one) / total

	print "Accuracy: " + str(accuracy)
	print "Within one: " + str(accuracy_within_one)


def read_and_train(uniword, biword, syllab_avg):
	# loop through tweets in and train system on each tweet
	obj = {}
	with open("age_to_tweets") as file:
		for line in file.readlines():
			obj = ast.literal_eval(line)


	# train system -> loop over age-tweets dict and train sys
	for age, tweets in obj.items():
		train_system(tweets, int(age), uniword, biword)
		average = train_system_syllables(tweets)
		syllab_avg[int(age)] = average

	with codecs.open('saved_dictionaries/uniword', 'w') as output:
		dumped = json.dumps(uniword)
		output.write(dumped)
	with codecs.open('saved_dictionaries/biword', 'w') as output:
		dumped = json.dumps(biword)
		output.write(dumped)
	with codecs.open('saved_dictionaries/syllab_avg', 'w') as output:
		dumped = json.dumps(syllab_avg)
		output.write(dumped)

def run_system(uniword, biword, syllab_avg):
	while 1:
		username = raw_input("What's your twitter handle?\n")
		demo(username, uniword, biword, syllab_avg)

if __name__ == '__main__':

	#Initialize dictionaries with empty dictionaries for each age range
	uniword, biword, syllab_avg = create_dictionaries()

	#Only needed to fill the file - comment out otherwise
	#Print "training..."
	read_and_train(uniword, biword, syllab_avg)

	uniword, biword, syllab_avg = load_dictionaries_from_files()

	#If running or testing
	if len(sys.argv) > 1 and sys.argv[1] == "test":
		with open("test_data") as file:
			for line in file.readlines():
				ages = ast.literal_eval(line)
		#This test tests using biword and uniword model
		print "--- System ---"
		test_system(ages, uniword, biword, syllab_avg)

		print "\n--- Syllables ---"
		#This test tests using syllables
		test_syllables(ages, syllab_avg)
	else:
		run_system(uniword, biword, syllab_avg)
