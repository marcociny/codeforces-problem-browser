import requests
import os
import json
import curses
import webbrowser
import sys

USER_HANDLE = "" # edit this with your user handle

cols, lines = os.get_terminal_size()

def get_problems():
    return json.loads(requests.get(f"https://codeforces.com/api/problemset.problems").content)["result"]["problems"]

def get_user_solves():
    standings = json.loads(requests.get("https://codeforces.com/api/user.status", params={"handle":USER_HANDLE}).content).get("result")
    if standings is not None:
        ac = [d for d in standings if d.get("verdict") == "OK"]
        user_solves = [standing["problem"]["name"] for standing in ac]
        return set(user_solves)
    else:
        return set()

def print_problems(start):
    w.erase()
    w.addstr("{0:5s}{1:3s}{2:50s}{3:7s}{4:7s}\n".format("CID", "N", "Name", "Rating", "Solved?"))
    idx = 0
    for p in problems[start:(lines-2) + start]:
        if idx == selected:
            w.attron(curses.A_BOLD)
        w.addstr("{0:5s}".format(str(p["contestId"])))
        w.addstr("{0:3s}".format(p["index"]))
        w.addstr("{0:50s}".format(p["name"] if len(p["name"]) <= 49 else p["name"][:46] + "..."))
        w.attroff(curses.A_BOLD)
        if p.get("rating") is None:
            w.attron(curses.color_pair(3))
            w.addstr("{0:7s}".format("???"))
            w.attroff(curses.color_pair(3))
        else:
            w.addstr("{0:7s}".format(str(p["rating"])))
        if p["name"] in user_solves:
            w.attron(curses.color_pair(2))
            w.addstr("{0:7s}".format("YES"))
            w.attroff(curses.color_pair(2))
        else:
            w.attron(curses.color_pair(1))
            w.addstr("{0:7s}".format("NO"))            
            w.attroff(curses.color_pair(1))
        w.addstr("\n")
        idx+=1

def init_tui():
    curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1,curses.COLOR_RED,-1)
    curses.init_pair(2,curses.COLOR_GREEN,-1)
    curses.init_pair(3, 246,-1)

def handle_input():
    global selected, start
    if input == curses.KEY_DOWN:
        selected += 1
    elif input == curses.KEY_UP:
        selected -= 1
    elif input == curses.KEY_RIGHT:
        start += lines
    elif input == curses.KEY_LEFT:
        start -= lines
    elif input == 10:
        webbrowser.open("https://codeforces.com/problemset/problem/" + str(problems[selected+start]["contestId"]) + "/" + str(problems[selected+start]["index"]))
    elif input == 27:
        curses.endwin()
        return 1
    # validation
    selected = max(0, selected)
    selected = min(lines-3, selected)
    start = max(0, start)
    start = min(len(problems)-1, start)
    return 0

def main(stdscr):
    global w, problems, user_solves, start, selected, input
    init_tui()
    cols,lines = os.get_terminal_size()
    w = stdscr
    w.keypad(True)
    problems = get_problems()
    user_solves = get_user_solves()
    # handle tui
    start = 0
    selected = 0
    while(True):
        w.move(0,0)
        print_problems(start)
        input = w.getch()
        code = handle_input()
        if(code == 1):
            curses.endwin()
            break

if __name__ == "__main__":
    if(len(sys.argv) != 2 and USER_HANDLE == ""):
        print(f"Usage: {sys.argv[0]} [user handle]")
        print("Alternatively, you can edit the USER_HANDLE field in the script.")
        exit()
    USER_HANDLE = sys.argv[1]
    curses.wrapper(main)
