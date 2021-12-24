import time
import sys
import argparse

import cv2
import numpy as np
import mss
import pyautogui

# screen_states = ["connect", "mm_sign", "main", "hunting", "heroes"]
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
    "hunt": [470, 225, 1000, 675],
    "heroes": [470, 225, 1000, 675],
    "heroes_subpanel": [470, 225, 1000, 675]

}

parser = argparse.ArgumentParser(description='Bot for BombCrypto')
parser.add_argument('--monitor', type=int, default=1, help='Input number of monitor to use. Default monitor 1')

args = parser.parse_args()

def prtScreen(screen_state="main"):
    """Capture partial screenshot of monitor specified in input args"""
    with mss.mss() as sct:
        mon = sct.monitors[args.monitor]
        # section of screenshot, manually set to BombCrypto layout assuming 1920x1080
        monitor = {
            "top": mon["top"] + section_coords[screen_state][1],  # 100px from the top
            "left": mon["left"] + section_coords[screen_state][0],  # 100px from the left
            "width": section_coords[screen_state][2],
            "height": section_coords[screen_state][3],
            "mon": args.monitor,
        }
        # return the data
        return np.array(sct.grab(monitor))


class Game:
    def __init__(self, state_graph, action_graph, section_coords, action_coords):
        self.screen_state = ''
        self.idle = False
        self.actions = []
        self.state_graph = state_graph
        self.action_graph = action_graph
        self.section_coords = section_coords
        self.action_coords = action_coords
        self.checkCurrentScreen()
    
    def checkCurrentScreen(self):
        """
            Read screen at app launch and store current screen state.
        """
        img = prtScreen(screen_state='connect')
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
        cv2.imshow(screen_state, img)
        cv2.waitKey()

        self.screen_state = screen_state

    def runCycle(self):
        # traverse through the graph from current state to the idling state
        img = prtScreen(screen_state='connect')

    def performAction(self):
        actions = self.action_graph[self.screen_state]
        for action in actions:
            x = self.action_coords[self.screen_state][0]
            y = self.action_coords[self.screen_state][1]
            print(f'action: {action} ({x}, {y})')
            # if action == "click":
            #     pyautogui.click(x, y)
            # elif action == "2click":
            #     pyautogui.doubleClick(x, y)
            # elif action == "drag":
            #     pyautogui.dragTo(x, y, button='left')


def main():
    # while True:
    #     forward(200)
    #     left(170)
    #     if abs(pos()) < 1:
    #         break
    # end_fill()
    # done()
    # screen_state = checkCurrentScreen()
    state_graph = {
        "connect": {"mm"},
        "mm": {"hunt"},
        "hunt": {"heroes"},
        "heroes": {"heroes", "hunt"}
    }
    action_graph = {
        "connect": {"click"},
        "mm": {"click"},
        "hunt": {"2click", "click"},
        "heroes": {"heroes", "hunt"}
    }
    game = Game(state_graph, action_graph, section_coords, action_coords)
    print(game.screen_state)
    game.performAction()


main()