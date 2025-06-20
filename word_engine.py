#!/usr/bin/python

class words:
    """ Provides list comprehensions to build constrained word lists."""
    def __init__ (self, wordFile='/usr/share/dict/words'):
        self.wordList = self.readWords(wordFile)
    def readWords(self, wordFile='/usr/share/dict/words'):
        """
        Reads words from given file and returns dictionary with three keys

        wordList["pos"] list of words that end with 's
        wordList["pNoun"] list of words that begin with a capital letter
        wordlist["cont"] list of words that contain ' but do not end with 's
        wordlist["std"] list of remaining words
        """
        wordList = { "pos":[], "pNoun":[], "cont":[], "std":[] }
        with open(wordFile, 'r') as wordFile:
            for word in wordFile:
                word = word.replace('\n','')
                if word[-2:] == "'s": wordList["pos"].append(word)
                elif not word[0].islower(): wordList["pNoun"].append(word)
                elif "\'" in word: wordList["cont"].append(word)
                else: wordList["std"].append(word)
        return wordList
    def splitByLength(self, List, length):
        return [ word for word in self.wordList[List] if len(word) == length ]
    def longerThan(self, List, length):
        return [ word for word in self.wordList[List] if len(word) > length ]
    def shorterThan(self, List, length):
        return [ word for word in self.wordList[List] if len(word) < length ]
    def includes(self, List, pattern):
        return [ word for word in List if pattern in word ]
    def possessiveWords(self):
        return [ word for word in self.wordList["pos"] ]
    def standardWords(self):
        return [ word for word in self.wordList["std"] ]
    def properNouns(self):
        return [ word for word in self.wordList["pNoun"] ]
    def startsWith(self, List, string):
        return [ word for word in List if word[0:len(string)]==string ]
    def endsWith(self, List, string):
        return [ word for word in List if word[-len(string):] == string ]
    def notIncludes(self, List, string):
        return [ word for word in List if string not in word ]
    def letterAt(self, List, letter, position):
        return [ word for word in List if word[position] == letter ]
    def letterNotAt(self, List, letter, position):
        return [ word for word in List if word[position] != letter ]
    def apostropheWords(self):
        return [ word for word in self.wordList["pos"] ] + [ word for word in self.wordList["cont"] ]
