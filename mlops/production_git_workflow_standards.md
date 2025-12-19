# Production Git Workflow Standards

This document defines the standards used for managing Git workflows in this repository, with a focus on consistency, clarity, and automation readiness.

---

## Conventional Commits

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#specification) specification to standardize commit messages.

Using Conventional Commits enables:
- Clear communication of intent
- Consistent and readable commit history
- Easier automation for changelogs and releases

### Commit Message Format
` <type>[optional scope]: <description> `

### Common Commit Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation-only changes
- `chore`: Maintenance or tooling changes
- `refactor`: Code refactoring without behavior changes
- `test`: Adding or updating tests
- `ci`: CI/CD related changes

### Examples

```text
feat: add prompt validation pipeline
fix: handle null input in inference runner
docs: update git workflow standards
chore: clean up unused scripts
```
---

These conventions are enforced across development workflows to maintain production-grade quality and traceability.
