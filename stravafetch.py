import requests
import json
import time
import os
from colorama import init, Fore, Style
from datetime import datetime

# Get today's date
today = datetime.today()

# Create a date for the start of the year
start_of_year = datetime(today.year, 1, 1)

# Calculate the number of days since the start of the year
days_since_start = (today - start_of_year).days+1

def get_dot_char(state):
    return {
        0: '○',  # No activity
        1: '●',  # Run
        2: '■',  # Ride
        3: '◆',  # Run + Ride
    }.get(state, '?')

# Resolve paths
script_dir = os.path.dirname(os.path.abspath(__file__))
token_path = os.path.join(script_dir, 'strava_tokens.json')

# End of months
end_of_month_days_non_leap = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]

# Load Strava app credentials and tokens
with open(token_path, 'r') as f:
    tokens = json.load(f)

CLIENT_ID = tokens['client_id']
CLIENT_SECRET = tokens['client_secret']
REFRESH_TOKEN = tokens['refresh_token']
ACCESS_TOKEN = tokens.get('access_token')
EXPIRES_AT = tokens.get('expires_at', 0)

def refresh_access_token():
    global ACCESS_TOKEN, EXPIRES_AT
    if time.time() >= EXPIRES_AT:
        #print("Refreshing Strava access token...")
        response = requests.post("https://www.strava.com/oauth/token", data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': REFRESH_TOKEN
        })
        new_tokens = response.json()
        ACCESS_TOKEN = new_tokens['access_token']
        EXPIRES_AT = new_tokens['expires_at']
        tokens.update(new_tokens)
        with open(token_path, 'w') as f:
            json.dump(tokens, f)
    return ACCESS_TOKEN

def get_activities(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    per_page = 200
    page = 1
    all_activities = []

    print("Fetching activities...")
    while True:
        res = requests.get(
            f'https://www.strava.com/api/v3/athlete/activities?per_page={per_page}&page={page}',
            headers=headers
        )
        try:
            data = res.json()
        except Exception as e:
            print("Failed to parse response JSON:", e)
            print("Raw response:", res.text)
            break

        if isinstance(data, dict) and 'errors' in data:
            print("Strava API returned an error:")
            print(json.dumps(data, indent=2))
            break

        if not data:
            #print(f"No more data on page {page}.")
            break

        all_activities.extend(data)
        page += 1
        time.sleep(1)

    print(f"Total activities fetched: {len(all_activities)}")
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
        activity_type = act.get('type', '')
        date_str = act.get('start_date_local', '')
        distance_m = act.get('distance', 0)

        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
                if date.year == current_year:
                    day = date.timetuple().tm_yday
                    km = round(distance_m / 1000.0, 1)
                    if 'Run' in activity_type:
                        run_days[day] = f"Run {km}km"
                        total_run_km = total_run_km+km
                        total_run_times += 1
                    if 'Ride' in activity_type:
                        ride_days[day] = f"Ride {km}km"
                        total_ride_km = total_ride_km+km
                        total_ride_times += 1 
            except Exception as e:
                print(f"Date parse failed: {e} — {date_str}")
    print("📅 Strava Yearly Grid (Run ",end="")    
    print(Fore.YELLOW + '● ' + Style.RESET_ALL,end="")
    print("/ Ride ",end="")
    print(Fore.BLUE + '■ ' + Style.RESET_ALL,end="")
    print("/ Both ",end="")
    print(Fore.MAGENTA + '◆ ' + Style.RESET_ALL,end="")  # Run + Ride
    print('/ None ',end="")
    print('○ ', end="")
    print('/ Current date ', end="")
    print(Fore.MAGENTA + '◉ ' + Style.RESET_ALL,end="") 
    print(')')
#for row in range(DOT_ROWS):
 #   line = ''
 #   for col in range(DOTS_PER_ROW):
 #       day = col * DOT_ROWS + row  # <-- this aligns vertically by columns
 #       if day < len(state_values):
 #           line += get_dot_char(state_values[day]) + ' '
 #       else:
#            line += '  '
# print(line)
    for i in range(1, 366):
        if i==days_since_start:
            if i in end_of_month_days_non_leap:
                print(Fore.RED + '◉ ' + Style.RESET_ALL)
            else:
                print(Fore.MAGENTA + '◉ ' + Style.RESET_ALL,end="")  # Run + Ride
        elif i in run_days and i in ride_days:
            if i in end_of_month_days_non_leap:
                print(Fore.MAGENTA + '◆ ' + Style.RESET_ALL)
            else:
                print(Fore.MAGENTA + '◆ ' + Style.RESET_ALL,end="")  # Run + Ride
        elif i in run_days: 
            if i in end_of_month_days_non_leap:
                print(Fore.YELLOW + '● ' + Style.RESET_ALL)
            else:
                print(Fore.YELLOW + '● ' + Style.RESET_ALL,end="")     
        elif i in ride_days:
            if i in end_of_month_days_non_leap:
                print(Fore.BLUE + '■ ' + Style.RESET_ALL)
            else:
                print(Fore.BLUE + '■ ' + Style.RESET_ALL,end="")
        else:
            if i in end_of_month_days_non_leap and i < 355:
                print('○ ')
            else:
                print('○ ',end="")
    print('')
    print('Total run: ',end="")
    print((str(round(total_run_times,1))),end="")
    print(' times - ',end="")
    print((str(round(total_run_km,1))),end="")
    print('km |',end="")
    print('  Total ride: ',end="")
    print((str(round(total_ride_times,1))),end="")
    print(' times - ',end="")
    print((str(round(total_ride_km,1))),end="")
    print('km',end="")
        
if __name__ == '__main__':
    access_token = refresh_access_token()
    activities = get_activities(access_token)
    write_run_calendar(activities)
