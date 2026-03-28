# Refactoring Proposal 01: Architectural Improvements for AI Factory Control Center

## 1. Overview
The current codebase is built using FastHTML and SQLModel. While functional, the architecture exhibits tight coupling between routing, business logic, database access, and UI rendering. This monolithic structure makes the code harder to maintain, test, and scale. The most prominent issue is the inclusion of complex Openhands business logic directly within the execution router.

This proposal outlines a plan to refactor the application towards a more modular, layered architecture, improving Separation of Concerns (SoC).

## 2. Key Issues Identified

### 2.1. Tight Coupling in Routers
Routers (e.g., `app/routers/execution.py`, `app/routers/projects.py`, `app/routers/users.py`) currently handle multiple responsibilities:
- HTTP request handling and routing.
- Database queries (SQLModel `Session` usage).
- Complex business logic (e.g., Openhands agent execution).
- UI rendering (FastHTML components).

### 2.2. Misplaced Openhands Business Logic
The `run_agent_in_background` function and `_FileWriter` class in `app/routers/execution.py` represent core business logic for interacting with the Openhands SDK. Placing this in a router file violates the Single Responsibility Principle and makes it difficult to reuse or test independently.

### 2.3. Decentralized Configuration
Environment variables (like `OPENHANDS_STORAGE_PATH`) are loaded directly in the files where they are used (e.g., `app/routers/execution.py`). This makes it hard to track and manage configuration across the application.

### 2.4. Lack of Data Access Layer
Database queries are scattered throughout the routers. This makes it difficult to change the database schema or query logic without modifying the routing layer.

## 3. Proposed Architecture

We propose moving towards a layered architecture:

1.  **Routers/Controllers (`app/routers/`)**: Responsible only for handling HTTP requests, validating input, calling the appropriate service, and returning the HTTP response (or rendered UI).
2.  **Services (`app/services/`)**: Contains the core business logic. Services orchestrate operations, interact with external APIs (like Openhands), and call repositories for data access.
3.  **Repositories/CRUD (`app/crud/` or `app/repositories/`)**: Encapsulates all database access logic. Routers and services should not interact with the database session directly but through these repositories.
4.  **Views/Components (`app/views/` or `app/components/`)**: Contains the FastHTML UI rendering logic, separating the presentation layer from the routing logic.
5.  **Core/Config (`app/core/config.py`)**: Centralized configuration management.

## 4. Refactoring Steps

### Step 1: Centralize Configuration
- Create `app/core/config.py` to load and validate all environment variables using `pydantic-settings` or a simple configuration class.
- Update all files to import configuration from this central module.

### Step 2: Extract Openhands Service
- Create `app/services/openhands_service.py`.
- Move `run_agent_in_background`, `_FileWriter`, and related Openhands SDK imports from `app/routers/execution.py` to this new service.
- Refactor the service to accept necessary parameters and return results or status updates, decoupling it from the FastHTML request context.
- The service should use a repository (see Step 3) to save execution messages to the database, rather than using the database session directly within the event handler.

### Step 3: Implement Data Access Layer (CRUD)
- Create a new directory `app/crud/`.
- Create files like `crud_user.py`, `crud_project.py`, `crud_execution.py`.
- Move all SQLModel `select`, `add`, `commit`, and `refresh` operations from the routers into these CRUD modules.
- Update routers and services to use these CRUD functions.

### Step 4: Extract UI Components
- Create a new directory `app/views/` or `app/components/`.
- Move the FastHTML rendering functions (e.g., `user_form`, `project_card`, execution UI components) out of the routers and into these view modules.
- Routers will import these components and pass the necessary data to them.

### Step 5: Refactor Routers
- Update the routers to act as thin controllers. They should:
    1. Receive the request.
    2. Call the appropriate CRUD or Service function.
    3. Call the appropriate View function with the result.
    4. Return the response.

## 5. Benefits
- **Improved Maintainability**: Smaller, focused files are easier to understand and modify.
- **Enhanced Testability**: Services and CRUD operations can be unit-tested independently of the web framework.
- **Reusability**: Business logic (like Openhands execution) can be reused in different contexts (e.g., a CLI tool or a background worker).
- **Clearer Separation of Concerns**: Developers can work on UI, business logic, or database access without stepping on each other's toes.
