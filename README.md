# Event Monitoring Automation

A Python web scraper that collects facility management events from 11 different sources and saves them to an Excel file.

## Sources

- GEFMA (Germany)
- IFMA (International)
- RealFM (Germany)
- IWFM (UK)
- EuroFM (Europe)
- FMJ (UK)
- FMUK (UK)
- Facility-Manager.de (Germany)
- i-FM.net (UK)
- Builtworld (Germany)
- i2FM (Germany)

## Requirements

- Python 3.8 or higher
- Chrome browser (for Builtworld scraper)

## Installation

### Option 1: Download from GitHub (no Git required)

1. Go to https://github.com/annapotapchuk/eventmonitoringautomation
2. Click the green **Code** button → **Download ZIP**
3. Extract the ZIP file
4. Open terminal/command prompt in the extracted folder

### Option 2: Clone with Git

```bash
git clone https://github.com/annapotapchuk/eventmonitoringautomation.git
cd eventmonitoringautomation
```

## Setup

### Create virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:

```bash
python main.py
```

Events will be saved to `events.xlsx` in the same folder.

## Output

The Excel file contains:
- **Title** - Event name
- **Date** - Event date(s)
- **Location** - Venue and city
- **URL** - Link to event details
- **Source** - Which website the event was scraped from

Events are sorted by date (closest first).

---

## Quick Start for Corporate Laptop (No Git, No Venv)

If you don't have Git installed or can't create virtual environments:

### 1. Download

1. Go to https://github.com/annapotapchuk/eventmonitoringautomation
2. Click green **Code** button → **Download ZIP**
3. Extract the ZIP to your desired folder

### 2. Install dependencies

Open Command Prompt (Windows) or Terminal (Mac) in the extracted folder:

```bash
pip install requests beautifulsoup4 openpyxl selenium
```

### 3. Run

```bash
python main.py
```

The `events.xlsx` file will appear in the same folder with all scraped events.
