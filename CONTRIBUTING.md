# Contributing to Babblefish

Thank you for your interest in contributing to Babblefish! This document provides guidelines for contributions.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building technology to break down language barriers—let's practice what we preach.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/Dankular/Babblefish/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, browser, Python version)
   - Logs/screenshots if applicable

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with tag `enhancement`
3. Describe:
   - Use case / problem it solves
   - Proposed solution
   - Alternative approaches considered
   - Any implementation ideas

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests if applicable
5. Update documentation
6. Commit with clear messages: `git commit -m "Add: feature description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

**PR Guidelines**:
- One feature/fix per PR
- Keep PRs focused and small
- Include tests for new functionality
- Update README/docs as needed
- Follow existing code style
- Add yourself to contributors if it's your first PR

## Development Setup

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed setup instructions.

**Quick setup**:

```bash
# Server
cd server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Client
cd client
npm install
npm run dev
```

## Code Style

### Python (Server)

- Follow PEP 8
- Use type hints
- Docstrings for classes and public methods (Google style)
- Black formatter (line length 100)
- isort for imports

```bash
pip install black isort
black server/ --line-length 100
isort server/
```

### JavaScript (Client)

- ESLint configuration (included)
- Prettier for formatting
- Functional components with hooks (React)
- Descriptive variable names

```bash
npm run lint
npm run format
```

## Testing

### Server Tests

```bash
cd server
pytest tests/ -v
```

**Write tests for**:
- New pipeline components
- Room management logic
- Protocol message handling

### Client Tests

```bash
cd client
npm run test
```

**Write tests for**:
- React hooks
- Audio processing utilities
- WebSocket message handling

## Documentation

- Update README.md for user-facing changes
- Update PROTOCOL.md for protocol changes
- Update DEPLOYMENT.md for setup changes
- Add JSDoc/docstrings for new functions
- Include examples in docs/

## Project Structure

```
Babblefish/
├── server/          # Python FastAPI server
│   ├── rooms/       # Room management
│   ├── pipeline/    # ML pipeline (ASR + Translation)
│   ├── transport/   # WebSocket protocol
│   └── speakers/    # Speaker registry (Phase 3)
├── client/          # React browser client
│   ├── src/core/    # Audio capture, VAD
│   ├── src/network/ # WebSocket, protocol
│   ├── src/pages/   # UI pages
│   └── src/components/ # Reusable components
├── models/          # Model download scripts
└── docs/            # Documentation
```

## Commit Messages

Use clear, imperative commit messages:

```
Add: New feature
Fix: Bug description
Update: Improved functionality
Refactor: Code restructuring
Docs: Documentation changes
Test: Test additions/changes
```

**Examples**:
- `Add: Silero VAD integration for client-side speech detection`
- `Fix: WebSocket reconnection loop on network failure`
- `Update: Improve translation quality with beam size tuning`

## Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch (future)
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation

## Release Process

1. Update version in `server/__init__.py` and `client/package.json`
2. Update CHANGELOG.md
3. Create release branch: `release/vX.Y.Z`
4. Test thoroughly
5. Merge to main
6. Tag release: `git tag vX.Y.Z`
7. Push tags: `git push --tags`

## Phase Roadmap

**Phase 1** (Current): Text translation MVP
- ✅ Server architecture
- ✅ Client architecture
- ✅ WebSocket protocol
- ✅ ASR + Translation pipeline

**Phase 2**: Generic TTS
- [ ] Kokoro TTS integration (client-side)
- [ ] Audio playback queue
- [ ] Server-side TTS fallback

**Phase 3**: Voice Cloning
- [ ] F5-TTS integration (client-side)
- [ ] Voice enrollment flow
- [ ] Speaker diarization
- [ ] Adaptive TTS routing

**Phase 4**: Production Hardening
- [ ] Authentication
- [ ] Room persistence
- [ ] Performance optimization
- [ ] Mobile app (React Native)

## Areas Needing Help

- [ ] **Testing**: More comprehensive test coverage
- [ ] **Localization**: Translate UI to more languages
- [ ] **Documentation**: Video tutorials, examples
- [ ] **Performance**: Optimize pipeline latency
- [ ] **Models**: Explore alternative ASR/translation models
- [ ] **Accessibility**: Screen reader support, keyboard navigation
- [ ] **Mobile**: Optimize for mobile browsers
- [ ] **Docker**: Complete Docker deployment (currently skipped)

## Questions?

- Open an issue with tag `question`
- Email: dan@khosa.co
- Start a discussion on GitHub Discussions (if enabled)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Remember**: Language should have no barriers. Your contributions help make that a reality. 🐟
