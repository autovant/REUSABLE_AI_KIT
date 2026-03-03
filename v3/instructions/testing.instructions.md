---
applyTo: '**/*.{spec,test}.{ts,tsx,js,jsx},**/*.{spec,test}.py,**/playwright.config.*,**/jest.config.*,**/vitest.config.*,**/conftest.py'
description: 'Testing standards: Playwright, unit tests, fix-test-verify loop'
---

# Testing Standards

## The Two Cardinal Sins

1. **Never mock what you're testing.** If you mock the payment service, you're NOT testing the payment service.
2. **Never create passing tests that don't prove the feature works.** A test that always passes is worse than no test.

## Fix-Test-Verify Loop

Every code change follows this cycle until all tests pass:

Fix -> Test -> Verify -> (repeat if failing)

- After fixing code, run affected tests immediately
- After writing new code, run `get_errors` then run tests
- Never declare done until tests pass with real assertions
- If a fix breaks another test, fix that too before continuing

## Playwright E2E Rules

### Locator Strategy (in order of preference)
1. `page.getByRole('button', { name: 'Submit' })` - accessible role
2. `page.getByLabel('Email')` - form labels
3. `page.getByText('Welcome')` - visible text
4. `page.getByTestId('submit-btn')` - data-testid (last resort)

**Never use**: CSS selectors, XPath, or IDs for Playwright tests.

### CI / Agent Mode
```typescript
const config: PlaywrightTestConfig = {
  reporter: [['line']],
  use: {
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  retries: 1,
};
```

### Common Playwright Anti-Patterns
- `await page.waitForTimeout(3000)` - Use waitForSelector or waitForResponse instead
- `page.locator('.btn-primary')` - Use getByRole instead
- `expect(items.length).toBe(5)` - Test real data, not magic numbers
- Opening browsers in CI - Always headless

## Unit Test Standards

- **Arrange-Act-Assert** pattern for every test
- **Test behavior, not implementation.** If you refactor and tests break, the tests were wrong.
- **One concept per test.** Not one assertion (some concepts need 2-3 assertions).
- **Descriptive names**: `should reject email without @ symbol` not `test_email_3`

## Data & Fixtures

- Use factories/builders for test data (not raw object literals everywhere)
- Never seed production databases in tests
- Each test creates and cleans its own data (no shared mutable state)
- For API tests, use real test database/instance when available
