# Tests - AI User Assistant Module

## Quick Start

### Run Tests (All)
```bash
cd /opt/odoo
/opt/odoo/odoo-server/odoo-bin -i ai_user_assistant --test-tags=at_install -d <database>
```

### Run Tests (Specific Module)
```bash
# Only models tests
/opt/odoo/odoo-server/odoo-bin --test-tags=at_install:/ai_user_assistant:test_models -d <database>

# Only controller tests  
/opt/odoo/odoo-server/odoo-bin --test-tags=at_install:/ai_user_assistant:test_controller -d <database>

# Only agents tests
/opt/odoo/odoo-server/odoo-bin --test-tags=at_install:/ai_user_assistant:test_agents_base -d <database>
```

### Run External Tests (Real OpenAI API)
```bash
# Requires valid API key in settings
/opt/odoo/odoo-server/odoo-bin --test-tags=external -d <database>
```

## Test Modules

| Module | Tests | Purpose |
|--------|-------|---------|
| `test_models.py` | 22 | ORM models: ai.assistant.knowledge, ai.assistant.message |
| `test_controller.py` | 16 | HTTP endpoint: /ai_assistant/ask |
| `test_agents_base.py` | 10 | BaseAgent abstract contract |
| `test_agents_router.py` | 16 | RouterAgent: classify questions into 3 routes |
| `test_agents_document.py` | 14 | DocumentAgent: search knowledge base |
| `test_integration.py` | 8 | End-to-end flows: question → agent → answer |

**Total: 86+ tests**

## Test Coverage

### Models (22 tests)
- ✓ Create, read, update, delete operations
- ✓ Required field validation
- ✓ Model relationships (user linking)
- ✓ Chat history retrieval and ordering
- ✓ Multi-user isolation
- ✓ Long text storage

### Controller (16 tests)
- ✓ API key validation (missing, invalid)
- ✓ Message persistence (user → assistant)
- ✓ Route classification (documents, action_project, general)
- ✓ Token counting and accumulation
- ✓ Chat history passing to agents
- ✓ Error handling from agents
- ✓ Response structure validation

### Agents (40 tests)
- ✓ BaseAgent inheritance contract
- ✓ RouterAgent: 3-way classification with fallback
- ✓ DocumentAgent: knowledge base access
- ✓ Error handling and robustness
- ✓ Token tracking

### Integration (8 tests)
- ✓ Full flows: question → router → agent → answer
- ✓ Multi-user isolation
- ✓ Token accumulation
- ✓ Chat history context between calls

## Key Features

### Mocking Strategy
- **Default** (@at_install): Mock OpenAI responses → fast tests
- **Real** (@tagged external): Real OpenAI API → slower, requires key

### Base Infrastructure
**`common.py`** provides:
- `BaseAITestCase`: TransactionCase with setup
- `MockOpenAIResponse`: Factory for creating responses
- Fixtures: users, API key, knowledge base
- Helpers: message creation, history retrieval, token counting

### Test Isolation
- TransactionCase with automatic rollback
- User isolation in chat history
- Independent agent tests with mocked OpenAI
- Factories for creating test data

## Troubleshooting

### Tests timeout
- Odoo server may be initializing. Wait for "Ready for tests" message.
- Check database connection: `--db-filter=<database>`

### Import errors
- Ensure module is installed: `-i ai_user_assistant`
- Check Python path: tests should be at `tests/`
- Validate syntax: `python3 -m py_compile tests/*.py`

### OpenAI API errors
- External tests require valid API key in `Settings → AI User Assistant`
- Skip external tests: `--test-tags=-external`
- Use mocked tests: `--test-tags=at_install`

## Files

```
tests/
├── __init__.py               # Test discovery
├── common.py                 # Shared test infrastructure
├── test_models.py            # Models tests
├── test_controller.py        # HTTP endpoint tests
├── test_agents_base.py       # BaseAgent tests
├── test_agents_router.py     # RouterAgent tests
├── test_agents_document.py   # DocumentAgent tests
└── test_integration.py       # End-to-end tests
```
