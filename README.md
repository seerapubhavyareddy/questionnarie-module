# Questionnaire Module

A comprehensive questionnaire management system for clinical trials, built with FastAPI (backend) and React (frontend).

## Features

### Phase 1: Questionnaire Module (Foundation)

- ✅ **Database Models**
  - Questionnaire table with full metadata
  - Question schema stored as JSON for flexibility
  - Version history tracking

- ✅ **API Endpoints**
  - `POST /api/questionnaires` - Create questionnaire
  - `GET /api/questionnaires` - List with pagination, filtering, sorting
  - `GET /api/questionnaires/:id` - Get single questionnaire
  - `PUT /api/questionnaires/:id` - Update questionnaire
  - `DELETE /api/questionnaires/:id` - Soft delete
  - `POST /api/questionnaires/:id/clone` - Clone questionnaire
  - `GET /api/questionnaires/:id/versions` - Version history
  - Bulk operations (delete, status update)

- ✅ **Question Types Supported**
  - Text (single line)
  - Textarea (multi-line)
  - Number
  - Email
  - Phone
  - Date
  - Single Choice (radio buttons)
  - Multiple Choice (checkboxes)
  - Dropdown
  - Rating (stars)
  - Scale (Likert)
  - Yes/No
  - Section Header

- ✅ **Questionnaire Builder UI**
  - Drag-and-drop question reordering
  - Question type selector
  - Answer options management
  - Validation rules
  - Preview functionality

- ✅ **Flexible Scoring System**
  - Multiple scoring types: Simple Sum, Subscale, Weighted
  - DASS-21 style subscale scoring (Stress, Anxiety, Depression)
  - Position-based question assignment (`questionIndices`)
  - Configurable severity ranges with labels
  - Score multipliers for clinical questionnaires
  - Real-time score calculation in preview
  - Required field validation before submission

- ✅ **Scoring API Endpoints**
  - `POST /api/questionnaires/:id/calculate-score` - Calculate scores
  - `GET /api/questionnaires/:id/scoring-config` - Get scoring config
  - `PUT /api/questionnaires/:id/scoring-config` - Update scoring config

## Project Structure

```
questionnarie-module/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── questionnaire.py    # SQLAlchemy models
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── questionnaires.py   # API endpoints
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── questionnaire.py    # Pydantic schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── scoring.py          # Scoring service
│   │   ├── __init__.py
│   │   └── database.py             # Database configuration
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 001_initial_questionnaire.py
│   │   │   └── 002_add_scoring_config.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── main.py                     # FastAPI application
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── public/
    │   └── favicon.svg
    ├── src/
    │   ├── components/
    │   │   ├── Layout.jsx
    │   │   ├── QuestionEditor.jsx
    │   │   └── QuestionPreview.jsx
    │   ├── pages/
    │   │   ├── QuestionnaireList.jsx
    │   │   ├── QuestionnaireBuilder.jsx
    │   │   └── QuestionnaireView.jsx
    │   ├── services/
    │   │   └── api.js
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    └── package.json
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd questionnarie-module/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file from example:
   ```bash
   cp .env.example .env
   ```

5. Update the DATABASE_URL in `.env` with your PostgreSQL connection string.

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the server:
   ```bash
   python main.py
   # Or with uvicorn:
   uvicorn main:app --reload --port 8003
   ```

The API will be available at `http://localhost:8003`.
API documentation at `http://localhost:8003/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd questionnarie-module/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5174`.

## API Documentation

### Questionnaire Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/questionnaires` | Create a new questionnaire |
| GET | `/api/questionnaires` | List questionnaires (paginated) |
| GET | `/api/questionnaires/{id}` | Get questionnaire by ID |
| PUT | `/api/questionnaires/{id}` | Update questionnaire |
| DELETE | `/api/questionnaires/{id}` | Soft delete questionnaire |
| POST | `/api/questionnaires/{id}/clone` | Clone questionnaire |
| GET | `/api/questionnaires/{id}/versions` | Get version history |
| POST | `/api/questionnaires/bulk-delete` | Bulk delete |
| POST | `/api/questionnaires/bulk-status` | Bulk status update |
| GET | `/api/questionnaires/types/list` | Get questionnaire types |
| GET | `/api/questionnaires/question-types/list` | Get question types |

### Query Parameters (List Endpoint)

| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default: 1) |
| page_size | int | Items per page (default: 20, max: 100) |
| search | string | Search in name and description |
| type | string | Filter by questionnaire type |
| status | string | Filter by status (draft, active, archived) |
| sort_by | string | Sort field (created_at, updated_at, name) |
| sort_order | string | Sort direction (asc, desc) |

## Questionnaire Types

- `eligibility` - Eligibility screening
- `screening` - General screening
- `baseline` - Baseline assessment
- `follow_up` - Follow-up visits
- `adverse_event` - Adverse event reporting
- `quality_of_life` - Quality of life surveys
- `custom` - Custom questionnaire

## Question Types

- `text` - Single line text input
- `textarea` - Multi-line text input
- `number` - Numeric input
- `email` - Email input
- `phone` - Phone number input
- `date` - Date picker
- `single_choice` - Radio buttons
- `multiple_choice` - Checkboxes
- `dropdown` - Select dropdown
- `rating` - Star rating
- `scale` - Likert scale
- `yes_no` - Yes/No toggle
- `section_header` - Section divider

## Next Phases

- **Phase 2**: Admin Questionnaire Management Portal
- **Phase 3**: Trial-Questionnaire Linking Module
- **Phase 4**: Vendor Portal (Trial-Specific View)
- **Phase 5**: Participant Portal (Eligibility & Registration)

## License

Proprietary - MannBiome
