# Ecosystem Package Specifications

This directory contains specifications for packages extracted from the ai_engineering_book ecosystem.

## Hub-and-Spoke Architecture

This repository serves as the **hub** for ecosystem-wide standards and package specifications. Individual packages are **spokes** that implement these specifications in their own repositories.

See {term}`ADR-26020` for the full architectural rationale.

## Package Specifications

| Package | Purpose | Status |
|---------|---------|--------|
| [vadocs](vadocs.md) | Documentation validation engine | v0.1.0 PoC |

## What Belongs Here

- **Package specifications** - What a package should do (capabilities, interfaces)
- **Version roadmaps** - Planned features and milestones
- **Integration guidance** - How packages interact with each other

## What Does NOT Belong Here

- **Implementation details** - Live in the package's own `docs/adr/`
- **Source code** - Lives in the package repository
- **User documentation** - Lives in the package's README
