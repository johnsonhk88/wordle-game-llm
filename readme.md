# Introduction
1. it is Wordle game solver by LLM Model
2. The guess word must only 5 letters
3. Use Restful API to connect Wordle Server to submit the guess word, and return the response with each letter position, resulting into correct, absent or present
4. Use the previous guess result for guiding LLM model to generate next guess word 
5. the program will continue to guess the word  until all letters are correct or reach to maximum try times. 

# Installation dependencies libraies and setup
1. run pip install -r requirements for install all requirement dependencies libraries for this project
2. Setup local LLM Model server
   2.1 Download LMStudio Software [link](https://lmstudio.ai/)
   2.2 Run lmstudio application locally
   2.2 Download LLama3-8B LLM Model from LMStudio software
   2.3 Load llama3 model for LM Studio, and enable local LLM Model server 
   2.4 use openAI API to connect local LLM Model server

# Run application 
1. type python apps.py for runing application
2. the program will try to several round to guess the word , base on previous guess word result to generate next guess word
