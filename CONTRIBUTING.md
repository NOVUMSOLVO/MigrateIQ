# Contributing to MigrateIQ

Thank you for your interest in contributing to MigrateIQ! We welcome contributions from the community and are pleased to have you join us.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Types of Contributions

We welcome many types of contributions, including:

- **Bug fixes**: Help us identify and fix issues
- **Feature development**: Implement new features and enhancements
- **Documentation**: Improve our docs, tutorials, and examples
- **Testing**: Add test coverage and improve test quality
- **Performance**: Optimize performance and scalability
- **Security**: Identify and fix security vulnerabilities
- **Internationalization**: Add support for new languages
- **UI/UX**: Improve user interface and experience

### Before You Start

1. **Check existing issues**: Look through existing [GitHub Issues](https://github.com/NOVUMSOLVO/MigrateIQ/issues) to see if your idea is already being discussed
2. **Create an issue**: For significant changes, create an issue first to discuss your approach
3. **Fork the repository**: Create your own fork to work on
4. **Read the documentation**: Familiarize yourself with the [Architecture](ARCHITECTURE.md) and setup process

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Git

### Local Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/MigrateIQ.git
   cd MigrateIQ
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your local configuration
   ```

5. **Set up the database**
   ```bash
   cd backend
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run the development servers**
   ```bash
   # From project root
   ./start.sh
   ```

### Development Tools

We recommend using the following tools for development:

- **IDE**: VS Code with Python and React extensions
- **Database**: pgAdmin or DBeaver for PostgreSQL management
- **API Testing**: Postman or Insomnia for API testing
- **Git GUI**: GitKraken, SourceTree, or VS Code Git integration

## How to Contribute

### 1. Choose an Issue

- Look for issues labeled `good first issue` for beginners
- Check issues labeled `help wanted` for areas where we need assistance
- For new features, create an issue first to discuss the approach

### 2. Create a Branch

Create a descriptive branch name:
```bash
git checkout -b feature/add-data-validation
git checkout -b bugfix/fix-migration-error
git checkout -b docs/update-api-documentation
```

### 3. Make Your Changes

- Follow our [coding standards](#coding-standards)
- Write tests for your changes
- Update documentation as needed
- Ensure your code passes all tests

### 4. Test Your Changes

```bash
# Backend tests
cd backend
python manage.py test
coverage run --source='.' manage.py test
coverage report

# Frontend tests
cd frontend
npm test
npm run test:coverage

# Integration tests
docker-compose -f docker-compose.test.yml up --build
```

### 5. Commit Your Changes

Use conventional commit messages:
```bash
git commit -m "feat: add data validation for CSV imports"
git commit -m "fix: resolve migration timeout issue"
git commit -m "docs: update API documentation for new endpoints"
```

## Pull Request Process

### Before Submitting

1. **Rebase your branch** on the latest main branch
2. **Run all tests** and ensure they pass
3. **Update documentation** if needed
4. **Add changelog entry** if applicable

### Submitting Your PR

1. **Create a pull request** from your fork to the main repository
2. **Fill out the PR template** completely
3. **Link related issues** using keywords like "Fixes #123"
4. **Request review** from maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process

1. **Automated checks**: CI/CD pipeline runs tests and checks
2. **Code review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged

## Coding Standards

### Python (Backend)

- **Style**: Follow PEP 8 with Black formatting
- **Imports**: Use isort for import organization
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings
- **Linting**: Code must pass flake8 checks

```python
def process_data(data: List[Dict[str, Any]]) -> ProcessingResult:
    """Process incoming data and return results.
    
    Args:
        data: List of data dictionaries to process
        
    Returns:
        ProcessingResult containing success status and processed data
        
    Raises:
        ValidationError: If data validation fails
    """
    pass
```

### JavaScript/TypeScript (Frontend)

- **Style**: Use Prettier for formatting
- **Linting**: Code must pass ESLint checks
- **Components**: Use functional components with hooks
- **TypeScript**: Use TypeScript for type safety
- **Testing**: Use React Testing Library

```typescript
interface DataTableProps {
  data: DataRow[];
  onRowSelect: (row: DataRow) => void;
  loading?: boolean;
}

const DataTable: React.FC<DataTableProps> = ({ data, onRowSelect, loading = false }) => {
  // Component implementation
};
```

### General Guidelines

- **Comments**: Write clear, concise comments
- **Naming**: Use descriptive variable and function names
- **Functions**: Keep functions small and focused
- **Error handling**: Implement proper error handling
- **Security**: Follow security best practices

## Testing Guidelines

### Backend Testing

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test API endpoints and database interactions
- **Coverage**: Maintain >90% test coverage
- **Fixtures**: Use factory_boy for test data

```python
class TestDataAnalyzer(TestCase):
    def setUp(self):
        self.analyzer = DataAnalyzer()
        self.sample_data = DataSourceFactory()
    
    def test_analyze_csv_data(self):
        result = self.analyzer.analyze(self.sample_data)
        self.assertIsInstance(result, AnalysisResult)
        self.assertTrue(result.is_valid)
```

### Frontend Testing

- **Component tests**: Test React components
- **Integration tests**: Test user workflows
- **Accessibility tests**: Ensure WCAG compliance
- **Visual regression**: Test UI consistency

```typescript
describe('DataTable Component', () => {
  it('renders data correctly', () => {
    const mockData = [{ id: 1, name: 'Test' }];
    render(<DataTable data={mockData} onRowSelect={jest.fn()} />);
    
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

## Documentation

### Types of Documentation

- **Code comments**: Inline documentation
- **API documentation**: OpenAPI/Swagger specs
- **User guides**: Step-by-step tutorials
- **Developer docs**: Technical implementation details

### Documentation Standards

- **Clarity**: Write clear, concise documentation
- **Examples**: Include practical examples
- **Updates**: Keep documentation current with code changes
- **Accessibility**: Ensure docs are accessible to all users

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code review and collaboration

### Getting Help

- **Documentation**: Check our [docs](docs/) first
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately to security@novumsolvo.com

### Recognition

We recognize contributors in several ways:

- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in changelog
- **Social media**: Highlighted on our social channels
- **Swag**: Occasional contributor swag for significant contributions

## License

By contributing to MigrateIQ, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

Thank you for contributing to MigrateIQ! Your efforts help make data migration easier for everyone.
