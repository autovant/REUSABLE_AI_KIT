---
applyTo: '**/*.{py,java,cs,go,rs,rb},**/routes/**,**/controllers/**,**/services/**,**/models/**,**/migrations/**'
description: 'Backend domain patterns: API design, database, security, performance'
---

# Backend Patterns

Applied only to backend files. Reference these when building or reviewing server-side code.

## API Design

- Resource-oriented URLs with nouns, HTTP verbs implicit in method
- Consistent error response shape across all endpoints
- Pagination for all list endpoints (cursor-based preferred, offset acceptable)
- Input validation at the boundary (request handler), not deep in services
- Appropriate status codes: 201 create, 204 delete, 422 validation, 409 conflict

## Database

- **Parameterized queries always.** Never string-concatenate user input into SQL.
- Indexes on foreign keys and frequently-filtered columns
- Migrations must be reversible (up + down)
- Avoid N+1: use eager loading / joins / batch queries
- Transactions for multi-table writes

### ORM Rules

- Understand the SQL your ORM generates (check query count)
- Use eager loading for known relationships (`selectinload`, `joinedload`, `.Include()`)
- Raw SQL for complex queries (CTEs, window functions) - ORMs aren't always better
- Batch inserts/updates for bulk operations

## Python / FastAPI

- Async functions for I/O (database, HTTP calls, file)
- Pydantic models for request/response validation
- Dependency injection for services
- Repository pattern for data access layer
- Common bugs: missing `await`, blocking call in async function, circular imports

## Node.js / Express

- Async/await over callbacks (no callback hell)
- Error-handling middleware at the end of the chain
- Zod or Joi for request validation
- Graceful shutdown on SIGTERM
- Common bugs: unhandled promise rejections, event listener memory leaks, blocking event loop

## Security

- Hash passwords with bcrypt/argon2. Never plaintext.
- Rate limit auth endpoints
- CORS: allowlist specific origins, not `*` in production
- Never return internal errors to clients - use generic messages
- Secrets from `process.env` / `os.environ`, never hardcoded

## Performance

- Connection pooling for databases (don't open/close per request)
- Cache frequently-read, rarely-written data (Redis or in-memory)
- Background jobs for long-running work (don't block the request)
- Profile slow endpoints: check query plan, add indexes, reduce N+1
