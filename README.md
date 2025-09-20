# ⛵🏃‍♂️ Strava Assistant

> Your personal AI-powered Strava posting companion for running and sailing

**Automatically process activity photos/videos, generate engaging captions, and create beautiful Strava posts from your adventures.**

---

## 🎯 The Vision

Transform your Strava posting from a manual chore into an effortless, AI-powered experience. Perfect for busy professionals who run for fitness and sail for adventure but don't want to spend time crafting posts.

### The Problem We Solve

- **Manual caption writing** takes time and creativity
- **Photo/video organization** and geotagging is tedious  
- **Posting consistency** suffers when you're busy
- **Context is lost** - your amazing adventures deserve great stories
- **Large video files** slow down processing and uploads

### The Solution

An intelligent system that:
1. **Processes** activity photos/videos with GPS data efficiently
2. **Matches** media to GPS coordinates automatically  
3. **Analyzes** your activity context (location, metrics, time)
4. **Generates** personalized, engaging captions
5. **Creates** new Strava activities from external data sources

## 🚢 Multiple Workflows Supported

### **Workflow 1: Navionics → Strava (Sailing)**
**Perfect for sailors using Navionics navigation**

```mermaid
graph LR
    A[⛵ Complete Sail] --> B[📱 Export GPX from Navionics]
    B --> C[📸 Collect Photos/Videos]
    C --> D[🤖 Media Processor]
    D --> E[📝 AI Caption Generator]
    E --> F[🚀 Create New Strava Activity]
```

**Use Case:** After a sailing session, export your track from Navionics, gather your photos/videos, and create a beautiful Strava post showcasing your sailing adventure.

### **Workflow 2: Strava → Enhanced (Running)**
**For runners wanting to enhance existing Strava activities**

```mermaid
graph LR
    A[🏃‍♂️ Complete Run] --> B[📱 Auto-sync to Strava]
    B --> C[📸 Add Photos Later]
    C --> D[🤖 Media Processor]
    D --> E[📝 Enhanced Captions]
    E --> F[✨ Update Strava Activity]
```

**Use Case:** Your run is already on Strava, but you want to add photos and improve the caption with AI-generated content.

---

## ✨ Key Features

### 🤖 **AI Caption Generation**
- **Context-aware templates** for different run types
- **Time-based messaging** (morning energy, evening therapy)
- **Location intelligence** (park names, neighborhoods, trails)
- **Personal style** adaptation (including sales context)
- **Smart emoji** and hashtag selection

### 📸 **Advanced Media Processing**
- **Smart format support** (HEIC, JPG, MOV, MP4 including 4K videos)
- **Efficient large file handling** with streaming for memory safety
- **GPS coordinate extraction** from existing EXIF data
- **GPX timestamp matching** with configurable tolerance
- **Parallel processing** for photos, sequential for large videos
- **Comprehensive metadata extraction** (resolution, duration, file size)

### 🗺️ **GPX Integration**
- **Activity metrics extraction** (distance, pace, elevation)
- **Route analysis** for terrain and difficulty assessment
- **Timestamp correlation** with photo capture times
- **Multiple format support** (GPX, TCX)

### ⚡ **Workflow Automation**
- **Real-time file monitoring** for new photos/GPX files
- **Session grouping** by time proximity
- **One-click posting** to Strava
- **Background processing** while you work

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[📸 Running Photos] --> C[File Monitor]
    B[🗺️ GPX Data] --> C
    C --> D[Photo Processor]
    D --> E[GPS Matching]
    E --> F[Location Analysis]
    F --> G[AI Caption Generator]
    G --> H[Session Manager]
    H --> I[🚀 Strava MCP]
    I --> J[📱 Strava Post]
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Photo Processor** | Geotag photos using GPX data | Python, exiftool, gpxpy |
| **Caption Generator** | AI-powered caption creation | Python, templating, location APIs |
| **Workflow Orchestrator** | Coordinate end-to-end automation | Python, watchdog, asyncio |
| **Strava MCP Server** | Direct Strava API integration | TypeScript, Model Context Protocol |
| **CLI Interface** | User interaction and control | Python argparse, rich output |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** for Strava MCP server
- **exiftool** for photo processing
- **Claude Desktop** with MCP support
- **Strava API** application credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/anthropics/strava-assistant.git
cd strava-assistant

# Run automated setup
python setup.py

# This will:
# ✅ Create Python virtual environment
# ✅ Install all dependencies
# ✅ Install exiftool via Homebrew
# ✅ Create necessary directories
# ✅ Provide MCP configuration instructions
```

### Strava API Setup

1. **Create Strava Application**
   - Visit [Strava API Settings](https://www.strava.com/settings/api)
   - Create new app with callback domain: `localhost`
   - Note your Client ID and Client Secret

2. **Complete Authentication**
   ```bash
   cd strava-mcp
   npx tsx scripts/setup-auth.ts
   # Enter your credentials and complete OAuth flow
   ```

3. **Configure Claude Desktop**
   ```json
   {
     "mcpServers": {
       "strava-mcp-local": {
         "command": "node",
         "args": ["/absolute/path/to/strava-assistant/strava-mcp/dist/server.js"]
       }
     }
   }
   ```

---

## 💡 Usage Examples

### 🚢 Navionics → Strava Workflow (Sailing)

```bash
# Process sailing media with Navionics GPX export
python media_processor.py ~/sailing-photos ~/Downloads/navionics-export.gpx

# Advanced processing with custom output
python media_processor.py /path/to/sailing-media /path/to/route.gpx
```

**Example Results:**
- ✅ **25 files processed** (20 HEIC photos + 5 videos including 389MB 4K)
- ✅ **794MB total** handled efficiently with streaming
- ✅ **24 files with GPS** data extracted from EXIF
- ✅ **11 perfect matches** with GPX trackpoints (0-100s tolerance)

### 🏃‍♂️ Running Enhancement Workflow

```bash
# Watch common directories for new files
python strava_assistant.py watch

# Watch specific directories
python strava_assistant.py watch --photos ~/Desktop ~/Downloads --gpx ~/Downloads
```

**What happens:**
- 🔍 Monitors directories for new photos and GPX files
- ⚡ Automatically processes when both are available
- 📝 Generates captions with location and metrics
- 📊 Creates session preview for review
- ✅ Queues for one-click Strava posting

### Manual Processing

```bash
# Process specific files
python strava_assistant.py process /path/to/photos /path/to/route.gpx

# List processed sessions
python strava_assistant.py list

# Post to Strava
python strava_assistant.py post session_20240919_143022
```

### Example Caption Output

#### 🚢 Sailing Activity
**Input:**
- 📸 Photos/videos from San Francisco Bay
- 🗺️ Navionics GPX with 12nm sailed
- ⏰ Afternoon sail with good wind

**Generated Caption:**
```
Perfect sailing conditions on the Bay today! 12nm of pure joy with steady winds 
and sunshine ⛵ 🌊 ☀️

#sailing #strava #sanfranciscobay #navionics #perfectday
```

#### 🏃‍♂️ Running Activity  
**Input:**
- 📸 Photos from Golden Gate Park
- 🗺️ 5.2km run with 120m elevation
- ⏰ Evening run after work meetings

**Generated Caption:**
```
Post-meeting run therapy - 5.2k through Golden Gate Park to clear the head! 
Perfect way to end the day 🏃‍♂️ 🌲 💪

#running #strava #eveningrun #goldengatepark #sanfrancisco #5k
```

---

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `STRAVA_CLIENT_ID` | Your Strava app client ID | `12345` |
| `STRAVA_CLIENT_SECRET` | Your Strava app secret | `abc123...` |
| `STRAVA_ACCESS_TOKEN` | OAuth access token (auto-generated) | `xyz789...` |
| `STRAVA_REFRESH_TOKEN` | OAuth refresh token (auto-generated) | `refresh123...` |
| `ROUTE_EXPORT_PATH` | Directory for exported routes | `/Users/you/strava-exports` |

### Caption Customization

Edit `caption_generator.py` to customize:
- **Templates** for different run types
- **Emoji selection** based on context
- **Hashtag generation** rules
- **Sales context** integration
- **Personal style** preferences

### File Monitoring

Default monitored directories:
- **Photos**: `~/Desktop`, `~/Downloads`
- **GPX files**: `~/Downloads`
- **Output**: `~/strava-processed`

Customize in `strava_assistant.py` config section.

---

## 📁 Project Structure

```
strava-assistant/
├── 📄 README.md                    # This file
├── 🐍 requirements.txt             # Python dependencies
├── ⚙️ setup.py                     # Automated installation script
├── 🏃 strava_assistant.py          # Main workflow orchestrator
├── 📸 photo_processor.py           # Photo geotagging pipeline (legacy)
├── 🚀 media_processor.py           # Advanced media processing engine
├── 🤖 caption_generator.py         # AI caption generation
├── 🔗 strava-mcp/                  # Strava MCP server
│   ├── 📦 package.json
│   ├── 🔧 scripts/setup-auth.ts
│   └── 🏗️ dist/server.js
├── 📁 sessions/                    # Processed session data
├── 📁 test_data/                   # Sample media and GPX files
│   ├── 📸 media/                   # Test photos and videos
│   └── 🗺️ sample_run.gpx          # Test GPX file
├── 📁 processed/                   # Archived results
└── 🗃️ venv/                       # Python virtual environment
```

---

## 🔄 Workflow Deep Dive

### 🚀 Advanced Media Processing Engine

The new `media_processor.py` provides enterprise-grade media processing capabilities:

#### **Performance Features**
- **Async parallel processing** for photos (up to 4 workers)
- **Sequential video processing** to prevent memory exhaustion
- **Streaming large file handling** for 4K videos (389MB+ tested)
- **Smart batching** based on file type and size

#### **Format Support**
- **Photos**: HEIC, JPG, JPEG, PNG with full EXIF extraction
- **Videos**: MOV, MP4, AVI with duration and resolution detection
- **GPS Parsing**: Degrees/minutes/seconds → decimal conversion
- **File Size Intelligence**: Automatic unit conversion (kB, MB, GB)

#### **GPS Matching Algorithm**
```python
# Configurable tolerance for timestamp matching
tolerance_seconds = 300  # 5 minutes default
gps_match = gps_matcher.find_best_match(media_metadata, tolerance_seconds)

# Results include time difference and confidence scores
{
    "matched_gps": {
        "latitude": 37.8467,
        "longitude": -122.4012,
        "time_diff_seconds": 0.0  # Perfect match!
    }
}
```

#### **Processing Pipeline**
1. **File Discovery** - Scan directory for supported formats
2. **Metadata Extraction** - Use `exiftool` for comprehensive EXIF data
3. **GPS Coordinate Parsing** - Handle various coordinate formats
4. **Timestamp Correlation** - Match media to GPX trackpoints
5. **Result Generation** - Create detailed JSON reports

### Legacy Workflows

### 1. **File Detection** (Running Enhancement)
- Real-time monitoring using `watchdog`
- Triggers on new `.jpg`, `.png`, `.heic`, `.gpx` files
- Smart filtering to avoid processing system files

### 2. **Session Grouping**
- Groups photos and GPX by timestamp proximity (±2 hours)
- Handles multiple photos per run session
- Manages concurrent processing

### 3. **Activity Analysis**
- Calculates distance, pace, elevation from GPX
- Determines activity type (running, sailing, cycling)
- Analyzes route characteristics and terrain

### 4. **Caption Generation**
- Selects appropriate template based on context
- Populates with location, metrics, time data
- Adds contextual emojis and hashtags
- Incorporates personal style elements

### 5. **Strava Integration**
- Uses MCP for secure API communication
- Handles photo uploads and activity creation
- Manages OAuth token refresh automatically
- Provides posting confirmation and error handling

---

## 🎨 Caption Examples

### Morning Run
```
Started the day right with a 6.2k run through Presidio! 
Beautiful crisp morning 🌅 👟 💪

#running #strava #morningrun #presidio #sanfrancisco
```

### Scenic Trail Run
```
When your running route looks like this, you know you're doing something right! 
8.5k of pure beauty in Marin Headlands 🏃‍♂️ 🏔️ 🔥

#running #strava #scenicrun #marinheadlands #trailrunning
```

### Post-Work Decompression
```
From boardroom to Golden Gate Park - 5k of decompression 
Perfect evening therapy session 🏃‍♂️ 🌲 😊

#running #strava #eveningrun #worklifebalance #goldengatepark
```

---

## 🔧 Troubleshooting

### Common Issues

**Photos not geotagging:**
- ✅ Ensure `exiftool` is installed: `brew install exiftool`
- ✅ Check photo timestamps are within ±30 seconds of GPX data
- ✅ Verify GPX file contains valid trackpoints

**MCP connection fails:**
- ✅ Use absolute paths in Claude configuration
- ✅ Restart Claude Desktop after config changes
- ✅ Verify Strava tokens are valid and not expired

**Caption quality issues:**
- ✅ More location data improves caption context
- ✅ GPS accuracy affects location name resolution
- ✅ Customize templates for personal style

### Debug Commands

```bash
# Test advanced media processing
python media_processor.py test_data/media test_data/sample_run.gpx

# Test legacy photo processing
python photo_processor.py /path/to/photos /path/to/route.gpx

# Test caption generation
python caption_generator.py processed_data.json

# Check MCP server status
cd strava-mcp && npm run build && node dist/server.js
```

### 🧪 Test Results

The media processor has been tested with realistic sailing/adventure data:

```bash
==================================================
MEDIA PROCESSING SUMMARY
==================================================
Total files processed: 25
Total size: 794.4 MB
Files with existing GPS: 24
Files matched with GPX: 11

File types:
  photo: 20
  video: 5
==================================================
```

**Performance Highlights:**
- ⚡ **Sub-second processing** of 25 mixed media files
- 📱 **Perfect HEIC support** (iPhone native format)
- 🎥 **4K video handling** (389MB MOV processed efficiently)
- 🎯 **High GPS match rate** (44% matched within 5min tolerance)
- 🔧 **Zero memory issues** with large file streaming

**Sample Processing Output:**
```json
{
  "file_path": "test_data/media/IMG_1637.HEIC",
  "file_type": "photo",
  "format": "HEIC",
  "size_mb": 3.2,
  "timestamp": "2025-09-17T10:52:36",
  "has_existing_gps": true,
  "existing_gps": {
    "latitude": 37.84683888888889,
    "longitude": -122.40127500000001,
    "altitude": 3.9,
    "speed": 1.608666974,
    "direction": 137.7478409
  },
  "matched_gps": {
    "latitude": 37.8467,
    "longitude": -122.4012,
    "elevation": 4.0,
    "time": "2025-09-17 10:52:36+00:00",
    "time_diff_seconds": 0.0
  },
  "processing_status": "success",
  "resolution": [2956, 3826]
}
```

Results are saved to `~/strava-processed/` as timestamped JSON files for review and integration.

---

## 🛡️ Privacy & Security

- **Local processing** - All data stays on your machine
- **Secure OAuth** - Industry-standard Strava authentication
- **No cloud uploads** - Photos and GPX never leave your device
- **Encrypted tokens** - Strava credentials stored securely
- **Optional sharing** - You control what gets posted

---

## 🚀 Future Enhancements

### Planned Features
- [ ] **Advanced photo analysis** using computer vision
- [ ] **Weather integration** for enhanced context
- [ ] **Training plan awareness** for workout-specific captions
- [ ] **Social media crossposting** (Instagram, Twitter)
- [ ] **Achievement detection** (PRs, milestones)
- [ ] **Group run recognition** from multiple GPS tracks

### Technical Improvements
- [ ] **Real-time preview** in web interface
- [ ] **Mobile app** for on-the-go posting
- [ ] **Cloud sync** for multi-device workflows
- [ ] **Advanced AI models** for better caption quality
- [ ] **Plugin architecture** for custom processors

---

## 🤝 Contributing

We welcome contributions! Areas where help is needed:

- **Caption templates** for different running styles
- **Location intelligence** improvements
- **Photo analysis** enhancements  
- **Additional GPS formats** support
- **Mobile integration** development
- **Documentation** and tutorials

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/strava-assistant.git

# Create development environment
python -m venv dev-env
source dev-env/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black . && isort .
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Strava API** for providing comprehensive activity data access
- **Model Context Protocol** for enabling secure AI-tool integrations
- **Claude Desktop** for MCP server hosting capabilities
- **ExifTool** for reliable photo metadata processing
- **GPXPy** for robust GPX file parsing

---

<div align="center">

**Ready to make your Strava posts effortless?**

[🚀 Get Started](#-quick-start) | [📖 Full Documentation](#-usage-examples) | [🤝 Contribute](#-contributing)

---

*Built with ❤️ for runners who code and coders who run*

</div>