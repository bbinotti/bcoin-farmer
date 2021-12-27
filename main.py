import time
import os
import argparse
import yaml

import cv2
import numpy as np
import mss
import pyautogui

# TODO features
# after signing in on MM, check that loading screen before next action
# Make sure sign in is successful, loop back to login state if not
# Add check for new map
# Use multiple windows: initial check for number of connect buttons found
# find MM button

pyautogui.PAUSE = .5

# screen_states = ["connect", "mm_sign", "main", "hunting", "heroes"]
state_graph = {
    "connect": ["mm"],
    "mm": ["main"],
    "main": ["hunt"],
    "hunt": ["heroes"],
    "heroes": ["hunt"],
    "new_map": ["hunt"]
}
action_graph = {
    "connect": ["click5"],
    "mm": ["click10"],
    "main": ["click"],
    "hunt": ["2click", "2click"],
    "heroes": ["drag", "work", "2click"], # maybe make an exit action?
    "new_map": ["click"]
}

parser = argparse.ArgumentParser(description='Bot for BombCrypto')
parser.add_argument('--monitor', type=int, default=1, help='Input number of monitor to use. Default monitor 1')

args = parser.parse_args()

def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

def takeScreenshot(capture_mode="main", section_coords=None):
    """Capture partial screenshot of monitor specified in input args"""
    with mss.mss() as sct:
        if capture_mode == 'full':
            mon = sct.monitors[args.monitor]
            return np.array(sct.grab(mon))[:,:,:3]
        elif capture_mode == 'all':
            mon = sct.monitors[0]
            return np.array(sct.grab(mon))[:,:,:3]
        else:
            mon = sct.monitors[args.monitor]
            # section of screenshot, manually set to BombCrypto layout assuming 1920x1080
            monitor = {
                "top": mon["top"] + int(section_coords[capture_mode][1]), 
                "left": mon["left"] + int(section_coords[capture_mode][0]), 
                "width": int(section_coords[capture_mode][2]),
                "height": int(section_coords[capture_mode][3]),
                "mon": args.monitor,
            }
            # return the data
            return np.array(sct.grab(monitor))[:,:,:3]

class Game:
    def __init__(self):
        self.screen_state = ''
        self.hunting = False
        self.game_info = self.findGameCoords()
        self.section_coords = self.getKeyCoordinates(pctDicts=cfg["sections"])
        self.key_coords = self.getKeyCoordinates(pctDicts=cfg["coords"])
        self.checkCurrentScreen()
        self.action_coords = {

            "connect": [self.key_coords["connect_button"]],
            "mm": [self.key_coords["mm_sign_button"]],
            "main": [self.key_coords["hunt_button"]],
            "hunt": [self.key_coords["background_area"], self.key_coords["hero_subpanel"]],
            "heroes": [self.key_coords["hero_drag_area"], self.key_coords["bottom_work_button"], self.key_coords["background_area"]],
            # "heroes_subpanel": [470, 225, 1000, 675],
            "new_map": [self.key_coords["new_map_button"]]

        }
        
        self.printGameInfo()
        print(self.section_coords)
    

    def findGameCoords(self):
        # Method to calculate coordinates of game based off of game's borders
        if not os.path.exists('./usr/user_coordinates.json'):
            img = takeScreenshot(capture_mode='full')
            img = img[:,:,:3]
            
            connect_coords = self.getTemplateCoords(img, cfg["files"]["connect_button_filename"]) # should only take partial screenshot
            # game borders
            tl_border_coords = self.getTemplateCoords(img, cfg["files"]["tl_border_filename"])
            br_border_coords = self.getTemplateCoords(img, cfg["files"]["br_border_filename"])
            game_w = br_border_coords[0] - tl_border_coords[0]
            game_h = br_border_coords[1] - tl_border_coords[1]
        
            game_info = {
                "tl_border": tl_border_coords,
                "br_border": br_border_coords,
                "game_w": game_w,
                "game_h": game_h
            }

            return game_info

    def getTemplateCoords(self, img, template_filename, thresh=0.9):
        template_img = cv2.imread(template_filename)
        t_w, t_h = template_img.shape[0], template_img.shape[1] 
        conv = cv2.matchTemplate(img, template_img, cv2.TM_CCOEFF_NORMED)
        # cv2.imshow("none", conv)
        # cv2.waitKey()
        tmp = np.where(conv > thresh)
        coords = (tmp[1][0] + int(t_h / 2), tmp[0][0] + int(t_w / 2))
        
        return coords

    def checkCurrentScreen(self):
        """
            Read screen at app launch and store current screen state.
        """
        img = takeScreenshot(capture_mode='game', section_coords=self.section_coords)

        # average_r = np.mean(img[:,:,0], axis=(0,1))
        # # brute force checking pixels
        # if 64 < average_r < 70:
        #     screen_state = 'connect'
        # elif 210 < average_r < 220:
        #     screen_state = 'main'
        # elif 145 < average_r < 155:
        #     screen_state = 'heroes'
        # else:
        #     screen_state = 'hunt'

        # cv2.imshow(screen_state, img)
        # cv2.waitKey()
        if self.isGameThisState(cfg["files"]["connect_button_filename"], capture_mode="game"):
            screen_state = 'connect'
        elif self.isGameThisState(cfg["files"]["main_filename"], capture_mode="game"):
            screen_state = 'main'
        elif self.isGameThisState(cfg["files"]["stamina_bar_filename"], capture_mode="game"):
            screen_state = 'heroes'
        else:
            screen_state = 'hunt'
        self.screen_state = screen_state

    def getKeyCoordinates(self, pctDicts):
        # use game border coordinates to calculate key areas coordinates
        key_coords = {}
        game_w = self.game_info["game_w"]
        game_h = self.game_info["game_h"]
        tl_border = self.game_info["tl_border"]
        for key in pctDicts.keys():
            x = np.around((pctDicts[key][0] * game_w) + tl_border[0])
            y = np.around((pctDicts[key][1] * game_h) + tl_border[1])
            if len(pctDicts[key]) > 2:
                x = np.around((pctDicts[key][0] * game_w) + tl_border[0])
                y = np.around((pctDicts[key][1] * game_h) + tl_border[1])
                w = np.around(pctDicts[key][2] * game_w)
                h = np.around(pctDicts[key][3] * game_h)
                key_coords[key] = (x, y, w, h)
            else:
                key_coords[key] = (x, y)

        return key_coords

    # TODO check redundancies
    def isGameThisState(self, template_filename, capture_mode="full", thresh=0.9):
        img = takeScreenshot(capture_mode=capture_mode, section_coords=self.section_coords)
        template_img = cv2.imread(template_filename)
        print(img.shape)
        print(template_img.shape)
        conv = cv2.matchTemplate(img, template_img, cv2.TM_CCOEFF_NORMED)
        # cv2.imshow("none", conv)
        # cv2.waitKey()
        tmp = np.where(conv > thresh)
        if len(tmp[0]) == 0:
            match = False
        else:
            match = True
        # TODO return match and coordinates?
        return match

    def printGameInfo(self):
        # show this game's info
        print("GAME INFO ") # TODO print which game #
        for key in self.game_info.keys():
            print(f'{key}: {self.game_info[key]}')

    def runCycle(self):
        # traverse through the graph from current state to the idling state
        while not self.hunting:
            edges = state_graph[self.screen_state]
            print(f'Current State: {self.screen_state}; Target state: {edges}')
            for edge in edges:
                actions = action_graph[self.screen_state]
                self.performActions(actions)
                self.screen_state = edge

    def performActions(self, actions):
        for i, action in enumerate(actions):
            x = self.action_coords[self.screen_state][i][0] - 1920
            y = self.action_coords[self.screen_state][i][1]
            print(f'action {i}: {action} ({x}, {y})')

            if action == "click":
                pyautogui.click(x, y)
            # TODO crude implementation, find a better way
            elif action == "click5":
                pyautogui.click(x, y)
                time.sleep(5)
            # TODO crude implementation, find a better way
            elif action == "click10":
                pyautogui.click(x, y)
                time.sleep(10)
            elif action == "2click":
                pyautogui.doubleClick(x, y, interval=0.5)
            elif action == "drag":
                s_size = 345 # size of hero window TODO find dynamically
                pyautogui.moveTo(x, y)
                pyautogui.drag(0, -s_size, 1, button='left')
                pyautogui.moveTo(x, y)
                pyautogui.drag(0, -s_size, 1, button='left')
            elif action == "work":
                pyautogui.click(x, y, clicks=15, interval=0.6)
                self.hunting = True


cfg = read_yaml('./config.yml')
def main():
    
    last_check = time.time()
    last_refresh = time.time()
    last_work = time.time()

    game = Game()
    # print(game.game_info["tl_border"], game.game_info["game_w"], game.game_info["game_h"])
    # print(game.isGameThisState(cfg["files"]["new_map_filename"], capture_mode="game"))
    # print(game.isGameThisState(cfg["files"]["connect_button_filename"], capture_mode="game"))
    while True:
        # print(game.screen_state)
        print('Running...')
        current_time = time.time()
        if not game.hunting:
            game.runCycle()
        if current_time - last_check > (cfg["timers"]["check_timer"] * 60):
            print("Checking for changes...")
            if game.isGameThisState(cfg["files"]["new_map_filename"], capture_mode="game"):

            # takeScreenshot for new map or errors
        if current_time - last_refresh > (cfg["timers"]["refresh_timer"] * 60):
            print('Refreshing game...')
            game.hunting = False
            # TODO use back button
            last_refresh = time.time()
        if current_time - last_work > (cfg["timers"]["work_timer"] * 60):
            print('Refreshing workers...')
            game.hunting = False
            last_work = time.time()
        else:
            print(f'Pausing program for {cfg["timers"]["pause_timer"] * 60} seconds...')
            time.sleep(cfg["timers"]["pause_timer"] * 60)

main()