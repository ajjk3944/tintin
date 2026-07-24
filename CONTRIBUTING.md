# Contributing to TensorTitan

Thank you for your interest in contributing to TensorTitan! This document provides guidelines and instructions for contributing.

## 🎯 How to Contribute

### Reporting Bugs
- Use the GitHub Issues tab
- Describe the bug in detail
- Include steps to reproduce
- Provide system information (OS, Python version, GPU details)
- Include relevant log files from `logs/` directory

### Suggesting Features
- Open a GitHub Issue with the "enhancement" label
- Clearly describe the feature and its benefits
- Explain use cases and examples

### Code Contributions

#### 1. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/tintin.git
cd tintin
```

#### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

#### 3. Make Changes
- Follow PEP 8 style guidelines
- Add comments for complex logic
- Update documentation if needed
- Test your changes thoroughly

#### 4. Commit Changes
```bash
git add .
git commit -m "Description of changes"
```

#### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

## 📝 Code Style

### Python Guidelines
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Example:
```python
def calculate_gpu_score(utilization: float, temperature: float) -> float:
    """
    Calculate a score for GPU based on utilization and temperature.
    
    Args:
        utilization: GPU utilization percentage (0-100)
        temperature: GPU temperature in Celsius
        
    Returns:
        Normalized score between 0 and 1
    """
    # Implementation here
    pass
```

## 🧪 Testing

Before submitting a PR:
```bash
# Run verification script
python verify.py

# Test with simulation
python data_simulator.py
python main.py
```

## 📦 Adding Dependencies

If you add new dependencies:
1. Add them to `requirements.txt`
2. Specify minimum version if needed
3. Document why the dependency is needed

## 🔍 Pull Request Process

1. Ensure all tests pass
2. Update README.md if you change functionality
3. Add comments explaining complex code
4. Request review from maintainers
5. Address review feedback promptly

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- No harassment or discrimination

## 💬 Getting Help

- Open a GitHub Discussion for questions
- Check existing Issues and PRs
- Read the documentation thoroughly

## 🎓 Areas for Contribution

### High Priority
- [ ] Unit tests for AI models
- [ ] Integration tests for components
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] API documentation

### Features
- [ ] Support for AMD GPUs
- [ ] Multi-node cluster support
- [ ] Advanced scheduling algorithms
- [ ] Real-time alerts via email/Slack
- [ ] Cost forecasting models

### Documentation
- [ ] API reference
- [ ] Deployment guides
- [ ] Troubleshooting guides
- [ ] Video tutorials
- [ ] Architecture deep-dives

## 📊 Roadmap

See our [GitHub Projects](https://github.com/ajjk3944/tintin/projects) for the development roadmap and planned features.

---

Thank you for contributing to TensorTitan! 🚀
