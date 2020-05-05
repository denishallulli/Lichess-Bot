import sys, re, time, pyautogui, chess, chess.engine, chess.polyglot, math, random as rand
import selenium.webdriver as driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

browser = driver.Chrome()
link = "https://lichess.org/login?referrer=/"
browser.get(link)

class Bot:

    def __init__(self):
        self.board = chess.Board()
        self.moves_game = []
        self.black_entered_match = [False]
        self.cache = -1 
        self.elapsed_time = 0
        self.attackers = [0]
        self.instant_moves = rand.randint(3,6)
        self.thought_about_mate = False
        self.pos_w = self.__create_dic('w')
        self.pos_b = self.__create_dic('b')
        self.WAIT_TIME = 3600

    def __extract_credentials(self, file):
        string1 = file.readline()
        string2 = file.readline()
        extract_u = string1[string1.index(':') + 1:len(string1)-1]
        extract_p = string2[string2.index(':') + 1:]
        username = extract_u[len(extract_u) - len(extract_u.lstrip()):]
        password = extract_p[len(extract_p) - len(extract_p.lstrip()):]

        return username, password

    def __moves_history(self):
        try:
            WebDriverWait(browser, self.WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, "//div[@class='moves']/m2[@class='active']")))    
        finally:
            try:
                WebDriverWait(browser, self.WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, "//div[@class='moves']/m2")))
            finally:
                elements = browser.find_elements_by_xpath("//div[@class='moves']/m2")
                self.moves_game = []
                for element in elements:
                    self.moves_game.append(element.get_attribute('innerText'))
                active_move = browser.find_element_by_xpath("//div[@class='moves']/m2[@class='active']").get_attribute('innerText')
                if self.moves_game[-1] != active_move:
                    self.moves_game.append(active_move) 

    def  __create_dic(self, side):

        dic = {}

        if side == 'b':
            for i in range(8,0,-1):
                j = 0
                for letter in ('h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'):
                    tile = letter + str(i)
                    dic[tile] = (382 + j*61, 618 - (8-i)*61)
                    j += 1
        else:
            for i in range(8):
                j = 0
                for letter in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'):
                    tile = letter + str(i+1)
                    dic[tile] = (382 + j*61, 618 - i*61)
                    j += 1
        return dic

    def  __load_engine_as_white(self):
        try:
            WebDriverWait(browser, self.WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='main-wrap']/main/div[1]/div[1]/div/cg-helper/cg-container/cg-board/piece[28]")))
        finally:
            return True
    
    def __find_attackers(self, side):

        num_attackers = 0

        if side == 'black':
            for piece_pos in self.board.piece_map():
                if str(self.board.piece_at(piece_pos)) in ['p', 'q', 'r', 'n', 'b', 'k']:
                    num_attackers += len(self.board.attackers(chess.WHITE, piece_pos))
        
        elif side == 'white':
            for piece_pos in self.board.piece_map():
                if str(self.board.piece_at(piece_pos)) in ['P', 'Q', 'R', 'N', 'B', 'K']:
                    num_attackers += len(self.board.attackers(chess.BLACK, piece_pos))
        
        self.attackers.append(num_attackers)
        
    
    def __move_type(self, side, move_pos, num_moves):
        if num_moves > 1:
            self.__find_attackers(side)

            if self.attackers[-1] - self.attackers[-2] > 0:
                new_attackers = self.attackers[-1] - self.attackers[-2]
            else:
                new_attackers = 0

            if re.search(r'x[a-h][1-8]', self.moves_game[-1]) and self.moves_game[-1][2:] == move_pos:
                    recapture_piece = True
            else:
                recapture_piece = False
                            
            if re.search(r'Q[a-h][1-8]', self.moves_game[-1]) and self.moves_game[-1][1:] == move_pos:
                queen_blunder = True
            else:
                queen_blunder = False

            return recapture_piece, queen_blunder, new_attackers
        else:
            return False, False, False
    
    def __wait_time(self, side, score_change, num_until_mate, move_pos, promotion):

        if side == 'black':
            n_moves = self.board.fullmove_number - 1
        else:
            n_moves = self.board.fullmove_number
        
        quick_moves = [rand.randint(9,35) for _ in range(5)]
        recapture, Qblunder, n_attacks = self.__move_type(side, move_pos, n_moves)

        if  n_moves < self.instant_moves or recapture or Qblunder or self.elapsed_time >= 50 or (n_moves in quick_moves) or self.thought_about_mate or promotion:
            return 0
        elif num_until_mate < 7:
            if num_until_mate < 3:
                return 0
            else:
                self.thought_about_mate = True
                return num_until_mate + (num_until_mate - rand.randint(2,4))**2/3-3
        else:
            thinking_time = rand.uniform(0.1,0.3) + 0.3*n_attacks + math.exp((abs(score_change)-7)*(9-abs(score_change))/10)*rand.uniform(4,6)

            if thinking_time + self.elapsed_time > 51:
                return 51 - self.elapsed_time
            elif self.elapsed_time > 45:
                return rand.uniform(0.1,0.3) + 0.3*n_attacks + math.exp((abs(score_change)-7)*(9-abs(score_change))/10)*rand.uniform(1,3)
            else:
                return thinking_time

    def  __move_piece(self, engine, book, side):

        score_change = 0
        moves_mate =  math.inf
        promote_to_Q = False

        if len(self.moves_game) != 0:
            self.board.push_san(self.moves_game[-1])
        
        if sum(1 for _ in book.find_all(self.board)) != 0:
            for entry in book.find_all(self.board):
                next_move = entry.move
                self.board.push(next_move)
                break
        else:
            if self.elapsed_time < 50:
                score_prior = engine.analyse(self.board, chess.engine.Limit(time=0.2))
                engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
                next_move = engine_move.move
                self.board.push(next_move)
                if len(str(next_move)) == 5 and str(next_move)[-1] == 'q':
                    promote_to_Q = True
                if not promote_to_Q:
                    score_after = engine.analyse(self.board, chess.engine.Limit(time=0.2))
                    if str(score_after["score"])[0] == '#':
                        moves_mate = int(str(score_after["score"])[2:])
                    else:
                        score_change = (int(str(score_after["score"])) - int(str(score_prior["score"])))/100
            else:
                engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
                next_move = engine_move.move
                self.board.push(next_move)

        start_click = str(next_move)[0:2]
        end_click = str(next_move)[2:4]

        if side == 'white':
            start_pos = self.pos_w[start_click]
            end_pos = self.pos_w[end_click]
        else:
            start_pos = self.pos_b[start_click]
            end_pos = self.pos_b[end_click]

        time.sleep(self.__wait_time(side, score_change, moves_mate, end_click, promote_to_Q))
        pyautogui.click(start_pos[0], start_pos[1])
        pyautogui.click(end_pos[0], end_pos[1])
        if promote_to_Q:
            pyautogui.click(end_pos[0], end_pos[1])

    def is_match_over(self):
        return (len(browser.find_elements_by_xpath('//*[@id="main-wrap"]/main/div[1]/div[5]/div[2]/div[@class="result-wrap"]')) != 0)
    
    def find_side(self):
        try:
            WebDriverWait(browser, self.WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main-wrap"]/main/div[1]/div[1]/div/cg-helper/cg-container/cg-board')))
        finally:
            string = browser.find_element_by_xpath('/html/body/script[3]').get_attribute('innerHTML')
            idx = re.search(r'\bcolor\b', string)
            if re.search(r'\binitialFen\b', string):
                return string[idx.end()+3: idx.end()+8]
            else:
                return 'NULL'

    def login(self, file):
        usrname, passwrd = self.__extract_credentials(file)
        browser.find_element_by_xpath('//*[@id="form3-username"]').send_keys(usrname)
        browser.find_element_by_xpath('//*[@id="form3-password"]').send_keys(passwrd)
        browser.find_element_by_xpath('//*[@id="form3-password"]').send_keys(Keys.ENTER)

    def play_move(self, engine, book, side):

        if side == 'black':
            self.__moves_history()
            if len(self.moves_game)%2 != 0 and len(self.moves_game) > self.cache:
                start_time = time.time()
                self.cache = len(self.moves_game)
                self.__move_piece(engine, book, side)
                self.elapsed_time += time.time() - start_time

        elif side == 'white':
            if not self.black_entered_match[-1]:
                self.black_entered_match.append(self.__load_engine_as_white())
                    
            if len(self.moves_game)%2 == 0 and self.black_entered_match and len(self.moves_game) > self.cache:
                start_time = time.time()
                self.cache = len(self.moves_game)
                self.__move_piece(engine, book, side)
                self.elapsed_time += time.time() - start_time
            self.__moves_history()

def main():
    
    #login_info = open('credentials.txt', 'r')
    logged_in = False 
    engine = chess.engine.SimpleEngine.popen_uci("engine")
    book = chess.polyglot.open_reader("lichess_bot.bin")
    engine.configure({"UCI_Elo": "1900", "Hash": "64"})

    while True:

        game_finished = False
        searching_side = True
        Lela = Bot()

        if not logged_in:
            #Lela.login(login_info)
            logged_in = True

        while not game_finished:
            if Lela.is_match_over():
                game_finished = True
            else:
                if searching_side:
                    side = Lela.find_side()
                    if not side == 'NULL':
                        searching_side = False
                if side == 'black' or side == 'white':
                    Lela.play_move(engine, book, side)

if __name__ == "__main__":
    main()
    browser.quit()