#!/usr/bin/python3

import word_engine
import sys
import string
import itertools
import pdb

class cipherWord:
    def __init__(self, cipher_word, all_words):
        self.cipher_word = cipher_word
        self.all_words = all_words
        self.words_by_length = all_words.splitByLength("std", len(self.cipher_word))
        self.words_by_dupes = self.filter_for_duplicates()
        self.tried_words = []
        self.available_words = [ word for word in self.words_by_dupes ]
        self.current_guess = ""

    def filter_for_duplicates(self):
        dict_list = self.words_by_length
        # Look for duplicate letters in cipher_word
        duplicates = [ letter for letter in self.cipher_word if self.cipher_word.count(letter) > 1 ]
        if len(duplicates) > 0:
            # enumerate duplicate letters to get their indices
            letter_data = [ letter_datum for letter_datum in enumerate(self.cipher_word) ]
            for dup_letter in set(duplicates):
                # Find all indices where each duplicate letter exist
                indices = [ letter_datum[0] for letter_datum in letter_data if letter_datum[1] == dup_letter ]
                new_dict_list = []
                # Return only words from dict_list that match duplicate pattern
                for dict_word in dict_list:
                    # Find all letters in dict word that are in cipher word duplicate letter indices
                    dict_letters = [ dict_word[index] for index in indices ]
                    # Add to new_dict if indices contain 1 unique letter
                    if len(set(dict_letters)) == 1 and dict_word.count(dict_letters[0])==len(indices):
                        new_dict_list.append(dict_word)
                #Prune dict_list to only positive results and move on to next letter with duplicates
                dict_list = new_dict_list
        else:
            # Remove all words that have dupes
            new_dict_list = []
            for dict_word in self.words_by_length:
                duplicates = [ letter for letter in dict_word if dict_word.count(letter) > 1 ]
                if len(duplicates) == 0:
                    new_dict_list.append(dict_word)
            dict_list = new_dict_list
        return(dict_list)

    def get_map(self):
        cipher_map = dict(zip(self.current_guess, self.cipher_word))
        return(cipher_map)

    def get_posmap(self, word, values):
        posmap = { value:[] for value in values }
        for index in range(0, len(word)):
            if word[index] in values:
                posmap[word[index]].append(index)
        return posmap

    def filter_for_solved(self, full_map):
        # Filter dict_list against current cipher_map
        # Duplicate pruned by dupes list
        words_by_map = [ word for word in self.words_by_dupes ]
        keys = full_map.keys()
        values = full_map.values()
        #Get values for all existing key value posititions in cipher_word
        cipher_values = [ value for value in self.get_posmap(self.cipher_word, full_map.values()).values() ]
        words_to_prune=[]
        for word in words_by_map:
            # Get values for all existing key positions in dictionary word
            word_values = [ value for value in self.get_posmap(word, full_map.keys()).values() ]
            # add to prunelist if they don't match
            if word_values != cipher_values:
                words_to_prune.append(word)
        # Prune selected words
        for word in set(words_to_prune):
            words_by_map.remove(word)
        self.available_words = words_by_map

    def choose_next_word(self):
        if len(self.available_words) == 0:
            return False
        else:
            self.current_guess = self.available_words[0]
            return True

    def hard_reset(self):
        self.tried_words = []
        self.available_words = [ word for word in self.words_by_dupes ]
        self.current_guess = ""

    def soft_reset(self):
        self.tried_words.append(self.current_guess)
        self.available_words.remove(self.current_guess)
        self.current_guess = ""


class cipherData:
    def __init__(self, cipher_words):
        self.all_words = word_engine.words("/usr/share/dict/words")
        self.cipher_words = [ cipherWord(word, self.all_words) for word in cipher_words ]
        self.solve()
        self.report()

    def get_full_map(self):
        cipher_maps = [ word.get_map() for word in self.cipher_words ]
        full_map = { key:value for cipher_map in cipher_maps for key, value in cipher_map.items() }
        return(full_map)

    def remaining_words(self):
        return [ word for word in self.cipher_words if word not in self.current_solve ]

    def solve(self):
        # First word should have the smallest list of available words
        self.solutions = []
        self.maps = []
        self.current_solve = [ min(self.cipher_words, key=lambda cipherWord: len(cipherWord.words_by_dupes)) ]
        # Loop until first word choices are exhausted
        while len(self.current_solve[0].words_by_dupes) > len(self.current_solve[0].tried_words):
            print("Current Guess: {}".format([ word.current_guess for word in self.cipher_words ]))
            # Check if last word in list has a current guess
            if len(self.current_solve[-1].current_guess) > 0:
                # Find next word with smallest list of available words, and choose a word from its list
                next_word = min(self.remaining_words(), key=lambda cipherWord: len(cipherWord.available_words))
                self.current_solve.append(next_word)
            #choose word from available words
            self.current_solve[-1].choose_next_word()
            #Update map and solved filter
            current_map = self.get_full_map()
            for word in self.remaining_words(): 
                word.filter_for_solved(current_map)
            #check if new word blows any unused words or phrase is solved
            # Test value for word choice exhaustion
            least_available_words = min([len(word.available_words) for word in self.cipher_words])
            # Test value for found solution
            shortest_current_guess = min([len(word.current_guess) for word in self.cipher_words])
            if least_available_words == 0 or shortest_current_guess > 0: 
                if shortest_current_guess > 0:
                    # Potential solution found
                    self.solutions.append([ word.current_guess for word in self.cipher_words ])
                    self.maps.append(current_map)
                # Perform a reset
                for word in self.current_solve[::-1]:
                    current_map = self.get_full_map()
                    if len(word.available_words) > 0 or word == self.current_solve[0]:
                        word.soft_reset()
                        break
                    else:
                        word.hard_reset()
                        del self.current_solve[-1]

    def report(self):
        print("Solution report:")
        if len(self.solutions) == 0:
            print("No solutions found")
        else:
            for index in range(0,len(self.solutions)):
                print("Potential solution: \n\t{}\n\t{}".format(self.solutions[index], self.maps[index]))

def get_cipher():
    arglen = len(sys.argv)

    if arglen == 1:
        cipher_phrase = input("Please enter a phrase to decode: ")
        cipher_words = cipher_phrase.split()
    else:
        cipher_words = sys.argv[1:]
    cipher = cipherData(cipher_words)
    return(cipher)

if __name__ == "__main__":
    cipher = get_cipher()
