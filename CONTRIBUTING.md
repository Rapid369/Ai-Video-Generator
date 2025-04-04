# Contributing to AI Video Generator

Thank you for your interest in contributing to the AI Video Generator project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:

1. A clear, descriptive title
2. A detailed description of the bug
3. Steps to reproduce the issue
4. Expected behavior
5. Actual behavior
6. Screenshots (if applicable)
7. Environment information (OS, browser, etc.)

### Suggesting Features

We welcome feature suggestions! Please create an issue on GitHub with:

1. A clear, descriptive title
2. A detailed description of the proposed feature
3. Any relevant mockups or examples
4. Why this feature would be beneficial to the project

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

#### Pull Request Guidelines

- Keep PRs focused on a single feature or bug fix
- Follow the existing code style
- Include tests for new functionality
- Update documentation as needed
- Reference any related issues

## Development Setup

1. Clone your fork of the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements-web.txt
   pip install -r requirements-dev.txt
   ```
4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```
5. Run the application:
   ```bash
   flask run
   ```

## Code Style

We follow PEP 8 guidelines for Python code. Please ensure your code adheres to these standards.

You can check your code style with:
```bash
flake8 .
```

And format your code with:
```bash
black .
```

## Testing

Please write tests for any new functionality. Run the test suite with:
```bash
pytest
```

## Documentation

Update documentation for any changes you make. This includes:

- Code comments
- Function/method docstrings
- README updates
- API documentation

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

## Questions?

If you have any questions about contributing, please open an issue on GitHub.
