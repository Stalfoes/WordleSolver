import pygame
from enum import Enum

BG_Color = (18,18,19)
W_Color = (215,218,220)
Y_Color = (175,163,60)
G_Color = (85,143,77)
D_Color = (58,58,60)

class Certainty(Enum):
    GREY = 0
    YELLOW = 1
    GREEN = 2

def C2C(c):
    if c == Certainty.GREY:
        return D_Color
    elif c == Certainty.YELLOW:
        return Y_Color
    elif c == Certainty.GREEN:
        return G_Color

class Game:
    def __init__(self, surface):
        self.surface = surface
        self.game_closed = False
        box_size = 62
        spacing = 5
        start_x = int(self.surface.get_width()/2) - int(5/2*box_size) - 2*spacing
        self.start_x = start_x
        start_y = 20
        self.start_y = start_y
        self.letter_boxes = [[LetterBox(self.surface,(start_x+x*(spacing+box_size),start_y+y*(spacing+box_size)),box_size) for x in range(5)] for y in range(6)]
        self.current_letter_filling = [0,0]
        self.solver = Solver()
        self.word_area_start = start_y+6*(spacing+box_size)+start_y
        self.word_area = WordArea(surface, self.word_area_start)

    def play(self):
        while not self.game_closed:
            self.handle_events()
            self.draw()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_closed = True
            if event.type == pygame.KEYDOWN:
                alphabet = set("abcdefghijklmnopqrstuvwxyz")
                letter = pygame.key.name(event.key)
                if event.key == pygame.K_BACKSPACE:
                    if self.current_letter_filling[1] == 0 and self.current_letter_filling[0] > 0:
                        self.current_letter_filling[0] -= 1
                    self.current_letter_filling[1] = 0
                    for lb in self.letter_boxes[self.current_letter_filling[0]]:
                        lb.clear()
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.current_letter_filling = [0,0]
                    for row in self.letter_boxes:
                        for lb in row:
                            lb.clear()
                    continue
                if letter not in alphabet:
                    continue
                x,y = pygame.mouse.get_pos()
                at_least_one_over = False
                for row in self.letter_boxes:
                    for lb in row:
                        if lb.isMousedOver(x, y):
                            lb.setLetter(letter.upper())
                            at_least_one_over = True
                            self.current_letter_filling[0] += 1
                if not at_least_one_over:
                    if self.current_letter_filling[0] < 6:
                        self.letter_boxes[self.current_letter_filling[0]][self.current_letter_filling[1]].setLetter(letter.upper())
                        self.current_letter_filling[1] += 1
                        if self.current_letter_filling[1] == 5:
                            self.current_letter_filling[0] += 1
                            self.current_letter_filling[1] = 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                x,y = pygame.mouse.get_pos()
                if y >= self.word_area_start:
                    self.word_area.areaClicked(x, y)
                    continue
                for row in self.letter_boxes:
                    for lb in row:
                        if lb.isMousedOver(x, y):
                            if event.button == 1:
                                lb.nextCertainty()
                            elif event.button == 3:
                                lb.clear()
    
    def draw(self):
        self.surface.fill(pygame.Color(BG_Color))
        for row in self.letter_boxes:
            for lb in row:
                lb.draw()
        # Make the possible word area
        possible_words, was_change = self.solver.findPossile(self.letter_boxes)
        self.word_area.draw(possible_words, was_change)
        # Show 3 variety words sorted descending in variety score
        top_variety_words = self.solver.wordsByVariety()[:10]
        variety_words_start_x = self.start_x - 100
        variety_words_start_y = self.start_y + 5 + 62
        l_surface = pygame.font.SysFont("Calibri", 16, True).render("Variety:", False, pygame.Color(W_Color))
        self.surface.blit(l_surface, (variety_words_start_x,variety_words_start_y))
        for y,vw in enumerate(top_variety_words):
            l_surface = pygame.font.SysFont("Calibri", 16, True).render(vw, False, pygame.Color(W_Color))
            self.surface.blit(l_surface, (variety_words_start_x,variety_words_start_y+(y+1)*16))
        pygame.display.update()

class LetterBox:
    def __init__(self, surface, position, size):
        self.surface = surface
        self.position = position
        self.size = size
        self.clear()
    
    def setLetter(self, l):
        self.letter = l
        if self.certainty == None:
            self.certainty = Certainty.GREY
    
    def nextCertainty(self):
        if self.certainty == None:
            # Do nothing
            pass
        elif self.certainty == Certainty.GREY:
            self.certainty = Certainty.YELLOW
        elif self.certainty == Certainty.YELLOW:
            self.certainty = Certainty.GREEN
        elif self.certainty == Certainty.GREEN:
            self.certainty = Certainty.GREY
    
    def clear(self):
        self.letter = None
        self.certainty = None
    
    def draw(self):
        rb = pygame.Rect(self.position[0],self.position[1],self.size,self.size)
        if self.certainty == None:
            pygame.draw.rect(self.surface, C2C(Certainty.GREY), rb, 2)
        else:
            pygame.draw.rect(self.surface, C2C(self.certainty), rb)
        l_surface = pygame.font.SysFont("Calibri", int(self.size/2), True).render(self.letter, False, pygame.Color(W_Color))
        l_rect = l_surface.get_rect(center=(self.position[0]+int(self.size/2), self.position[1]+int(self.size/2)))
        self.surface.blit(l_surface, l_rect)

    def isMousedOver(self, mx, my):
        if self.position[0] <= mx and mx <= self.position[0] + self.size:
            if self.position[1] <= my and my <= self.position[1] + self.size:
                return True
        return False

class WordArea:
    def __init__(self, surface, start_y):
        self.surface = surface
        self.start_y = start_y
        self.page_box_size = 40
        self.word_size = 80
        self.word_gap = 20
        self.start_x = int(self.surface.get_width()/8)
        self.end_x = int(self.surface.get_width()*7/8)
        self.end_y = self.surface.get_height() - 20
        self.max_x_words = (self.end_x - self.start_x) // (self.word_size + self.word_gap)
        self.max_y_words = (self.end_y - self.start_y) // (self.word_size/4 + self.word_gap)
        self.max_page_words = int(self.max_x_words * self.max_y_words)
        self.page = 0
        self.max_page = 0
        self.page_boxes = [PageBox(surface, (self.start_x - self.word_gap - self.page_box_size, self.start_y), self.page_box_size, '<'),
                           PageBox(surface, (self.end_x + self.word_gap + self.page_box_size, self.start_y), self.page_box_size, '>')]
        self.word_pages = []

    def draw(self, possible_words, was_change):
        from math import ceil
        # Need to handle a reset and calculation of word pages
        n_words = len(possible_words)
        n_pages = self.max_page
        if was_change:
            # Recalculate the number of pages and reset the buttons
            n_pages = ceil(n_words / self.max_page_words)
            self.max_page = n_pages - 1
            self.page_boxes[0].disable()
            self.page = 0
            if n_pages > 1:
                self.page_boxes[1].enable()
            else:
                self.page_boxes[1].disable()
            # Split the possible_words into pages in a list
            if n_pages == 1:
                self.word_pages = [possible_words]
            else:
                self.word_pages = [possible_words[i : i + self.max_page_words] for i in range(0, len(possible_words), self.max_page_words)]
        # Draw the page boxes
        for pb in self.page_boxes:
            pb.draw()
        # Draw the extra information
        l_surface = pygame.font.SysFont("Calibri", int(self.word_size/5)).render("{} possible words".format(n_words), False, pygame.Color(Y_Color))
        self.surface.blit(l_surface, (self.start_x, self.start_y-(self.word_size/4+self.word_gap)))
        l_surface = pygame.font.SysFont("Calibri", int(self.word_size/5)).render("Page {}/{}".format(self.page+1,self.max_page+1), False, pygame.Color(W_Color))
        self.surface.blit(l_surface, (self.start_x+(self.max_x_words-1)*(self.word_size+self.word_gap), self.start_y-(self.word_size/4+self.word_gap)))
        # Draw the words on the current page
        if n_words == 0:
            return
        for i, word in enumerate(self.word_pages[self.page]):
            x = i % self.max_x_words
            y = i // self.max_x_words
            l_surface = pygame.font.SysFont("Calibri", int(self.word_size/5)).render(word, False, pygame.Color(W_Color))
            self.surface.blit(l_surface, (self.start_x+x*(self.word_size+self.word_gap), self.start_y+y*(self.word_size/4+self.word_gap)))
    
    def areaClicked(self, mx, my):
        for i, pb in enumerate(self.page_boxes):
            if pb.isMousedOver(mx, my):
                if i == 0:
                    self.previousPage()
                elif i == 1:
                    self.nextPage()
    
    def nextPage(self):
        if self.page < self.max_page:
            self.page += 1
        if self.page == self.max_page:
            self.page_boxes[1].disable()
        if self.page > 0:
            self.page_boxes[0].enable()
    
    def previousPage(self):
        if self.page > 0:
            self.page -= 1
        if self.page == 0:
            self.page_boxes[0].disable()
        if self.page < self.max_page:
            self.page_boxes[1].enable()

class PageBox:
    def __init__(self, surface, position, size, character):
        self.surface = surface
        self.position = position
        self.size = size
        self.enabled = False
        self.character = character

    def disable(self):
        self.enabled = False
    
    def enable(self):
        self.enabled = True

    def draw(self):
        rb = pygame.Rect(self.position[0], self.position[1], self.size, self.size)
        if not self.enabled:
            # draw it disabled
            pygame.draw.rect(self.surface, D_Color, rb, 2)
        else:
            # draw it enabled
            pygame.draw.rect(self.surface, D_Color, rb)
        l_surface = pygame.font.SysFont("Calibri", int(self.size/2)).render(self.character, False, pygame.Color(W_Color))
        l_rect = l_surface.get_rect(center=(self.position[0]+int(self.size/2), self.position[1]+int(self.size/2)))
        self.surface.blit(l_surface, l_rect)
    
    def isMousedOver(self, mx, my):
        if self.position[0] <= mx and mx <= self.position[0] + self.size:
            if self.position[1] <= my and my <= self.position[1] + self.size:
                return True
        return False

def LB2Rules(letter_boxes):
    return [[{"letter":lb.letter,"certainty":lb.certainty} for lb in row] for row in letter_boxes]

class Solver:
    def __init__(self):
        file = open("words.txt",'r')
        allwords = [w.strip() for w in file.readlines()]
        print("Number of total English words loaded = {}".format(len(allwords)))
        file.close()
        self.words = [w.upper() for w in allwords if len(w) == 5 and w.isalpha()]
        print("Number of 5 letter English words loaded = {}".format(len(self.words)))
        self.last_result = None
        self.last_rules = None
        self.last_variety_list = None

    def findPossile(self, letter_boxes):
        rules = LB2Rules(letter_boxes)
        if self.last_rules == rules:
            return self.last_result, False
        # Filter based on greens first I think is easiest to start with
        results = [w for w in self.words]
        for word in rules:
            for letter_position, letter in enumerate(word):
                if letter["certainty"] == Certainty.GREEN:
                    results = [w for w in results if w[letter_position] == letter["letter"]]
        # Filter based on the number of GREEN or YELLOW occurances of a letter in a word. This handles grey letters and multiple of the same letter (even mixed Grey,Green,Yellow)
        for word in rules:
            # Count the number of total occurances of each letter in the word
            letter_total_counts = {letter["letter"]:0 for letter in word if letter["letter"] != None}
            for letter in word:
                if letter["letter"] == None:
                    continue
                letter_total_counts[letter["letter"]] += 1
            # Count the number of GREEN or YELLOW occurances of each letter in the word, filter words based on those counts
            letter_colour_counts = {letter["letter"]:0 for letter in word if letter["letter"] != None}
            for letter in word:
                if letter["letter"] == None:
                    continue
                if letter["certainty"] == Certainty.GREEN or letter["certainty"] == Certainty.YELLOW:
                    letter_colour_counts[letter["letter"]] += 1
            # We only want to filter out things if we have TOTAL information for it
            # i.e. if there's only one R in the word and it's green we can't assume there's no other R in the word
            for letter in letter_total_counts:
                if letter_total_counts[letter] == letter_colour_counts[letter]:
                    results = [w for w in results if w.count(letter) >= letter_colour_counts[letter]]
                else:
                    results = [w for w in results if w.count(letter) == letter_colour_counts[letter]]
        # Filter based on the yellow's positions
        for word in rules:
            for letter_position, letter in enumerate(word):
                if letter["certainty"] == Certainty.YELLOW:
                    results = [w for w in results if w[letter_position] != letter["letter"]]
        self.last_result = results
        self.last_rules = rules
        self.updateVarietyWords(rules, results)
        return results, True
    
    def updateVarietyWords(self, rules, possible_words):
        # Return the word containing the most number of letters we've not used, as to figure out the most information possible on the next guess
        letters_in_possible = {letter for word in possible_words for letter in word}
        letters_not_possible = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - letters_in_possible

        letters_in_rules = {letter["letter"] for word in rules for letter in word if letter["letter"] != None}
        important_letters = letters_in_possible - letters_in_rules

        word_scores = {word:0 for word in self.words}
        for word in word_scores:
            # Give 1 point if it contains a letter not yet touched
            for il in list(important_letters):
                if il in word:
                    word_scores[word] += 1
        sorted_words = sorted(word_scores.items(), key=lambda p: p[1], reverse=True)
        words_by_score = [p[0] for p in sorted_words]
        # Filter out any word containing a letter that's not even possible for us
        # (Unless that removes everything we have, in which case keep what we have)
        filtered_words_by_score = [word for word in words_by_score if len(set(word).intersection(letters_not_possible)) == 0]
        if len(filtered_words_by_score) > 0:
            words_by_score = filtered_words_by_score
        self.last_variety_list = words_by_score

    def wordsByVariety(self):
        return self.last_variety_list

pygame.init()
pygame.font.init()
pygame.display.set_mode((1200,800))
pygame.display.set_caption("Wordle Solver")
surface = pygame.display.get_surface()
game = Game(surface)
game.play()
pygame.quit()