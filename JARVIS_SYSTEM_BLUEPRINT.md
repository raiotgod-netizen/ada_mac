# ADA System Blueprint

## Goal
Convert ADA from a multimodal assistant app into a full personal operating system assistant, closer to a real-world Jarvis.

## Product Vision
ADA should become:
- voice-first
- local-first when possible
- cloud-augmented when useful
- memory-persistent
- action-capable
- modular
- resilient to provider failures
- safe for real daily use

## Core System Layers

### 1. Interaction Layer
Responsible for how the user talks to ADA.
- wake word
- push-to-talk
- continuous conversation mode
- typed chat
- camera context
- gesture interaction
- notification surface
- spoken confirmations when needed

### 2. Cognition Layer
Responsible for understanding, planning, and decision making.
- intent detection
- task decomposition
- short-term working memory
- long-term memory
- rules and preferences
- planner/orchestrator
- mode selection (fast, deep, local, safe)
- confidence scoring

### 3. Action Layer
Responsible for doing real work.
- filesystem actions
- app control
- terminal/dev actions
- browser automation
- custom scripts
- CAD and fabrication
- smart home control
- printer control
- calendar/email/connectors
- notification and reminder engine

### 4. Runtime Layer
Responsible for availability and reliability.
- provider state tracking
- degraded mode
- reconnect strategy
- local fallback models
- queueing
- tool health monitoring
- telemetry/logging
- crash recovery

### 5. Safety Layer
Responsible for staying usable and not reckless.
- permission tiers
- sensitive action guardrails
- per-tool policy
- audit log
- user-defined rules
- device trust model
- local-only mode

## Missing Pieces in Current ADA
Current ADA already has:
- Electron UI
- voice loop with Gemini Live
- browser agent
- CAD generation
- printer support
- Kasa support
- project memory
- face auth
- gesture UI
- custom scripts

Main gaps for a complete system:
- central planner/orchestrator
- local model fallback
- wake word pipeline
- unified memory engine
- task queue and background jobs
- connectors (calendar, email, reminders, notifications)
- richer PC control
- system observation layer
- capability registry
- robust policy engine
- proactive routines
- environment model (devices, rooms, schedules, people)

## Target Architecture

### Backend modules to add
- `backend/orchestrator.py`
  - central planner
  - routes intents to tools/subsystems
  - manages multi-step tasks

- `backend/runtime_manager.py`
  - tracks provider availability
  - chooses local/cloud mode
  - exposes runtime health to frontend

- `backend/memory_engine.py`
  - merges preferences, rules, episodic memory, semantic summaries
  - supports retrieval by task/context

- `backend/task_queue.py`
  - background tasks
  - retries
  - task state transitions
  - scheduled execution

- `backend/device_registry.py`
  - trusted devices
  - microphones, speakers, cameras, printers, smart devices
  - health + availability

- `backend/connectors/`
  - calendar
  - email
  - notifications
  - messaging
  - weather
  - maps

- `backend/local_fallback/`
  - local STT
  - local TTS
  - local LLM routing
  - fallback command parser

- `backend/policy_engine.py`
  - safety tiers
  - user rules
  - per-tool approval rules

### Frontend modules to add
- provider/runtime status panel
- tasks panel
- memory panel
- routines/automations panel
- notification center
- always-listening / wake-word state indicator
- active tools and background jobs view
- trust/permissions UI

## Phased Build Plan

### Phase 1: Robust Core
Objective: make ADA reliable enough for daily use.
- runtime manager
- explicit degraded mode UI
- provider health states
- central orchestrator skeleton
- task queue skeleton
- structured event logging
- better startup diagnostics

### Phase 2: Local-First Brain
Objective: reduce dependence on cloud quota.
- local intent parser
- local command fallback
- optional local LLM support
- local STT/TTS options
- fallback routing policy

### Phase 3: Persistent Personal Memory
Objective: make ADA feel continuous.
- memory engine
- semantic retrieval
- preferences/rules/person profile
- project and life context
- memory review and consolidation

### Phase 4: Real-World Action System
Objective: make ADA useful beyond chat.
- improved PC control
- app automation
- browser workflows
- calendar/reminders
- notifications
- richer script system
- background jobs

### Phase 5: Proactive Assistant
Objective: make ADA feel like a real operating companion.
- routines
- scheduled summaries
- reminder intelligence
- anomaly detection
- attention model
- proactive suggestions with restraint

### Phase 6: Jarvis Layer
Objective: cinematic but useful experience.
- wake word
- room/device awareness
- multimodal context fusion
- overlay/heads-up display
- continuous agent mode
- voice persona system

## Recommended Order Right Now
1. runtime manager
2. orchestrator skeleton
3. task queue
4. memory engine
5. local fallback routing
6. connectors
7. proactive routines

## Definition of Done for “System Complete”
ADA should be able to:
- start reliably even when providers fail
- explain its current operating mode
- remember the user and current projects
- take multi-step requests and execute them safely
- continue work in background
- handle reminders, files, browser, apps, smart home, and projects
- degrade gracefully when cloud services are unavailable
- recover after restarts without losing context

## Immediate Next Implementation
Build **Phase 1** now:
- add `runtime_manager.py`
- add `orchestrator.py`
- add `task_queue.py`
- expose runtime/task state to frontend
- create a system dashboard panel in UI

## Practical Note
This is not a one-turn patch. It is a system program.
The right way is to implement it in phases without breaking the current ADA.
