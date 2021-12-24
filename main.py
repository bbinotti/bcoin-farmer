import time
import sys
import argparse

import cv2
import numpy as np
import mss
import pyautogui

pyautogui.PAUSE = .5

# screen_states = ["connect", "mm_sign", "main", "hunting", "heroes"]
state_graph = {
    "connect": ["mm"],
    "mm": ["hunt"],
    "hunt": ["heroes"],
    "heroes": ["hunt"]
}
action_graph = {
    "connect": ["click"],
    "mm": ["click"],
    "hunt": ["2click", "2click"],
    "heroes": ["drag", "work", "2click"] # maybe make an exit action?
}

parser = argparse.ArgumentParser(description='Bot for BombCrypto')
parser.add_argument('--monitor', type=int, default=1, help='Input number of monitor to use. Default monitor 1')

args = parser.parse_args()
class Game:
    def __init__(self, section_coords, action_coords):
        self.screen_state = ''
        self.working = False
        self.actions = []
        self.section_coords = section_coords
        self.action_coords = action_coords
        self.checkCurrentScreen()
    
    def checkCurrentScreen(self):
        """
            Read screen at app launch and store current screen state.
        """
        img = self.prtScreen(screen_state='connect')
        print(np.mean(img[:,:,0], axis=(0,1)))
        print(img[10,10,0])

        # brute force checking pixels
        if 65 < np.mean(img[:,:,0], axis=(0,1)) < 70:
            screen_state = 'connect'
        elif 210 < np.mean(img[:,:,0], axis=(0,1)) < 220:
            screen_state = 'main'
        elif 145 < np.mean(img[:,:,0], axis=(0,1)) < 155:
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
        while not self.working:
            edges = state_graph[self.screen_state]
            print(edges)
            for edge in edges:
                actions = action_graph[self.screen_state]
                self.performActions(actions)
                self.screen_state = edge


    def performActions(self, actions):
        for i, action in enumerate(actions):
            x = self.action_coords[self.screen_state][2*i] - 1920
            y = self.action_coords[self.screen_state][(2*i)+1]
            print(f'action {i}: {action} ({x}, {y})')
            if action == "click":
                pyautogui.click(x, y)
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
                self.working = True


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

        "connect": [830, 670, 280, 100],
        "mm_sign": [470, 225, 1000, 675],
        "main": [470, 225, 1000, 675],
        "hunt": [1207, 341, 972, 825],
        "heroes": [620, 720, 888, 730, 1207, 341],
        "heroes_subpanel": [470, 225, 1000, 675]

    }
    game = Game(section_coords, action_coords)
    while True:
        # print(game.screen_state)
        # game.performActions()
        game.working = False
        game.runCycle()


main()