# Ad Clicker Bot

This Python application uses Selenium to automatically interact with ads on the website ai-art-fake.onrender.com. It simulates human behavior by moving the mouse, scrolling, and clicking on various ad elements.

## Features

- Clicks on various types of ads (banners, social bars, pop-unders)
- Closes any new tabs that open after clicking ads
- Simulates human behavior with random mouse movements and scrolling
- Runs for a configurable duration (default: 5-6 minutes)

## Requirements

- Python 3.7 or higher
- Chrome browser installed

## Installation

1. Clone this repository or download the files
2. Install required packages:

```
pip install -r requirements.txt
```

## Usage

Simply run the script:

```
python ad_clicker.py
```

The script will:
1. Open a Chrome browser window
2. Navigate to ai-art-fake.onrender.com
3. Begin simulating human browsing behavior
4. Click on detected ad elements
5. Close any new tabs that open
6. Continue this process for 5-6 minutes
7. Automatically close the browser when finished

## Customization

You can modify the following parameters in the script:
- `duration_minutes`: Change how long the script runs
- `ad_selectors`: Add/remove CSS selectors to target different ad elements

## Notes

For troubleshooting, check the console output which provides information about clicks, new windows, and any errors that occur. 