# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WhatsApp Fashion Commerce AI - A WhatsApp-based AI assistant for fashion e-commerce.

**Status**: MVP complete - all 4 user stories implemented and ready for deployment.

## Build/Test/Lint Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Lint
ruff check app/ tests/

# Type check
mypy app/ --ignore-missing-imports

# Security audit
pip-audit -r requirements.txt

# Docker development
docker-compose up
```

## Tech Stack

- **Framework**: FastAPI + Pydantic v2
- **AI**: GPT-4 + Gemini 2.0 Vision + OpenAI Embeddings
- **Database**: Supabase PostgreSQL + pgvector
- **Cache**: Redis (Upstash)
- **Messaging**: WhatsApp Cloud API

## Code Style

- Strict type hints (NON-NEGOTIABLE)
- Async-first design
- Service-oriented architecture
- Graceful degradation: retry once with 3s timeout, then fallback

## SpecKit Workflow

This project uses SpecKit for specification-driven development. Available slash commands:

- `/speckit.constitution` - Create/update project constitution with core principles
- `/speckit.specify` - Create feature specifications from natural language descriptions
- `/speckit.clarify` - Identify underspecified areas and encode clarifications
- `/speckit.plan` - Generate implementation design artifacts
- `/speckit.tasks` - Generate actionable, dependency-ordered tasks
- `/speckit.implement` - Execute the implementation plan
- `/speckit.analyze` - Cross-artifact consistency analysis
- `/speckit.checklist` - Generate custom checklists for features
- `/speckit.taskstoissues` - Convert tasks to GitHub issues

### Directory Structure

- `.specify/templates/` - Templates for specs, plans, tasks, checklists
- `.specify/memory/constitution.md` - Project constitution (needs to be populated)
- `.specify/scripts/powershell/` - Helper scripts for feature setup

## Getting Started

1. Define project constitution: `/speckit.constitution`
2. Create feature spec: `/speckit.specify`
3. Plan implementation: `/speckit.plan`
4. Generate tasks: `/speckit.tasks`
5. Implement: `/speckit.implement`
