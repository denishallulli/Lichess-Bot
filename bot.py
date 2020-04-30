import sys, re, time, pyautogui, chess, chess.engine, random as rand
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
                    dic[tile] = (382 + j*63, 618 - (8-i)*63)
                    j += 1
        else:
            for i in range(8):
                j = 0
                for letter in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'):
                    tile = letter + str(i+1)
                    dic[tile] = (382 + j*63, 618 - i*63)
                    j += 1
        return dic

    def  __load_engine_as_white(self):
        try:
            WebDriverWait(browser, self.WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='main-wrap']/main/div[1]/div[1]/div/cg-helper/cg-container/cg-board/piece[28]")))
        finally:
            return True

    def  __move_piece(self, engine, side):
        if len(self.moves_game) != 0:
            self.board.push_san(self.moves_game[-1])
        engine_move = engine.play(self.board, chess.engine.Limit(time=0.1))
        
        self.board.push(engine_move.move)

        start_click = str(engine_move.move)[0:2]
        end_click = str(engine_move.move)[2:4]

        if side == 'white':
            start_pos = self.pos_w[start_click]
            end_pos = self.pos_w[end_click]
        else:
            start_pos = self.pos_b[start_click]
            end_pos = self.pos_b[end_click]

        pyautogui.click(start_pos[0], start_pos[1])
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

    def play_move(self, engine, side):

        if side == 'black':
            self.__moves_history()
            if len(self.moves_game)%2 != 0 and len(self.moves_game) > self.cache:
                self.cache = len(self.moves_game)
                self.__move_piece(engine, side)

        elif side == 'white':
            if not self.black_entered_match[-1]:
                self.black_entered_match.append(self.__load_engine_as_white())
                    
            if len(self.moves_game)%2 == 0 and self.black_entered_match and len(self.moves_game) > self.cache:
                self.cache = len(self.moves_game)
                self.__move_piece(engine, side)
            self.__moves_history()



def main():
    
    login_info = open('credentials.txt', 'r')
    logged_in = False 
    engine = chess.engine.SimpleEngine.popen_uci("engine")

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
                    Lela.play_move(engine, side)

if __name__ == "__main__":
    main()
    browser.quit()