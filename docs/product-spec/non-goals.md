# V1 Non-Goals

The following are explicitly out of scope for V1 and must not be built until V2 or later.

## Camera & Vision

- No support for arbitrary camera angles (fixed overhead only)
- No recognition of physical dice rolled on the board
- No browser-based camera input (server-side camera only)
- No multi-camera setups

## Game & Rules

- No multi-map support (WW2 Pacific 1940 2nd Edition only)
- No technology development phase
- No direct TripleA code or asset import (clean-room implementation only)

## AI & Learning

- No reinforcement learning or self-play training during live games
- No vector memory or RAG retrieval (deferred to V2)
- No LLM integration for game commentary (deferred)
- No AlphaZero-style policy/value networks

## Architecture

- No Kubernetes or Helm deployment (Docker Compose only)
- No Terraform infrastructure-as-code
- No microservices (single FastAPI process)
- No real-time analytics dashboards (basic logging only)

## Security

- No multi-user authentication system (session-based player assignment only)
- No role-based access control
- No encrypted game storage

## Autonomy

- No hidden autonomous state edits
- No live model self-modification during active games
- No autonomous rule interpretation — all ambiguous states require human confirmation
