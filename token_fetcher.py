import json
import requests
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

console = Console()


def section(title):
    console.print(Panel(title, style="bold cyan", expand=False))


# Step 1 – API Setup
section("Step 1️⃣  Setting up the Strava API")

console.print(
    """
[bold green]Welcome to the Strava Fetcher! 🏃‍♂️[/bold green]

To create your app:
[bold]-[/bold] Visit [blue underline]https://www.strava.com/settings/api[/blue underline]
[bold]-[/bold] Set category to: [bold]Visualizer[/bold]
[bold]-[/bold] App name: [italic]statfetcher[/italic] (avoid using "strava")
[bold]-[/bold] Website: [italic]https://github.com/AndersHackerMand/stravafetch[/italic]
[bold]-[/bold] Callback domain: [italic]localhost[/italic]
[bold]-[/bold] Upload any image to complete
"""
)

YOUR_CLIENT_ID = Prompt.ask("🔑 [bold yellow]Enter your Client ID[/bold yellow]")
YOUR_CLIENT_SECRET = Prompt.ask(
    "🔒 [bold yellow]Enter your Client Secret[/bold yellow]"
)

# Step 2 – OAuth Flow
section("Step 2️⃣  Authorize OAuth 2.0")
auth_url = f"https://www.strava.com/oauth/authorize?client_id={YOUR_CLIENT_ID}&response_type=code&redirect_uri=http://localhost/callback&approval_prompt=force&scope=read,activity:read_all"
# Just print it raw and unstyled
# console.print("\n🌐 Open this link in your browser to authorize access:", markup=False)
print(auth_url + "\n")  # Print the full URL in one line
console.print(
    "Once redirected, press authorize, this will redirect you to an error page. From the url of this page copy the value between [bold]code=[/bold] and [bold]&[/bold] in the URL and paste it below.\n"
)

code = Prompt.ask("🔗 [bold green]Paste code[/bold green]")

# Step 3 – Token Exchange
section("Step 3️⃣  Getting Access Token")

response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": YOUR_CLIENT_ID,
        "client_secret": YOUR_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    },
)

data = response.json()

formatted_token = {
    "client_id": YOUR_CLIENT_ID,
    "client_secret": YOUR_CLIENT_SECRET,
    "access_token": data.get("access_token", ""),
    "refresh_token": data.get("refresh_token", ""),
    "expires_at": data.get("expires_at", 0),
    "token_type": data.get("token_type", ""),
    "expires_in": data.get("expires_in", 0),
}

with open("strava_tokens.json", "w") as f:
    json.dump(formatted_token, f, indent=4)

console.print(
    "💾 [bold green]Token saved to[/bold green] [italic]strava_tokens.json[/italic]"
)

# Step 4 – Validate Token
section("Step 4️⃣  Validating Token with Strava")

access_token = formatted_token["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)

if response.status_code == 200:
    console.print(
        "✅ [bold green]Token is valid! Here is your athlete data:[/bold green]\n"
    )
    json_output = json.dumps(response.json(), indent=4)
    syntax = Syntax(json_output, "json", theme="monokai", line_numbers=True)
    console.print(syntax)
else:
    console.print(
        f"❌ [bold red]Token failed. Status:[/bold red] {response.status_code}"
    )
    console.print(f"[red]Message: {response.text}[/red]")

# Step 5 – Finish
section("🎉 All Done!")
# Run stravafetch.py after saving tokens
print("\n🚀 Running stravafetch.py to fetch your activity data...\n")
subprocess.run(["python", "stravafetch.py"])
console.print(
    "[bold green]You can now run[/bold green] [italic]python stravafetch.py[/italic] to fetch your activity data!"
)
