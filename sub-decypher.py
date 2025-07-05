#!/usr/bin/python3

import word_engine
import sys
import string
import itertools
import pdb
import shutil
import time

class cipherWord:
    def __init__(self, cipher_word, all_words):
        self.cipher_word = cipher_word
        self.all_words = all_words
        if "'" in cipher_word:
            self.words_by_length = [ word for word in all_words.apostropheWords() if len(word) == len(cipher_word) ]
        else:
            self.words_by_length = all_words.splitByLength("std", len(self.cipher_word))
        self.words_by_dupes = self.filter_for_duplicates()
        self.tried_words = []
        self.available_words = [ word for word in self.words_by_dupes ]
        self.current_guess = ""

    def filter_for_duplicates(self):
        dict_list = self.words_by_length
        # Look for duplicate letters in cipher_word (excluding apostrophes)
        cipher_letters = [ letter for letter in self.cipher_word if letter != "'" ]
        duplicates = [ letter for letter in cipher_letters if cipher_letters.count(letter) > 1 ]
        if len(duplicates) > 0:
            # enumerate all letters to get their indices
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
            # Remove all words that have dupes (excluding apostrophes from both cipher and dict words)
            new_dict_list = []
            for dict_word in self.words_by_length:
                dict_letters = [ letter for letter in dict_word if letter != "'" ]
                duplicates = [ letter for letter in dict_letters if dict_letters.count(letter) > 1 ]
                if len(duplicates) == 0:
                    new_dict_list.append(dict_word)
            dict_list = new_dict_list
        return(dict_list)

    def get_map(self):
        # Create mapping excluding apostrophes (they appear in clear text)
        if not self.current_guess:
            return {}
        cipher_letters = []
        guess_letters = []
        for i, char in enumerate(self.cipher_word):
            if char != "'":
                cipher_letters.append(char)
                guess_letters.append(self.current_guess[i])
        cipher_map = dict(zip(guess_letters, cipher_letters))
        return(cipher_map)

    def get_posmap(self, word, values):
        posmap = { value:[] for value in values }
        for index in range(0, len(word)):
            if word[index] in values and word[index] != "'":
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
            # Check if apostrophes match exactly in position
            apostrophe_match = True
            for i, char in enumerate(self.cipher_word):
                if char == "'" and (i >= len(word) or word[i] != "'"):
                    apostrophe_match = False
                    break
                elif char != "'" and i < len(word) and word[i] == "'":
                    apostrophe_match = False
                    break
            
            if not apostrophe_match:
                words_to_prune.append(word)
                continue
                
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
    def __init__(self, cipher_words, show_realtime=False, show_all_results=False):
        self.all_words = word_engine.words("/usr/share/dict/words")
        self.cipher_words = [ cipherWord(word, self.all_words) for word in cipher_words ]
        self.show_realtime = show_realtime
        self.show_all_results = show_all_results
        self.total_word_attempts = 0
        self.backtracking_events = 0
        self.attempts_per_position = [0] * len(cipher_words)
        self.abandons_at_depth = [0] * (len(cipher_words) + 1)  # +1 for depth 0
        self.start_time = time.time()
        self.solve()
        self.end_time = time.time()
        self.ranked_solutions = self.rank_solutions()
        self.report()

    def get_full_map(self):
        cipher_maps = [ word.get_map() for word in self.cipher_words ]
        full_map = { key:value for cipher_map in cipher_maps for key, value in cipher_map.items() }
        return(full_map)

    def print_progress(self, current_word_index=-1):
        # Print current progress with asterisks for unguessed words
        # Highlight the current word being guessed
        output_line = ""
        for i, word in enumerate(self.cipher_words):
            if i > 0:
                output_line += " "
            
            if word.current_guess:
                # Word has been guessed
                if i == current_word_index:
                    # Highlight current word with brackets
                    output_line += "[{}]".format(word.current_guess)
                else:
                    output_line += word.current_guess
            else:
                # Word not guessed yet, show asterisks
                asterisk_word = ""
                for char in word.cipher_word:
                    if char == "'":
                        asterisk_word += "'"
                    else:
                        asterisk_word += "*"
                
                if i == current_word_index:
                    # Highlight current word with brackets
                    output_line += "[{}]".format(asterisk_word)
                else:
                    output_line += asterisk_word
        
        # Check if output is to a terminal (not piped)
        if sys.stdout.isatty():
            # Use simple carriage return and overwrite approach
            # This works for most cases, even if line wraps it's still better than no clearing
            print(f"\r{output_line}\033[K", end="", flush=True)
        else:
            # Output is piped, just print each line normally
            print(output_line)

    def remaining_words(self):
        return [ word for word in self.cipher_words if word not in self.current_solve ]

    def solve(self):
        # First word should have the smallest list of available words
        self.solutions = []
        self.maps = []
        progress = []
        self.current_solve = [ min(self.cipher_words, key=lambda cipherWord: len(cipherWord.words_by_dupes)) ]
        # Loop until first word choices are exhausted
        while len(self.current_solve[0].words_by_dupes) > len(self.current_solve[0].tried_words):
            # Check if last word in list has a current guess
            if len(self.current_solve[-1].current_guess) > 0:
                # Find next word with smallest list of available words, and choose a word from its list
                next_word = min(self.remaining_words(), key=lambda cipherWord: len(cipherWord.available_words))
                self.current_solve.append(next_word)
            #choose word from available words
            self.current_solve[-1].choose_next_word()
            self.total_word_attempts += 1
            
            # Track attempts per position
            current_word_position = self.cipher_words.index(self.current_solve[-1])
            self.attempts_per_position[current_word_position] += 1
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
                new_progress = [ word.current_guess for word in self.cipher_words ]
                if progress != new_progress:
                    progress = new_progress
                    # Find the index of the word that was just guessed
                    current_word_index = -1
                    for i, word in enumerate(self.cipher_words):
                        if word in self.current_solve and word.current_guess:
                            current_word_index = i
                            break
                    # Print progress only if real-time display is enabled
                    if self.show_realtime:
                        self.print_progress(current_word_index)
                if shortest_current_guess > 0:
                    # Potential solution found
                    if self.show_realtime:
                        print()  # Move to new line when solution is found
                    self.solutions.append([ word.current_guess for word in self.cipher_words ])
                    self.maps.append(current_map)
                # Perform a reset
                self.backtracking_events += 1
                
                # Track abandon depth (how many words were placed before backtracking)
                abandon_depth = len([w for w in self.current_solve if w.current_guess])
                self.abandons_at_depth[abandon_depth] += 1
                
                for word in self.current_solve[::-1]:
                    current_map = self.get_full_map()
                    if len(word.available_words) > 0 or word == self.current_solve[0]:
                        word.soft_reset()
                        break
                    else:
                        word.hard_reset()
                        del self.current_solve[-1]

    def get_word_frequency_score(self, word):
        """Simple heuristic-based word frequency scoring."""
        word_lower = word.lower()
        
        # Very common words get high scores
        very_common = {'the', 'and', 'you', 'that', 'was', 'for', 'are', 'with', 'his', 'they',
                      'this', 'have', 'from', 'not', 'had', 'but', 'what', 'can', 'out', 'other',
                      'were', 'all', 'your', 'when', 'said', 'there', 'use', 'each', 'which',
                      'she', 'how', 'their', 'will', 'about', 'if', 'up', 'time', 'has'}
        if word_lower in very_common:
            return 100
            
        # Common words get medium-high scores  
        common = {'one', 'two', 'way', 'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did',
                 'get', 'come', 'made', 'may', 'part', 'over', 'new', 'sound', 'take', 'only',
                 'little', 'work', 'know', 'place', 'year', 'live', 'back', 'give', 'most',
                 'very', 'after', 'thing', 'our', 'just', 'name', 'good', 'sentence', 'man',
                 'think', 'say', 'great', 'where', 'help', 'through', 'much', 'before', 'line',
                 'right', 'too', 'mean', 'old', 'any', 'same', 'tell', 'boy', 'follow', 'came',
                 'want', 'show', 'also', 'around', 'form', 'three', 'small', 'set', 'put', 'end',
                 'why', 'again', 'turn', 'here', 'off', 'went', 'old', 'number', 'no', 'way',
                 'could', 'people', 'my', 'than', 'first', 'water', 'been', 'call', 'make', 'into'}
        if word_lower in common:
            return 75
        
        # Length-based scoring for other words
        length = len(word)
        if length <= 2:
            return 60  # Short words are often common
        elif length <= 4:
            return 50
        elif length <= 6:
            return 40
        elif length <= 8:
            return 30
        else:
            return 20  # Very long words are usually less common

    def score_solution(self, solution):
        """Score a complete solution based on word frequency."""
        if not solution:
            return 0
        
        # Sum individual word scores
        word_scores = [self.get_word_frequency_score(word) for word in solution]
        base_score = sum(word_scores)
        
        # Average to normalize for phrase length
        return base_score / len(solution)

    def rank_solutions(self):
        """Rank all solutions by their frequency score."""
        if not self.solutions:
            return []
        
        # Calculate scores for all solutions
        scored_solutions = []
        for solution in self.solutions:
            score = self.score_solution(solution)
            scored_solutions.append((score, solution))
        
        # Sort by score (highest first)
        scored_solutions.sort(key=lambda x: x[0], reverse=True)
        
        return scored_solutions

    def display_paginated_results(self):
        """Display results with pagination - space to continue, 'a' for all, any other key to quit."""
        if not self.ranked_solutions:
            return
            
        # If show_all_results is True, display all results without pagination
        if self.show_all_results:
            for score, solution in self.ranked_solutions:
                print(f" {' '.join(solution)} (score: {score:.1f})")
            return
            
        page_size = 20
        current_index = 0
        
        while current_index < len(self.ranked_solutions):
            # Display current page
            end_index = min(current_index + page_size, len(self.ranked_solutions))
            for i in range(current_index, end_index):
                score, solution = self.ranked_solutions[i]
                print(f" {' '.join(solution)} (score: {score:.1f})")
            
            current_index = end_index
            
            # Check if there are more results
            if current_index < len(self.ranked_solutions):
                remaining = len(self.ranked_solutions) - current_index
                print(f"\n[{remaining} more results - Press SPACE to continue, 'a' for all, any other key to quit]")
                
                # Check if we're in an interactive terminal
                if sys.stdin.isatty():
                    try:
                        # Read a single character
                        import termios, tty
                        fd = sys.stdin.fileno()
                        old_settings = termios.tcgetattr(fd)
                        try:
                            tty.setraw(fd)
                            char = sys.stdin.read(1)
                        finally:
                            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                        
                        # Check the character pressed
                        if char == ' ':
                            print()  # Add blank line before next page
                            continue
                        elif char.lower() == 'a':
                            print("Showing all remaining results...")
                            # Display all remaining results
                            for i in range(current_index, len(self.ranked_solutions)):
                                score, solution = self.ranked_solutions[i]
                                print(f" {' '.join(solution)} (score: {score:.1f})")
                            break
                        else:
                            print("Stopped.")
                            break
                            
                    except (ImportError, OSError):
                        # Fallback for systems without termios (like Windows)
                        char = input().strip().lower()
                        if char == 'a':
                            print("Showing all remaining results...")
                            # Display all remaining results
                            for i in range(current_index, len(self.ranked_solutions)):
                                score, solution = self.ranked_solutions[i]
                                print(f" {' '.join(solution)} (score: {score:.1f})")
                            break
                        elif char != ' ' and char != '':
                            print("Stopped.")
                            break
                else:
                    # Non-interactive mode (piped input/output), show all results
                    break
            else:
                # No more results
                break

    def report(self):
        elapsed_time = self.end_time - self.start_time
        
        # Get terminal width for formatting
        try:
            terminal_width = shutil.get_terminal_size().columns
        except:
            terminal_width = 80  # fallback
        
        # Print formatted statistics report
        print(f"\n{'=' * min(60, terminal_width)}")
        print("SOLUTION REPORT")
        print(f"{'=' * min(60, terminal_width)}")
        
        # Format statistics in columns
        stats = [
            ("Word Attempts", f"{self.total_word_attempts:,}"),
            ("Backtracking Events", f"{self.backtracking_events:,}"),
            ("Time Elapsed", f"{elapsed_time:.2f}s"),
            ("Solutions Found", f"{len(self.solutions):,}")
        ]
        
        # Calculate column widths
        max_label_width = max(len(stat[0]) for stat in stats)
        max_value_width = max(len(stat[1]) for stat in stats)
        
        # Print statistics in aligned columns
        for label, value in stats:
            print(f"{label:<{max_label_width}} : {value:>{max_value_width}}")
        
        print(f"{'=' * min(60, terminal_width)}")
        
        # Print position analysis table
        if len(self.cipher_words) > 1:  # Only show for multi-word phrases
            print()
            print("POSITION ANALYSIS")
            print(f"{'=' * min(60, terminal_width)}")
            
            # Show total attempts per position (more meaningful than average)
            # since each position gets attempted different numbers of times
            
            # Create table headers
            print(f"{'Position':<8} | {'Length':<6} | {'Total Attempts':<13} | {'Abandons at Depth':<16}")
            print(f"{'-' * 8} | {'-' * 6} | {'-' * 13} | {'-' * 16}")
            
            # Print data for each position/depth
            max_rows = max(len(self.cipher_words), len(self.abandons_at_depth))
            for i in range(max_rows):
                pos_str = str(i + 1) if i < len(self.cipher_words) else ""
                
                if i < len(self.cipher_words):
                    length_str = str(len(self.cipher_words[i].cipher_word))
                else:
                    length_str = "-"
                
                if i < len(self.attempts_per_position) and self.attempts_per_position[i] > 0:
                    attempts_str = f"{self.attempts_per_position[i]:,}"
                else:
                    attempts_str = "-"
                
                if i < len(self.abandons_at_depth):
                    abandon_str = f"{self.abandons_at_depth[i]:,}"
                else:
                    abandon_str = "-"
                
                print(f"{pos_str:<8} | {length_str:<6} | {attempts_str:<13} | {abandon_str:<16}")
            
            print(f"{'=' * min(60, terminal_width)}")
        
        if len(self.solutions) == 0:
            print("No solutions found")
        else:
            if self.show_realtime:
                print("(Solutions were displayed above during solving)")
            else:
                print("Potential solutions (ranked by frequency):")
                self.display_paginated_results()


def get_cipher():
    # Check for flags
    show_realtime = '--show-realtime' in sys.argv
    show_all_results = '--show-all-results' in sys.argv
    
    # Filter out flags from arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    if len(args) == 0:
        cipher_phrase = input("Please enter a phrase to decode: ")
        # Strip surrounding double quotes if present
        if len(cipher_phrase) >= 2 and cipher_phrase[0] == '"' and cipher_phrase[-1] == '"':
            cipher_phrase = cipher_phrase[1:-1]
        cipher_words = cipher_phrase.split()
    else:
        # Join all arguments into single phrase and check for surrounding quotes
        cipher_phrase = ' '.join(args)
        if len(cipher_phrase) >= 2 and cipher_phrase[0] == '"' and cipher_phrase[-1] == '"':
            cipher_phrase = cipher_phrase[1:-1]
        cipher_words = cipher_phrase.split()
    
    cipher = cipherData(cipher_words, show_realtime=show_realtime, show_all_results=show_all_results)
    return(cipher)

if __name__ == "__main__":
    cipher = get_cipher()
