# Questionnaire Module

Clinical-trial questionnaire service built with FastAPI (backend) and React (frontend).

## Current Implementation Status

### Completed

- **Phase 1 (Core Questionnaire Module)**
  - Questionnaire CRUD with soft delete and version snapshots
  - Flexible JSON-based question schema
  - Bulk operations and metadata filtering/sorting
  - Configurable scoring with score calculation APIs

- **Phase 3 (Trial-Questionnaire Linking)**
  - Trial-to-questionnaire linking with ordering and required flags
  - Link-level recurrence and schedule settings
  - Bulk replace endpoint for trial links
  - Vendor-scoped trial questionnaire read APIs

- **Phase 5 (Participant Questionnaire Responses)**
  - Customer trial questionnaire listing/detail APIs
  - Draft + submit response flow
  - Visit-based recurrence window handling
  - Progress tracking and required-answer validation
  - Eligibility result API based on required eligibility questionnaires

### In Progress / Planned

- **Phase 2**: Admin Questionnaire Management Portal enhancements
- **Phase 4**: Vendor portal workflow expansion

## Key Backend Capabilities

- **Questionnaire Models**
  - `Questionnaire`
  - `QuestionnaireVersion`
  - `TrialQuestionnaire`
  - `ParticipantQuestionnaireResponse`

- **Recurrence Support**
  - `one_time`, `weekly`, `monthly`, `custom`
  - Optional `start_at_utc`, `end_at_utc`, `window_duration_minutes`, `max_visits`
  - Recurrence config with UTC times/slots and optional weekday/day filters

- **Response Lifecycle**
  - Draft save and final submission
  - Locked windows for non-active visits
  - Scoring integration on submit
  - Eligibility pass/fail storage per response

## Project Structure

```text
questionnarie-module/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── questionnaire.py
│   │   ├── routes/
│   │   │   ├── questionnaires.py
│   │   │   ├── trial_questionnaires.py
│   │   │   └── participant_questionnaires.py
│   │   ├── schemas/
│   │   │   └── questionnaire.py
│   │   ├── services/
│   │   │   └── scoring.py
│   │   └── database.py
│   ├── alembic/
│   │   └── versions/
│   │       ├── 001_initial_questionnaire.py
│   │       ├── 002_add_scoring_config.py
│   │       ├── 003_add_trial_questionnaires.py
│   │       ├── 004_add_participant_questionnaire_responses.py
│   │       └── 005_add_recurrence_and_visit_number.py
│   ├── main.py
│   └── requirements.txt
└── frontend/
    └── src/
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

1. Go to backend:

   ```bash
   cd questionnarie-module/backend
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   # Windows PowerShell:
   # .\venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:

   ```bash
   cp .env.example .env
   ```

5. Set `DATABASE_URL` in `.env`.

6. Run migrations:

   ```bash
   alembic upgrade head
   ```

7. Start API:

   ```bash
   uvicorn main:app --reload --port 8003
   ```

Backend docs: `http://localhost:8003/docs`

### Frontend Setup

1. Go to frontend:

   ```bash
   cd questionnarie-module/frontend
   ```

2. Install packages:

   ```bash
   npm install
   ```

3. Start dev server:

   ```bash
   npm run dev
   ```

Default frontend URL: `http://localhost:5174`

## API Overview

### 1) Questionnaire Management

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/questionnaires` | Create questionnaire |
| GET | `/api/questionnaires` | List questionnaires |
| GET | `/api/questionnaires/{id}` | Get questionnaire detail |
| PUT | `/api/questionnaires/{id}` | Update questionnaire |
| DELETE | `/api/questionnaires/{id}` | Soft delete questionnaire |
| POST | `/api/questionnaires/{id}/clone` | Clone questionnaire |
| GET | `/api/questionnaires/{id}/versions` | List version snapshots |
| POST | `/api/questionnaires/bulk-delete` | Bulk soft delete |
| POST | `/api/questionnaires/bulk-status` | Bulk status update |
| GET | `/api/questionnaires/types/list` | List questionnaire types |
| GET | `/api/questionnaires/question-types/list` | List question types |
| POST | `/api/questionnaires/{id}/calculate-score` | Calculate score |
| GET | `/api/questionnaires/{id}/scoring-config` | Get scoring config |
| PUT | `/api/questionnaires/{id}/scoring-config` | Update scoring config |

### 2) Trial-Questionnaire Linking (Admin/Vendor)

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/trials/{trial_id}/questionnaires` | Link questionnaire to trial |
| GET | `/api/trials/{trial_id}/questionnaires` | List trial questionnaire links |
| PUT | `/api/trials/{trial_id}/questionnaires` | Replace all links for trial |
| PUT | `/api/trials/{trial_id}/questionnaires/{questionnaire_id}` | Update one link |
| DELETE | `/api/trials/{trial_id}/questionnaires/{questionnaire_id}` | Unlink questionnaire |
| GET | `/api/vendor/trials/{trial_id}/questionnaires?vendor_id=...` | Vendor-scoped link list |
| GET | `/api/vendor/trials/{trial_id}/questionnaires/{questionnaire_id}?vendor_id=...` | Vendor-scoped questionnaire detail |

### 3) Participant Questionnaire Flow

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/customer/{customer_id}/trials/{trial_id}/questionnaires` | Participant trial questionnaire summary |
| GET | `/api/customer/{customer_id}/trials/{trial_id}/questionnaires/{questionnaire_id}` | Participant questionnaire detail |
| POST | `/api/customer/{customer_id}/trials/{trial_id}/responses` | Create/update draft or submit response |
| GET | `/api/customer/{customer_id}/trials/{trial_id}/responses/{response_id}` | Fetch one response |
| GET | `/api/customer/{customer_id}/trials/{trial_id}/eligibility-result` | Trial eligibility result |

## Supported Questionnaire Types

- `eligibility`
- `screening`
- `baseline`
- `follow_up`
- `adverse_event`
- `quality_of_life`
- `custom`

## Supported Question Types

- `text`
- `textarea`
- `number`
- `email`
- `phone`
- `date`
- `single_choice`
- `multiple_choice`
- `dropdown`
- `rating`
- `scale`
- `yes_no`
- `section_header`

## License

Proprietary - MannBiome
