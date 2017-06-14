# 486-final-project

## Setup:
	pip install -r requirements.txt

## Step 1: Obtain datasets
	
	Run:
		python get_tweets.py

	The above command line will create your training dataset which will be located in age_to_tweet and your test data set which will be located in test_data.
		age_to_tweet: Dictionary containing age value mapping to list of tweets corresponding with that age
		test_data: Dictionary containing age that maps to a dictionary of celebrities that map to their tweets
		

## Step 2: Test
	
	Run:
		python system.py test

	The above command will run our system function and syllables function and output our exact accuracy and within one accuracy. The above command line creates detests biword, uniword, and syllab_avg.

		biword: pairs of words from tweets
		uniword: single words from tweets
		syllab_avg: Average syllable count for each bucket range


## Step 3: Demo
	
	Setup:
		Uncomment lines 163 - 172
	
	Run:
		python system.py

	The above command line will begin a demo. You will be prompted to enter your twitter handle.
