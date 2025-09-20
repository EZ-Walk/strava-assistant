# Contributing to Strava Assistant

Thank you for your interest in contributing to Strava Assistant! This project aims to make Strava posting effortless through AI-powered automation.

## 🤝 How to Contribute

### Areas Where We Need Help

1. **Caption Templates** - Create templates for different running scenarios
2. **Location Intelligence** - Improve location name resolution and context
3. **Photo Analysis** - Enhance computer vision capabilities
4. **GPS Format Support** - Add support for additional file formats
5. **Mobile Integration** - Help with smartphone workflow integration
6. **Documentation** - Improve setup guides and tutorials

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/strava-assistant.git
   cd strava-assistant
   ```

3. **Set up development environment**:
   ```bash
   python -m venv dev-env
   source dev-env/bin/activate  # On Windows: dev-env\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Make your changes** following our coding standards

6. **Test your changes**:
   ```bash
   python -m pytest tests/
   python strava_assistant.py --help  # Basic functionality test
   ```

7. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request** with a clear description of your changes

## 🎯 Specific Contribution Ideas

### Caption Templates
Add new templates in `caption_generator.py`:
```python
'new_run_type': [
    "Template with {placeholders} for dynamic content",
    "Another variation with {different} context",
]
```

### Location Intelligence
Enhance location processing in `photo_processor.py`:
- Add support for local landmarks
- Improve trail name recognition
- Add weather context integration

### Photo Analysis
Extend photo analysis capabilities:
- Computer vision for scenery detection
- Weather condition recognition
- Time of day estimation from lighting

## 📋 Code Standards

### Python Code Style
- Use **Black** for formatting: `black .`
- Use **isort** for imports: `isort .`
- Follow **PEP 8** conventions
- Add **type hints** where possible
- Include **docstrings** for functions and classes

### Commit Messages
- Use present tense: "Add feature" not "Added feature"
- Be descriptive: "Add morning run caption templates" 
- Reference issues: "Fix #123: Handle empty GPX files"

### Testing
- Add tests for new functionality
- Ensure existing tests pass
- Test with real GPX files and photos when possible

## 🐛 Bug Reports

When reporting bugs, please include:
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **System information** (OS, Python version)
- **Sample files** if relevant (anonymized GPX/photos)
- **Error messages** and stack traces

## 💡 Feature Requests

For feature requests, please describe:
- **Use case** - what problem does this solve?
- **Proposed solution** - how should it work?
- **Alternative solutions** - what else did you consider?
- **Implementation ideas** - technical approach if you have one

## 🚀 Development Tips

### Testing with Real Data
- Use your own GPX files and photos for testing
- Anonymize any sensitive location data before sharing
- Test with various GPS devices and photo sources

### Local Development Workflow
```bash
# Activate virtual environment
source venv/bin/activate

# Run with test data
python strava_assistant.py process test_photos/ test_route.gpx

# Test caption generation
python caption_generator.py test_data.json

# Monitor file changes during development
python strava_assistant.py watch --photos ~/test_photos --gpx ~/test_gpx
```

### MCP Server Development
```bash
cd strava-mcp
npm run build
npm run dev  # For development with hot reload
```

## 📖 Documentation

### README Updates
- Keep examples current with code changes
- Add new features to the feature list
- Update installation instructions if needed

### Code Documentation
- Add docstrings to new functions
- Update type hints for better IDE support
- Include usage examples in docstrings

## 🤖 AI and Automation Guidelines

### Caption Generation
- Templates should feel natural and conversational
- Include context-specific variations
- Test with different running scenarios
- Consider cultural and regional differences

### Photo Processing
- Handle various photo formats and qualities
- Consider privacy implications of location data
- Optimize for speed with large photo collections
- Gracefully handle missing or corrupt EXIF data

## ⚖️ License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- The main README acknowledgments section
- Release notes for significant contributions
- GitHub contributor graphs and statistics

## 📞 Getting Help

- **GitHub Issues** - For bugs and feature requests
- **Discussions** - For questions and brainstorming
- **Code Review** - We'll provide feedback on pull requests

---

**Thank you for helping make Strava posting effortless for runners everywhere! 🏃‍♂️✨**