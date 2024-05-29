import os, json, requests, time
import pandas as pd
from openai import OpenAI



# Define URL and ENDPOINT
baseURL = "https://wordle.votee.dev:8000"


# Get Method 
wordEndpoint = "/word"
randomEndpoint = "/random"
dailyEndpoint = "/daily"

# Post Method
wordsegEnpoint = "/wordseg"

#result response (Slot, guess, result), result =(absent, present, correct)

# define Global Variable
correctList = {} # store correct word list with position 
presentList = {} # store present word list with position
absentList = [] # store absent word list
triedList = [] # store tried word list

def clearList():
    correctList.clear()
    presentList.clear()
    absentList.clear()
    triedList.clear()

# Prompt Engineering to control the correct output for LLM to guess the word
templatePrompt1 = """You are playing a word game called Wordle. Your goal of the game is to guess a 5-letter one word only.
\nRandomly guess the words, you can used any word with 5 letters.
\nOutput only one word in JSON format with key "word" only.
"""
templatePrompt2 = """You are playing a word game called Wordle. Your goal of the game is to guess a 5-letter one word only.
\nThe Guess one Words must follow the requirement below:
\n1. The Guess word must be a 5-letter word only
\n2. The Guess word cannot use same as the tried word list
\n3. The Guess Word refer to the sample word. if the sample word letter position is ? symbol that is unknown letter, you must replace the ? symbol with the other guess letter, but you should not use absent letter. 
\n4. After, completed fill unknown to sample, you can use for guessing the word. 
\n5. Output guess one word In JSON format with key "word" only
\nsample word: {sample}
\ntried words list : {tried}
\nabsent words list : {absent}
\npresent words list : {present}
"""

templatePrompt3 = """You are playing a word game called Wordle. Your goal of the game is to guess a 5-letter one word only.
\nThe Guess Words must follow the requirement below:
\n1. The Guess one word must be a 5-letter word only
\n2. The Guess one word refer to the sample word. if the sample word letter position is ? symbol that is unknown letter, you must replace the ? symbol with the other guess letter, but you should not use absent letter. 
\n3. think step by step to guess the word by using the present word list to fill the unknown letter in the sample word.
\n4. The Guess word do not repeat the tried words list. if the word is in the tried words list, you should guess another words.
\n5. After, completed fill unknown to sample, you can use for guessing the word.
\n6. Do not contain any explanation of guess word for output 
\n7. Output guess word with the correct letter in JSON format with key "word" only
\nsample word: {sample}
\ntried words list : {tried}
\nabsent words list : {absent}
\npresent words list : {present}
"""


templatePrompt4 = """You are playing a word game called Wordle. Your goal of the game is to guess a 5-letter one word only.
\nThe guess Words must follow the requirement below:
\n1. The guess one word must be a 5-letter word only.
\n2. The guess one word must refer to the sample word. There are two type of letter in sample word. ? symbol in sample word represent unknown letter, otherwise is corrected words. You should replace the ? symbol with the other guess letter, but you cannot use absent letter. Keep the corrected letter for output guess word.
\n3. The guess word cannot repeat the tried words list. if the guess word is the inside the tried words list, you must repeat to guess another words.
\n4. think step by step how to correctly generate new guess word, you can using the present word list to fill the unknown letter in the sample word.
\n5. After, completed fill unknown to sample, you can use for guessing the word. 
\n6. if the guess word contain the absent letter, you should not use the absent letter to fill the unknown letter in the guess word.
\n6. Do not contain any explanation of guess word for output 
\n7. Output one guess word In JSON format with key "word" only
\nsample word: {sample}
\ntried words list : {tried}
\nabsent words list : {absent}
\npresent words list : {present}
"""

templatePrompt5 = """You are playing wordle game, Each Guess the new word must follow the requirement: 
\n1. Generate one word must has 5 letters only. 
\n2. Generate word do not use the tried words list
\n3. Generate word firstly check sample word. if sample letter position with ? symbol that is unknown letter, generate other letter and also can use present letter list but can not include invalid letter list , otherwise keep the known letter in the position
\n4. Generate word check unknown letter, do not include the absent letter listed in the generated word
\n5. Respond only with a 5 letters word as your answer, Output in JSON format word only with key "word"
\nsample word: {sample}
\ntried words list : {tried}
\nabsent words list : {absent}
\npresent words list : {present}
"""

# Restful API Get Method Function 
def getResponseRandom(guess, seed=1234):
    try:
         ret = requests.get(baseURL + randomEndpoint, params={"guess": guess, "seed": seed})
         print(ret.request.url)
         ret.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"""Error: {err}""")
        return None
    return ret.json()

def getResponseWord(guess, word):
    try:
         ret = requests.get(baseURL + wordEndpoint + "/"+ word , params={"guess": guess})
         print(ret.request.url)
         ret.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"""Error: {err}""")
        return None
    return ret.json()


def getResponseDaily(guess, size=5):
    try:
         ret = requests.get(baseURL + dailyEndpoint , params={"guess": guess, "size": size})
         print(ret.request.url)
         ret.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"""Error: {err}""")
        return None
    return ret.json()

def responseJsonParser(txt):
    # create dataframe structure
    data = pd.DataFrame(columns=["slot", "guess", "result"])
    # parse json file
    for row in txt: # iterate each row
        data = pd.concat([data, pd.DataFrame(row, index=[0])], axis=0) #add row to dataframe
    data.reset_index(drop=True, inplace=True) # reset index
    return data


def updateCorrectList(correctList, data):
    # select correct result from Dataframe
    correctData = data[data["result"] == "correct"]
    for index, row in correctData.iterrows(): # iterate each row
        if row["guess"] not in correctList: # check if the word is not in the list
            correctList[row["guess"]] = [row["slot"]] # add word to the list with position list
        else:
            poslist = correctList[row["guess"]] # get position list 
            if row["slot"] not in poslist:
                poslist.append(row["slot"])
                correctList[row["guess"]] = poslist # update position list
    return 

def updatePresentList(presentList, data):
    # select present result from Dataframe
    presentData = data[data["result"] == "present"]
    for index, row in presentData.iterrows(): # iterate each row
        if row["guess"] not in presentList: # check if the word is not in the list
            presentList[row["guess"]] = [row["slot"]] # add word to the list with position list
        else:
            poslist = presentList[row["guess"]] # get position list 
            if row["slot"] not in poslist:
                poslist.append(row["slot"])
                presentList[row["guess"]] = poslist # update position list
    return 

def updateAbsentList(absentList, data):
    # select absent result from Dataframe
    absentData = data[data["result"] == "absent"]
    for index, row in absentData.iterrows(): # iterate each row
        if row["guess"] not in absentList: # check if the word is not in the list
            absentList.append(row["guess"]) # add word to the list
    return

def updateTriedList(triedList, triedData):
    if triedData not in triedList:
        triedList.append(triedData)
    return

def updateALLList(data):
    global correctList, presentList, absentList
    updateCorrectList(correctList, data)
    updatePresentList(presentList, data)
    updateAbsentList(absentList, data)
    return


def LLMinit():
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    return client

def getLLMResponse(client, msg):
    response = client.completions.create(model="crusoeai/Llama-3-8B-Instruct-Gradient-1048k-GGUF",
                                         prompt=msg, 
                                         max_tokens=2048,
                                         temperature=1, #0.8,
                                         top_p=1)
    return response


def LLMResponseParser(response):
    """
    LLM Response Parser to get guess word
    """
    rep = response.choices[0].text
    print(rep)
    try:
        rep = rep.replace("```", "")
        rep = rep.split("\n\n")
        rep[1] = rep[1].replace("</s>", "")
        rep[1] = rep[1].replace("'''", "")
        rep[1] = rep[1].replace("```", "")
        # print(rep[1])
        jsonTxt = json.loads(rep[1])
    except Exception as e: 
        print("Error: LLM Response Parser", e)
        return None
    
    return jsonTxt


def fillCorrectWord(correctList):
    word ="?????"
    for key, value in correctList.items(): # iterate each correct word list
        for pos in value: #get position value
            word = word[:pos] + key + word[pos+1:] #fill correct word in the position
    return word

def correctCount(correctList):
    count = 0
    for key, value in correctList.items(): # iterate each correct word list
        count += len(value) #get position value
    return count 

def main():
    Test = False
    numTry = 15#20#5# 20
    
    #init LLM model
    client = LLMinit()

    if Test: # for testing function 
        ret = getResponseRandom("green", 1234)
        print(ret)
        df = responseJsonParser(ret)
        print(df)
        updateCorrectList(correctList, df)
        updatePresentList(presentList, df)
        updateAbsentList(absentList, df)
        print(correctList)
        print(presentList)
        print(absentList)
        # response = getLLMResponse(client, "What is it?")
        # print("LLM Response: ", response.choices[0].text)
        response = getLLMResponse(client, templatePrompt1)
        # print("LLM Response: \n", response.choices[0].text)
        jsonTxt = LLMResponseParser(response)
        print(jsonTxt)
        sample =fillCorrectWord(correctList)
        print(sample)
        count = correctCount(correctList)
        print(f"""Num of Correct Word: {count}""")
        # ret = getResponseWord("apple", "apple")
        # print(ret)
        # ret = getResponseDaily("daily",5)
        # print(ret)

    # loop for guessing the word
    clearList()
    for i in range(numTry):
        print(f"""Try Number: {i+1}""")
        # LLM Guess word
        if i == 0:
            res = getLLMResponse(client, templatePrompt1) #random guess first word
        
        else:
            # use the previous correct word to fill the sample word
            sample =fillCorrectWord(correctList)
            # print(f"""sample : {sample} """)
            newPrompt = templatePrompt5.format(sample=sample, tried=triedList, absent=absentList, present=presentList)
            print(f"""Prompt:\n{newPrompt}""")
            res = getLLMResponse(client, newPrompt)
        
        # send LLM Guess word to the API
        if res: 
            print("LLM Response:\n", res.choices[0].text)
            jsonTxt = LLMResponseParser(res) #get LLM guess word
            print(jsonTxt)
            if jsonTxt:
                guess = jsonTxt["word"]
                print("Guess Word: ", guess)
                if len(guess) != 5:
                    print("Error: Guess Word must be 5-letter word")
                    continue
                if '?' in guess:
                    print("Error: Guess Word cannot contain '?'")
                    continue
                updateTriedList(triedList, guess) # update tried list
                ret = getResponseRandom(guess, 1111) # send to API server
                # ret = getResponseWord(guess, "horse") # set the word for testing guest word response
                df = responseJsonParser(ret)  # parse response to dataframe
                print(df)
                updateALLList(df)
                # sample =fillCorrectWord(correctList)
                # print(sample)
                count = correctCount(correctList)
                print(f"""Num of Correct Word: {count}""")
                # ret = getResponseWord("apple", "apple")
                if count == 5:
                    print(f"""Guessed Correct Word: {fillCorrectWord(correctList)}""")
                    print(f"""Congratulations! You have guessed the word in {i+1} tries!""")
                    break   
                print(f"""Correct List: {correctList}""")
                print(f"""Present List: {presentList}""")
                print(f"""Absent List: {absentList}""")
                print(f"""Tried List: {triedList}""")
                print("-"* 30)
        time.sleep(1)
    print("End of the Game!")


        



    



if __name__ == "__main__":
    main()