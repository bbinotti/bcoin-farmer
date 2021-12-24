import time
import sys
import argparse

import cv2
import numpy as np
import mss
import pyautogui

import config as cfg

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
        img = self.prtScreen(screen_state='connect')

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

    def prtScreen(self, screen_state="main"):
        """Capture partial screenshot of monitor specified in input args"""
        with mss.mss() as sct:
            mon = sct.monitors[args.monitor]
            # section of screenshot, manually set to BombCrypto layout assuming 1920x1080
            monitor = {
                "top": mon["top"] + self.section_coords[screen_state][1],  # 100px from the top
                "left": mon["left"] + self.section_coords[screen_state][0],  # 100px from the left
                "width": self.section_coords[screen_state][2],
                "height": self.section_coords[screen_state][3],
                "mon": args.monitor,
            }
            # return the data
            return np.array(sct.grab(monitor))

    # pseudocode for populating coordinates dynamically
    # def findCoordinates(self):
    #     actions = action_graph[self.screen_state]
    #     for action in actions:
    #         self.action_coords[self.screen_state].append(findButton() + monitor_difference)

    def runCycle(self):
        # traverse through the graph from current state to the idling state
        while not self.hunting:
            edges = state_graph[self.screen_state]
            print(f'Target state: {edges}')
            for edge in edges:
                actions = action_graph[self.screen_state]
                self.performActions(actions)
                self.screen_state = edge

    def performActions(self, actions):
        for i, action in enumerate(actions):
            print(self.action_coords[self.screen_state][i])
            x = self.action_coords[self.screen_state][i][0] - 1920
            y = self.action_coords[self.screen_state][i][1]
            print(f'action {i}: {action} ({x}, {y})')
            if action == "click":
                pyautogui.click(x, y)
            elif action == "click5":
                pyautogui.click(x, y)
                time.sleep(5)
            elif action == "click10":
                pyautogui.click(x, y)
                time.sleep(10)
            elif action == "2click":
                pyautogui.doubleClick(x, y, interval=0.5)
            elif action == "drag":
                s_size = 345 # size of hero window TODO find dynamically
                pyautogui.moveTo(x, y)
                # pyautogui.dragTo(x, y-s_size, button='left')
                pyautogui.drag(0, -s_size, 1, button='left')
                pyautogui.moveTo(x, y)
                pyautogui.drag(0, -s_size, 1, button='left')
            elif action == "work":
                pyautogui.click(x, y, clicks=15, interval=0.6)
                self.hunting = True


def main():
    
    section_coords = {

        "connect": [830, 670, 280, 100],
        "mm_sign": [470, 225, 1000, 675],
        "main": [470, 225, 1000, 675],
        "hunt": [470, 225, 1000, 675],
        "heroes": [470, 225, 1000, 675],
        "heroes_subpanel": [470, 225, 1000, 675]

    }
    action_coords = {

        "connect": [cfg.connect_button],
        "mm": [cfg.mm_sign_button],
        "main": [cfg.hunt_button],
        "hunt": [cfg.background_area, cfg.hero_subpanel],
        "heroes": [cfg.hero_drag_area, cfg.bottom_work_button, cfg.background_area],
        "heroes_subpanel": [470, 225, 1000, 675]

    }

    start_time = time.time()
    game = Game(section_coords, action_coords)
    while True:
        # print(game.screen_state)
        print('Running...')
        time_diff = time.time() - start_time
        if not game.hunting:
            game.runCycle()
        if time_diff > (cfg.check_timer * 60):
            print("Checking for changes...")
            # prtScreen for new map or errors
        if time_diff > (cfg.refresh_timer * 60):
            print('Refreshing game...')
            game.hunting = False
            # TODO use back button
            start_time = time.time()
        if time_diff > (cfg.work_timer * 60):
            print('Refreshing workers...')
            game.hunting = False
            start_time = time.time()
        else:
            print(f'Pausing program for {cfg.pause_timer * 60} seconds...')
            time.sleep(cfg.pause_timer * 60)

main()