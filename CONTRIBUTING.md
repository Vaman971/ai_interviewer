# Contributing to AI Interviewer

First off, thank you for considering contributing to AI Interviewer! It's people like you that make this tool great.

## Branching Strategy
We use a specific branching strategy to keep the repository organized and stable:
- **`main`**: The production-ready branch. This branch is protected and only the core maintainer has the right to merge into it.
- **`develop`**: The main integration branch. **All features, enhancements, and bug fixes must target this branch.** 
- **Feature Branches**: Make all your code changes in a new branch created from `develop` (e.g., `feature/awesome-new-feature` or `bugfix/issue-123`).

## Submitting Pull Requests
1. **Fork the repository** and clone it locally.
2. **Set your base branch**: Always create your new branch off of `develop`:
   ```bash
   git fetch origin
   git checkout develop
   git checkout -b feature/your-feature
   ```
3. **Make your changes** and ensure they adhere to the project's coding standards.
4. **Test your code**: Ensure all backend (e.g., `pytest`) and frontend tests pass locally. Do not check in broken code.
5. **Commit your changes**: Write clear, descriptive commit messages.
6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature
   ```
7. **Submit a Pull Request** against the **`develop`** branch of this repository.
8. **Fill out the Pull Request template**: We automatically provide a template when you open a PR. Please fill it out completely to help us review your code quickly.

## Reporting Bugs and Requesting Features
We use GitHub Issues to track public bugs and features. 
- Please use the provided **Issue Templates** (`Bug report` or `Feature request`) when opening a new issue.
- Please search existing issues before filing a new one to avoid duplicates.

## Local Development Setup
The project consists of a Python backend and a Node.js frontend.
- **Backend**: Navigate to the repository root. Ensure your virtual environment is set up and install dependencies driven by `pyproject.toml` (or `uv.lock`). Copy `.env.example` to `.env` and fill in the required keys.
- **Frontend**: Navigate to the `frontend/` directory, install node dependencies (`npm install`), and run the development server.
- **Docker**: A `docker-compose.yml` file is provided at the root if you prefer to orchestrate the stack using Docker containers.

## License
By contributing, you agree that your contributions will be licensed under its MIT License.
