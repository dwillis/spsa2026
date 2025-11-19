# SPSA 2026 Conference Schedule

An interactive, searchable web interface for the SPSA 2026 conference schedule.

## Features

- 📅 **Browse sessions by day** - Thursday, Friday, Saturday
- 🔍 **Full-text search** - Search across titles, people, topics, and papers
- 🏷️ **Filter by category** - Narrow down by research area
- ⏰ **Time-based filtering** - Find sessions by time of day
- 📱 **Responsive design** - Works on desktop, tablet, and mobile
- 🎨 **Modern UI** - Clean, intuitive interface

## Project Structure

```
.
├── parse_schedule.py      # Python script to parse PDF schedules
├── index.html             # Main web interface
├── schedule_all.json      # Combined schedule data (all days)
├── schedule_thursday.json # Thursday schedule
├── schedule_friday.json   # Friday schedule
├── schedule_saturday.json # Saturday schedule
├── spsa_thursday.pdf      # Source PDF for Thursday
├── spsa_friday.pdf        # Source PDF for Friday
└── spsa_saturday.pdf      # Source PDF for Saturday
```

## How It Works

### 1. PDF Parsing

The `parse_schedule.py` script extracts structured data from the conference PDF files:

- **Session details**: ID, title, time, location, category
- **People information**: Chairs, participants, discussants with affiliations
- **Papers**: Titles attached to participants

```bash
python3 parse_schedule.py
```

This generates JSON files for each day containing structured session data.

### 2. Web Interface

The `index.html` file provides an interactive interface with:

- Real-time search and filtering
- No backend required - runs entirely in the browser
- Responsive design for all devices

## Data Structure

Each session in the JSON files contains:

```json
{
  "id": "2100",
  "title": "Session Title",
  "day": "thursday",
  "day_time": "8:00am-9:15am",
  "location": "Room Name - Floor",
  "category": "Research Category",
  "chair": [
    {
      "name": "Person Name",
      "affiliation": "University Name"
    }
  ],
  "participants": [
    {
      "name": "Person Name",
      "affiliation": "University Name",
      "paper": "Paper Title"
    }
  ],
  "discussants": [
    {
      "name": "Person Name",
      "affiliation": "University Name"
    }
  ]
}
```

## Deployment

The site is automatically deployed to GitHub Pages using GitHub Actions whenever changes are pushed to the repository.

### Manual Deployment

1. Enable GitHub Pages in repository settings
2. Select "GitHub Actions" as the source
3. Push changes to trigger the workflow

The workflow will:
1. Parse the PDF files
2. Generate JSON data
3. Deploy the site to GitHub Pages

## Development

### Prerequisites

- Python 3.11+
- PyPDF2 library

### Setup

```bash
# Install dependencies
pip install PyPDF2

# Parse PDFs
python3 parse_schedule.py

# Open index.html in a browser or serve with a local server
python3 -m http.server 8000
```

Visit `http://localhost:8000` to view the site locally.

## Technologies Used

- **Python**: PDF parsing and data extraction
- **PyPDF2**: PDF text extraction
- **HTML/CSS/JavaScript**: Frontend interface
- **GitHub Actions**: Automated deployment
- **GitHub Pages**: Static site hosting

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.