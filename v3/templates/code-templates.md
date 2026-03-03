# Code Templates

Starter templates used by the `code-scaffold` skill to generate project-appropriate code.
Agents should detect the project stack first, then use the matching template.

## How to Use

1. The `code-scaffold` skill detects the project's tech stack
2. It selects the matching template from the sections below
3. It adapts naming, imports, and conventions to match existing project code
4. It generates the file and registers it (imports, exports, routes, etc.)

## React Component (TypeScript)

```tsx
interface {{Name}}Props {
  // Define props here
}

export function {{Name}}({ ...props }: {{Name}}Props) {
  return (
    <div>
      {/* Component content */}
    </div>
  );
}

## React Component with Hooks

```tsx
import { useState, useEffect } from 'react';

interface {{Name}}Props {
  // Define props here
}

export function {{Name}}({ ...props }: {{Name}}Props) {
  const [state, setState] = useState<null>(null);

  useEffect(() => {
    // Setup logic
    return () => {
      // Cleanup
    };
  }, []);

  return (
    <div>
      {/* Component content */}
    </div>
  );
}

## API Route Handler (Express)

```typescript
import { Router, Request, Response } from 'express';

const router = Router();

router.get('/', async (req: Request, res: Response) => {
  try {
    // Handler logic
    res.json({ data: [] });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
```

## API Endpoint (FastAPI)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/{{route}}", tags=["{{tag}}"])


class {{Name}}Request(BaseModel):
    pass


class {{Name}}Response(BaseModel):
    pass


@router.get("/", response_model=list[{{Name}}Response])
async def list_{{name_snake}}():
    """List all {{name_human}}."""
    return []


@router.post("/", response_model={{Name}}Response, status_code=201)
async def create_{{name_snake}}(request: {{Name}}Request):
    """Create a new {{name_human}}."""
    raise HTTPException(status_code=501, detail="Not implemented")
```

## Service Class (TypeScript)

```typescript
export class {{Name}}Service {
  constructor(
    // Inject dependencies
  ) {}

  async getAll(): Promise<{{Name}}[]> {
    throw new Error('Not implemented');
  }

  async getById(id: string): Promise<{{Name}} | null> {
    throw new Error('Not implemented');
  }

  async create(data: Create{{Name}}Dto): Promise<{{Name}}> {
    throw new Error('Not implemented');
  }

  async update(id: string, data: Update{{Name}}Dto): Promise<{{Name}}> {
    throw new Error('Not implemented');
  }

  async delete(id: string): Promise<void> {
    throw new Error('Not implemented');
  }
}
```

## Service Class (Python)

```python
class {{Name}}Service:
    def __init__(self):
        pass

    async def get_all(self) -> list:
        raise NotImplementedError

    async def get_by_id(self, id: str) -> dict | None:
        raise NotImplementedError

    async def create(self, data: dict) -> dict:
        raise NotImplementedError

    async def update(self, id: str, data: dict) -> dict:
        raise NotImplementedError

    async def delete(self, id: str) -> None:
        raise NotImplementedError
```

## Unit Test (Jest)

```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';

describe('{{Name}}', () => {
  beforeEach(() => {
    // Setup
  });

  it('should do the expected thing', () => {
    // Arrange
    // Act
    // Assert
    expect(true).toBe(true);
  });

  it('should handle edge case', () => {
    // Test edge case
  });
});
```

## Unit Test (pytest)

```python
import pytest


class Test{{Name}}:
    def setup_method(self):
        """Setup for each test."""
        pass

    def test_expected_behavior(self):
        """Should do the expected thing."""
        assert True

    def test_edge_case(self):
        """Should handle edge case."""
        pass
```

## Playwright E2E Test

```typescript
import { test, expect } from '@playwright/test';

test.describe('{{Name}}', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/{{title}}/);
  });

  test('should handle user interaction', async ({ page }) => {
    // Arrange
    // Act
    // Assert
  });
});
```

## Django Model

```python
from django.db import models


class {{Name}}(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{{Name}} {self.pk}"
```

## .NET Controller

```csharp
using Microsoft.AspNetCore.Mvc;

namespace {{Namespace}}.Controllers;

[ApiController]
[Route("api/[controller]")]
public class {{Name}}Controller : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        return Ok(new List<object>());
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(string id)
    {
        return NotFound();
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] object request)
    {
        return StatusCode(501);
    }
}
```
