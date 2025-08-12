import calendar
import json
import os
import time
from collections import namedtuple
from datetime import datetime

import requests
from rich import print
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

# Get today's date
today = datetime.today()


# Create a date for the start of the year
start_of_year = datetime(today.year, 1, 1)

# Calculate the number of days since the start of the year
days_since_start = (today - start_of_year).days + 1

console = Console()

# check if leapyear
leapyear = calendar.isleap(datetime.now().year)

ColorTheme = namedtuple("ColorTheme", "none run ride both today title")
THEME_GRUVBOX = ColorTheme(
    none="#928374",  # faded gray
    run="#fabd2f",  # bright yellow
    ride="#fe8019",  # orange
    both="#b8bb26",  # green
    today="#fb4934",  # red
    title="#d3869b",  # purple
)
THEME_NORD = ColorTheme(
    none="#4c566a",  # gray
    run="#88c0d0",  # light blue
    ride="#81a1c1",  # darker blue
    both="#a3be8c",  # green
    today="#bf616a",  # red
    title="#b48ead",  # purple
)
THEME_CATPPUCCIN = ColorTheme(
    none="#6c7086",  # overlay
    run="#f9e2af",  # yellow
    ride="#f38ba8",  # red-pink
    both="#a6e3a1",  # green
    today="#eba0ac",  # rose
    title="#cba6f7",  # lavender
)

THEME_SOLARIZED_LIGHT = ColorTheme(
    none="#93a1a1",  # base1
    run="#b58900",  # yellow
    ride="#cb4b16",  # orange
    both="#859900",  # green
    today="#dc322f",  # red
    title="#6c71c4",  # violet
)

# Choose theme
THEME = THEME_SOLARIZED_LIGHT


def get_dot_char(state):
    return {
        0: ("○ ", THEME.none),  # No activity
        1: ("● ", THEME.run),  # Run
        2: ("■ ", THEME.ride),  # Ride
        3: ("◆ ", THEME.both),  # Run + Ride
        4: ("◉ ", THEME.today),  # Today
    }.get(state, "?")


# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
token_path = os.path.join(script_dir, "strava_tokens.json")


# End of months
end_of_month_days = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
end_of_month_days_leap = [31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
if leapyear:
    end_of_month_days = end_of_month_days_leap

# Load Strava app credentials and tokens
with open(token_path, "r") as f:
    tokens = json.load(f)

CLIENT_ID = tokens["client_id"]
CLIENT_SECRET = tokens["client_secret"]
REFRESH_TOKEN = tokens["refresh_token"]
ACCESS_TOKEN = tokens.get("access_token")
EXPIRES_AT = tokens.get("expires_at", 0)


def refresh_access_token():
    global ACCESS_TOKEN, EXPIRES_AT
    if time.time() >= EXPIRES_AT:
        # print("Refreshing Strava access token...")
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN,
            },
        )
        new_tokens = response.json()
        ACCESS_TOKEN = new_tokens["access_token"]
        EXPIRES_AT = new_tokens["expires_at"]
        tokens.update(new_tokens)
        with open(token_path, "w") as f:
            json.dump(tokens, f)
    return ACCESS_TOKEN


def get_activities(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    per_page = 200
    page = 1
    all_activities = []

    while True:
        with console.status("Fetching activities", spinner="material"):
            res = requests.get(
                f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}&page={page}",
                headers=headers,
            )
            try:
                data = res.json()
            except Exception as e:
                print("Failed to parse response JSON:", e)
                print("Raw response:", res.text)
                break

            if isinstance(data, dict) and "errors" in data:
                print("Strava API returned an error:")
                print(json.dumps(data, indent=2))
                break

            if not data:
                # print(f"No more data on page {page}.")
                break

            all_activities.extend(data)
            page += 1
            time.sleep(1)

    # console.print(f"Total activities fetched: [#98971a]{len(all_activities)}[/#98971a]")
    return all_activities


def write_run_calendar(activities):
    run_days = {}
    ride_days = {}
    current_year = datetime.now().year
    total_run_km = 0
    total_ride_km = 0
    total_run_times = 0
    total_ride_times = 0
    for act in activities:
        activity_type = act.get("type", "")
        date_str = act.get("start_date_local", "")
        distance_m = act.get("distance", 0)

        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
                if date.year == current_year:
                    day = date.timetuple().tm_yday
                    km = round(distance_m / 1000.0, 1)
                    if "Run" in activity_type:
                        run_days[day] = f"Run {km}km"
                        total_run_km += km
                        total_run_times += 1
                    if "Ride" in activity_type:
                        ride_days[day] = f"Ride {km}km"
                        total_ride_km += km
                        total_ride_times += 1
            except Exception as e:
                print(f"Date parse failed: {e} — {date_str}")
        # Build a title with styled parts
    title = Text("(", style="bold")

    title.append("Run ")
    title.append(*get_dot_char(1))  # Styled dot
    title.append("/ Ride ")
    title.append(*get_dot_char(2))
    title.append("/ Both ")
    title.append(*get_dot_char(3))
    title.append("/ None ")
    title.append(*get_dot_char(0))
    title.append("/ Current date ")
    title.append(*get_dot_char(4))
    title.append(")")

    days = 366
    if leapyear:
        days = 367

    dot_chars = []
    for i in range(1, days):
        if i == days_since_start:
            dot_chars.append(get_dot_char(4))
        elif i in run_days and i in ride_days:
            dot_chars.append(get_dot_char(3))
        elif i in run_days:
            dot_chars.append(get_dot_char(1))
        elif i in ride_days:
            dot_chars.append(get_dot_char(2))
        else:
            dot_chars.append(get_dot_char(0))
        if i in end_of_month_days:
            dot_chars.append(("\n", ""))
    joined_dot_chars = Text.assemble(*dot_chars)
    text = Text()
    #    text.append("Total run: ")
    text.append(
        f"          {total_run_times}", style=f"bold {get_dot_char(1)[1]}"
    )  # Styled number
    text.append(" runs - ")
    text.append(
        f"{round(total_run_km, 1)}", style=f"bold {get_dot_char(1)[1]}"
    )  # Styled number
    text.append(" km | ")
    #    text.append(" km | Total ride: ")
    text.append(
        f"{total_ride_times}", style=f"bold {get_dot_char(2)[1]}"
    )  # Styled number
    text.append(" rides - ")
    text.append(
        f"{round(total_ride_km)}", style=f"bold {get_dot_char(2)[1]}"
    )  # Styled number
    text.append(" km ")

    group = Group(
        title,
        joined_dot_chars,
        text,
    )
    paneltitle = Text("Stravafetch", style=f"bold {THEME.title}")
    panel = Panel(group, title=paneltitle, expand=False)
    console.print(panel)


if __name__ == "__main__":
    access_token = refresh_access_token()
    activities = get_activities(access_token)
    write_run_calendar(activities)
