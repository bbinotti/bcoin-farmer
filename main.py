import time
import os
import argparse
import yaml

import cv2
import numpy as np
import mss
import pyautogui

# import config as cfg

pyautogui.PAUSE = .5

# screen_states = ["connect", "mm_sign", "main", "hunting", "heroes"]
state_graph = {
    "connect": ["mm"],
    "mm": ["main"],
    "main": ["hunt"],
    "hunt": ["heroes"],
    "heroes": ["hunt"]
}
action_graph = {
    "connect": ["click5"],
    "mm": ["click10"],
    "main": ["click"],
    "hunt": ["2click", "2click"],
    "heroes": ["drag", "work", "2click"] # maybe make an exit action?
}

parser = argparse.ArgumentParser(description='Bot for BombCrypto')
parser.add_argument('--monitor', type=int, default=1, help='Input number of monitor to use. Default monitor 1')

args = parser.parse_args()

def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

# populating coordinates dynamically
def calibrateCoordinates():
    if not os.path.exists('./usr/user_coordinates.json'):
        img = prtScreen(capture_mode='full')
        img = img[:,:,:3]
        
        connect_coords = getTemplateCoords(img, cfg["files"]["connect_button_filename"])
        print(connect_coords)
        tl_border_coords = getTemplateCoords(img, cfg["files"]["tl_border_filename"])
        print(tl_border_coords)
        br_border_coords = getTemplateCoords(img, cfg["files"]["br_border_filename"])
        print(br_border_coords)


def getTemplateCoords(img, template_filename, thresh=0.9):
    template_img = cv2.imread(template_filename)
    t_w, t_h = template_img.shape[0], template_img.shape[1] 
    conv = cv2.matchTemplate(img, template_img, cv2.TM_CCOEFF_NORMED)
    # cv2.imshow("none", conv)
    # cv2.waitKey()
    tmp = np.where(conv > thresh)
    coords = (tmp[0][0] + int(t_w / 2), tmp[1][0] + int(t_h / 2))
    return coords


def prtScreen(capture_mode="main", section_coords=None):
    """Capture partial screenshot of monitor specified in input args"""
    with mss.mss() as sct:
        if capture_mode == 'full':
            mon = sct.monitors[args.monitor]
            return np.array(sct.grab(mon))
        elif capture_mode == 'all':
            mon = sct.monitors[0]
            return np.array(sct.grab(mon))
        else:
            mon = sct.monitors[args.monitor]
            # section of screenshot, manually set to BombCrypto layout assuming 1920x1080
            monitor = {
                "top": mon["top"] + section_coords[capture_mode][1], 
                "left": mon["left"] + section_coords[capture_mode][0], 
                "width": section_coords[capture_mode][2],
                "height": section_coords[capture_mode][3],
                "mon": args.monitor,
            }
            # return the data
            return np.array(sct.grab(monitor))

class Game:
    def __init__(self, section_coords, action_coords):
        self.screen_state = ''
        self.hunting = False
        self.section_coords = section_coords
        self.action_coords = action_coords
        self.checkCurrentScreen()
    
    def checkCurrentScreen(self):
        """
            Read screen at app launch and store current screen state.
        """
        img = prtScreen(capture_mode='connect', section_coords=self.section_coords)

        average_r = np.mean(img[:,:,0], axis=(0,1))
        print(average_r)
        # brute force checking pixels
        if 64 < average_r < 70:
            screen_state = 'connect'
        elif 210 < average_r < 220:
            screen_state = 'main'
        elif 145 < average_r < 155:
            screen_state = 'heroes'
        else:
            screen_state = 'hunt'
        # cv2.imshow(screen_state, img)
        # cv2.waitKey()

        self.screen_state = screen_state

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
    section_coords = {

        "connect": [830, 670, 280, 100],
        "mm_sign": [470, 225, 1000, 675],
        "main": [470, 225, 1000, 675],
        "hunt": [470, 225, 1000, 675],
        "heroes": [470, 225, 1000, 675],
        "heroes_subpanel": [470, 225, 1000, 675],

    }
    action_coords = {

        "connect": [cfg["coords"]["connect_button"]],
        "mm": [cfg["coords"]["mm_sign_button"]],
        "main": [cfg["coords"]["hunt_button"]],
        "hunt": [cfg["coords"]["background_area"], cfg["coords"]["hero_subpanel"]],
        "heroes": [cfg["coords"]["hero_drag_area"], cfg["coords"]["bottom_work_button"], cfg["coords"]["background_area"]],
        "heroes_subpanel": [470, 225, 1000, 675]

    }

    last_check = 0
    last_refresh = 0
    last_work = 0

    calibrateCoordinates()
    game = Game(section_coords, action_coords)
    # while True:
    #     # print(game.screen_state)
    #     print('Running...')
    #     current_time = time.time()
    #     if not game.hunting:
    #         game.runCycle()
    #     if current_time - last_check > (cfg["timers"]["check_timer"] * 60):
    #         print("Checking for changes...")
    #         # prtScreen for new map or errors
    #     if current_time - last_refresh > (cfg["timers"]["refresh_timer"] * 60):
    #         print('Refreshing game...')
    #         game.hunting = False
    #         # TODO use back button
    #         last_refresh = time.time()
    #     if current_time - last_work > (cfg["timers"]["work_timer"] * 60):
    #         print('Refreshing workers...')
    #         game.hunting = False
    #         last_work = time.time()
    #     else:
    #         print(f'Pausing program for {cfg["timers"]["pause_timer"] * 60} seconds...')
    #         time.sleep(cfg["timers"]["pause_timer"] * 60)

main()