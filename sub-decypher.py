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
        self.available_words = []
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

    def filter_for_solved(self, full_map):
        # Filter dict_list against current cipher_map
        # Duplicate pruned by dupes list
#        pdb.set_trace()
        words_by_map = [ word for word in self.words_by_dupes ]
        print("Available words based on dupe pattern: \n{}".format(words_by_map))
        keys = full_map.keys()
        values = full_map.values()
#        print("Map to be applied: \n\t{}\n\t{}".format(keys, values))
        # Check if any keys exist in cipher
        present_keys = [ key for key in full_map.keys() if full_map[key] in self.cipher_word ]
        if len(present_keys) == 0:
            # Remove all words that do not contain a map key
#            print("Found no existing keys in word: {}.".format(self.cipher_word))
            words_to_prune = [ word for key in full_map.keys() for word in words_by_map if key in word ]
        else:
            # Remove words whose letters do not match the current keymap
#            print("Found the following keys in word: \n{}".format(present_keys))
            words_to_prune=[]
            for key in present_keys:
                if full_map[key] in self.cipher_word:
#                    print("found value: {} in cipher_word: {}".format(full_map[key], self.cipher_word))
                    letter_data = enumerate(self.cipher_word)
                    # Find positions where the key exists
                    positions = [ letter_datum[0] for letter_datum in letter_data if letter_datum[1] == full_map[key] ]
#                    print("Value found at positions: {}".format(positions))
                    for position in positions:
                        for word in [ word for word in words_by_map if word[position] != key ]:
                            words_to_prune.append(word)

#       # Prune words that do not match
#        print("Pruning the following words: \n{}".format(set(words_to_prune)))
        for word in set(words_to_prune):
            words_by_map.remove(word)
        return(words_by_map)

    def choose_next_word(self, full_map):
        available_words = self.filter_for_solved(full_map)
#        print("Tried words: \n{}".format(self.tried_words))
        for word in self.tried_words:
            available_words.remove(word)
        if len(available_words) == 0:
            return False
        else:
            self.available_words = available_words
            self.current_guess = available_words[0]
            return True

    def full_reset(self):
        self.tried_words = []
        self.current_guess = ""

    def reset(self):
        self.tried_words.append(self.current_guess)
        self.current_guess = ""


class cipherData:
    def __init__(self, cipher_words):
        self.all_words = word_engine.words("/usr/share/dict/words")
        self.cipher_words = [ cipherWord(word, self.all_words) for word in cipher_words ]
        self.cipher_orders = itertools.permutations(cipher_words)
        self.solve()

    def solve(self):
        solves = []
        maps = []
#        for i in range(0,3000):
        while len(self.cipher_words[0].words_by_dupes) > len(self.cipher_words[0].tried_words):
            current_solve = [ word.current_guess for word in self.cipher_words ]
#            print(current_solve)
#            print("Base word: {}\tAvailable: {}\tTried: {}".format(self.cipher_words[0].cipher_word, len(self.cipher_words[0].words_by_dupes), len(self.cipher_words[0].tried_words)))
            #Loop through words.  Find first word with no current_guess
            for word in enumerate(self.cipher_words):
                if word[1].current_guess == "":
#                    print("Selected {}-{} with no guesses.".format(word[0],word[1].cipher_word))
                    # Attempt to choose a word
                    if not word[1].choose_next_word(self.get_full_map()):
#                        print("Choose word returned false")
#                        print("Previous word: {}".format(self.cipher_words[word[0]-1].cipher_word))
#                        print("Previous word available word count: {}".format(len(self.cipher_words[word[0]-1].available_words)))
                        # Could not choose a word.  Does this word have a guessing history?
                        if len(word[1].tried_words) == 0:
#                            print("This is not the first word and has never been guessed")
                            if len(self.cipher_words[word[0]-1].available_words) > 0:
#                                print("Previous word has more words.  Soft reset")
                                self.cipher_words[word[0]-1].reset()
                            else:
#                                print("Previous word supply exhausted.  Hard reset")
                                self.cipher_words[word[0]-1].full_reset()
                        else: 
#                            print("This word has exhausted its word supply. Hard reset")
                            word[1].full_reset()
#                            print("Soft reset on previous word")
                            self.cipher_words[word[0]-1].reset()
                        break
                    else:
#                        print("Chose word: {}".format(word[1].current_guess))
                        break
                if word[0] == len(self.cipher_words)-1 and word[1] != "":
                    solves.append(current_solve)
                    maps.append(self.get_full_map())
                    word[1].reset()
        for i in range(0, len(solves)):
            print("Potential solve: \n{}\nMap: \n{}".format(solves[i],maps[i]))

    def translate(self, word):
        full_cipher = {}
        for cipher_map in self.cipher_maps:
           full_cipher.update(cipher_map)
        transtab = word.maketrans(full_cipher)
        return(word.translate(transtab))

    def get_full_map(self):
        cipher_maps = [ word.get_map() for word in self.cipher_words ]
        full_map = { key:value for cipher_map in cipher_maps for key, value in cipher_map.items() }
        return(full_map)

def get_cipher():
    arglen = len(sys.argv)

    if arglen == 1:
        cipher_phrase = input("Please enter a phrase to decode: ")
        cipher_words = cipher_phrase.split()
    else:
        cipher_words = sys.argv[1:]
    cipher = cipherData(cipher_words)
    return(cipher)


cipher = get_cipher()
