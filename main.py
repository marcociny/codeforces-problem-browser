import requests
import os
import json
import curses
import webbrowser
import sys
import re

USER_HANDLE = "" # edit this with your user handle

cols, lines = os.get_terminal_size()

class Problems:
    all_problems = None
    problems = None
    user_solves = None

    active_filters = []
    is_filter_active = False

    def __init__(self, user_handle):
        self.all_problems = self.get_problems()
        self.problems = self.all_problems
        self.user_solves = self.get_user_solves()

    def get_problems(self):
        return json.loads(requests.get(f"https://codeforces.com/api/problemset.problems").content)["result"]["problems"]
    def get_user_solves(self):
        standings = json.loads(requests.get("https://codeforces.com/api/user.status", params={"handle":USER_HANDLE}).content).get("result")
        if standings is not None:
            ac = [d for d in standings if d.get("verdict") == "OK"]
            user_solves = [standing["problem"]["name"] for standing in ac]
            return set(user_solves)
        else:
            return set()

    def filter(self, type, key):
        key = key.lower()
        self.is_filter_active = True
        self.active_filters.append(f"{type}:{key}")
        if type == "name":
            self.problems = [element for element in self.problems if element["name"].lower().find(key) != -1]
        elif type == "tag":
            self.problems = [element for element in self.problems if key in element["tags"]]
        elif type == "rating":
            key = key.replace(" ", "")
            if key.isdigit():
                self.problems = [element for element in self.problems if "rating" in element and str(element["rating"]) == key]
                return
            sign, number = re.match(r'(\D*)(\d*)', key).groups()
            number = int(number)
            if sign == ">":
                self.problems = [element for element in self.problems if "rating" in element and int(element["rating"]) > number]
                return
            elif sign == ">=":
                self.problems = [element for element in self.problems if "rating" in element and int(element["rating"]) >= number]
                return
            elif sign == "<":
                self.problems = [element for element in self.problems if "rating" in element and int(element["rating"]) < number]
                return
            elif sign == "<=":
                self.problems = [element for element in self.problems if "rating" in element and int(element["rating"]) <= number]
                return
        return
    def unset_filters(self):
        self.active_filters = []
        self.is_filter_active = False
        self.problems = self.all_problems

def get_search_input(w, r, c, prompt_string):
    curses.echo() 
    w.addstr(r, c, prompt_string)
    w.refresh()
    input = w.getstr(r + 0, c + len(prompt_string), 50)
    input = input.decode()
    return input

def search(w, problems, query):
    curses.echo()
    w.addstr(lines-1, 0, " " * (cols-1))
    search_input = get_search_input(w, lines-1, 0, "Search by " + query + ": ")
    curses.noecho()
    if search_input == "":
        return
    problems.filter(query, search_input)
    return
    
def print_problems(w, start, selected, problems):
    w.erase()
    w.addstr("{0:5s}{1:3s}{2:50s}{3:7s}{4:7s}\n".format("CID", "N", "Name", "Rating", "Solved?"))
    idx = 0
    for p in problems.problems[start:(lines-2) + start]:
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
        if p["name"] in problems.user_solves:
            w.attron(curses.color_pair(2))
            w.addstr("{0:7s}".format("YES"))
            w.attroff(curses.color_pair(2))
        else:
            w.attron(curses.color_pair(1))
            w.addstr("{0:7s}".format("NO"))            
            w.attroff(curses.color_pair(1))
        w.addstr("\n")
        idx+=1
    if problems.is_filter_active:
        filters = problems.active_filters
        w.addstr(f"Filter(s): {filters}. Press [q] to reset.")

def handle_input(w, problems, input, selected, start):
    if input == ord("/"): # / key
        search(w, problems, "tag")
        start, selected = 0, 0
        print_problems(w, start, selected, problems)
    elif input == ord("?"): # ? key
        search(w, problems, "name")
        print_problems(w, start, selected, problems)
    elif input == ord("!"):
        search(w, problems, "rating")
        print_problems(w, start, selected, problems)

    elif input == curses.KEY_DOWN:
        selected += 1
    elif input == curses.KEY_UP:
        selected -= 1
    elif input == curses.KEY_RIGHT:
        start += lines
    elif input == curses.KEY_LEFT:
        start -= lines
    elif input == 10: # enter key
        try:
            webbrowser.open("https://codeforces.com/problemset/problem/" + str(problems.problems[selected+start]["contestId"]) + "/" + str(problems.problems[selected+start]["index"]))
        except IndexError:
            pass
    elif input == ord("q"):
        if problems.is_filter_active:
            problems.unset_filters()
            start, selected = 0, 0
            print_problems(w, start, selected, problems)
            return selected, start, False
    elif input == ord("Q"):
        return selected, start, True
    # clamping
    selected = max(0, selected)
    selected = min(lines-3, selected)
    start = max(0, start)
    start = min(len(problems.problems)-1, start)
    return selected, start, False

def init_tui():
    curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1,curses.COLOR_RED,-1)
    curses.init_pair(2,curses.COLOR_GREEN,-1)
    curses.init_pair(3, 246,-1)

def main(stdscr):
    init_tui()
    cols,lines = os.get_terminal_size()
    w = stdscr
    w.keypad(True)
    w.addstr(int(lines/2)-1, int(cols/2)-5, "Loading...")
    w.refresh()
    problems = Problems(USER_HANDLE)
    # handle tui
    start = 0
    selected = 0
    while(True):
        print_problems(w, start, selected, problems)
        input = w.getch()
        selected, start, exit = handle_input(w, problems, input, selected, start)
        if(exit):
            return

if __name__ == "__main__":
    if(len(sys.argv) != 2 and USER_HANDLE == ""):
        print(f"Usage: {sys.argv[0]} [user handle]")
        print("Alternatively, you can edit the USER_HANDLE field in the script.")
        exit()
    USER_HANDLE = sys.argv[1]
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)
