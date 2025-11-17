# Patient Onboarding Workflow

## Overview
The patient onboarding workflow is a complete end-to-end process that takes a potential patient from initial inquiry through to becoming an active client ready for therapy sessions.

## Workflow Steps

### 1. Contact Form Submission
**Location:** `/contact` (frontend)
**Backend:** `POST /v1/inquiries`

- Patient fills out contact form with:
  - Name
  - Email
  - Phone
  - Concerns/reason for seeking therapy

**What Happens:**
- Creates an `Inquiry` record in the database
- Creates or updates a `Client` record with status `ONBOARDING`
- Sends welcome email with onboarding link
- Returns success with onboarding URL

**API Request:**
```bash
curl -X POST http://localhost:8000/v1/inquiries \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-tenant" \
  -H "X-Idempotency-Key: inquiry-12345" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "concerns": "Experiencing anxiety and stress"
  }'
```

### 2. Welcome Email
**Triggered by:** Contact form submission

- Patient receives email with:
  - Welcome message
  - Onboarding link: `/onboarding/{client_id}`
  - Instructions for next steps
  - Estimated time (10-15 minutes)

**Email Template:** `email_service.send_welcome_email()`

### 3. Intake Form
**Location:** `/onboarding/{client_id}` - Step 1
**Backend:** `POST /v1/intake/{client_id}`

Patient completes comprehensive intake form:
- Date of birth
- Presenting concerns (detailed)
- Previous therapy experience
- Current medications
- Emergency contact (name + phone)
- Insurance information (provider + member ID)
- Preferred session type (video/phone/in-person)
- Therapy goals

**What Happens:**
- Saves intake data to `Client.intake_data` JSON field
- Extracts key fields to dedicated columns
- Updates client status to `ONBOARDING` if not already
- Returns success with next step

**API Request:**
```bash
curl -X POST http://localhost:8000/v1/intake/{client_id} \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-tenant" \
  -d '{
    "date_of_birth": "1990-01-15",
    "presenting_concerns": "Anxiety and work-related stress",
    "previous_therapy": "Yes, CBT for 6 months in 2019",
    "medications": "Lexapro 10mg daily",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+1234567890",
    "insurance_provider": "Blue Cross Blue Shield",
    "insurance_member_id": "ABC123456",
    "preferred_session_type": "video",
    "goals": "Better stress management and coping strategies"
  }'
```

### 4. Consent Forms
**Location:** `/onboarding/{client_id}` - Step 2
**Backend:**
- `GET /v1/intake/{client_id}/consents` (list consents)
- `POST /v1/intake/{client_id}/consents/{consent_type}` (sign each)

Patient reviews and signs required consent forms:

**Required Consents:**
1. `treatment_consent` - Consent for Treatment
2. `telehealth_consent` - Telehealth Services Consent
3. `privacy_hipaa` - Privacy Practices & HIPAA
4. `financial_agreement` - Financial Agreement

**Optional Consents:**
5. `recording_consent` - Session Recording Consent

**What Happens:**
- Each consent signature creates a `Consent` record
- System checks if all required consents are signed
- If all required consents signed AND intake complete → auto-activate client

**API Requests:**
```bash
# Get available consents
curl http://localhost:8000/v1/intake/{client_id}/consents \
  -H "X-Tenant-ID: demo-tenant"

# Sign a consent
curl -X POST http://localhost:8000/v1/intake/{client_id}/consents/treatment_consent \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-tenant" \
  -d '{}'
```

### 5. Complete Onboarding
**Location:** `/onboarding/{client_id}` - Step 3
**Backend:** `POST /v1/intake/{client_id}/complete`

**What Happens:**
- Verifies intake form is complete
- Verifies all required consents are signed
- Updates client status to `ACTIVE`
- Sends completion email with dashboard link
- Returns success

**API Request:**
```bash
curl -X POST http://localhost:8000/v1/intake/{client_id}/complete \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-tenant"
```

### 6. Completion Email
**Triggered by:** Onboarding completion

Patient receives congratulatory email with:
- Welcome to active status message
- What happens next (therapist matching within 24h)
- Dashboard link
- Support contact information

**Email Template:** `email_service.send_onboarding_complete_email()`

### 7. Success Screen
**Location:** `/onboarding/{client_id}` - Final step

Patient sees completion screen with:
- Success message
- Next steps overview
- Button to go to dashboard
- Information about therapist matching

## Testing the Workflow

### Prerequisites
1. Backend running: `cd irteqa-health-api && python -m uvicorn main:app --reload --port 8000`
2. Frontend running: `cd irteqa-frontend-app && npm run dev`
3. `.env` file configured (optional: email credentials for actual email sending)

### Test Steps

1. **Navigate to Contact Form**
   ```
   http://localhost:3000/contact
   ```

2. **Fill Out Contact Form**
   - Name: Test User
   - Email: test@example.com
   - Phone: +1234567890
   - Concerns: Test inquiry

3. **Submit and Get Onboarding Link**
   - Click "Submit Inquiry"
   - Note the onboarding link displayed
   - Click "Start Onboarding"

4. **Complete Intake Form**
   - Fill all required fields marked with *
   - Date of birth, concerns, emergency contact, etc.
   - Click "Continue to Consents"

5. **Sign Consent Forms**
   - Review each required consent
   - Check all 4 required consent checkboxes
   - Click "Submit & Complete Onboarding"

6. **View Success Screen**
   - Verify "Welcome Aboard!" message
   - See next steps information
   - Can click "Go to Dashboard"

### Verify in Database

```bash
# Check client status
sqlite3 irteqa-health-api/irteqa_health.db "SELECT id, name, email, status FROM clients WHERE email='test@example.com';"

# Check consents
sqlite3 irteqa-health-api/irteqa_health.db "SELECT client_id, consent_type, signed FROM consents WHERE client_id='<client_id>';"
```

### Verify Emails (Development Mode)

If SMTP credentials are not configured, emails will be logged to console:

```
[EMAIL] Would send email:
  To: test@example.com
  Subject: Welcome to Irteqa Health - Let's Get Started
  ...
```

## API Endpoints

### Inquiries
- `POST /v1/inquiries` - Create inquiry and start onboarding

### Intake
- `GET /v1/intake/{client_id}` - Get intake status
- `POST /v1/intake/{client_id}` - Submit intake form
- `GET /v1/intake/{client_id}/consents` - List required consents
- `POST /v1/intake/{client_id}/consents/{consent_type}` - Sign consent
- `POST /v1/intake/{client_id}/complete` - Complete onboarding

### Clients
- `GET /v1/clients` - List all clients
- `GET /v1/clients/{id}` - Get client details

## Database Schema

### Client
```sql
CREATE TABLE clients (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    status TEXT NOT NULL, -- ONBOARDING, ACTIVE, INACTIVE, TERMINATED
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    date_of_birth DATE,
    concerns TEXT,
    intake_data JSON,
    insurance_provider TEXT,
    insurance_member_id TEXT,
    assigned_therapist_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Inquiry
```sql
CREATE TABLE inquiries (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    concerns TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Consent
```sql
CREATE TABLE consents (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    consent_type TEXT NOT NULL,
    signed BOOLEAN NOT NULL DEFAULT FALSE,
    signed_at TIMESTAMP,
    artifact_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
```

## Client Status Flow

```
INQUIRY → ONBOARDING → ACTIVE → (INACTIVE/TERMINATED)
```

- **ONBOARDING**: Client created from inquiry, completing intake/consents
- **ACTIVE**: All requirements met, ready for sessions
- **INACTIVE**: Client paused or on break
- **TERMINATED**: Client ended care

## Auto-Activation Logic

Client is automatically activated when:
1. ✅ Intake form is submitted (`client.intake_data` is not null)
2. ✅ All 4 required consents are signed:
   - treatment_consent
   - telehealth_consent
   - privacy_hipaa
   - financial_agreement

This happens either:
- When signing the last required consent
- When calling the `/complete` endpoint

## Future Enhancements (TODOs)

1. **Therapist Matching** (intake.py line 114)
   - Auto-assign therapist based on specialties
   - Consider availability and patient preferences
   - Match based on insurance networks

2. **Automated Reminders** (Celery tasks)
   - Send reminder if intake not completed in 24h
   - Send reminder if consents not signed in 48h
   - Weekly check-ins during onboarding

3. **Therapist Assignment Notification**
   - Email patient when therapist is assigned
   - Include therapist bio and photo
   - Include link to schedule first session

4. **Session Scheduling**
   - Enable session booking after activation
   - Calendar integration
   - Automated reminders

## Support & Troubleshooting

### Common Issues

**Email not sending:**
- Check `.env` file has SMTP credentials
- In development, emails are logged to console
- Verify `email_service.py` initialization

**Client not activating:**
- Verify all 4 required consents are signed
- Verify intake_data is not null
- Check client status in database

**Onboarding link invalid:**
- Ensure client_id in URL is valid UUID
- Check client exists: `GET /v1/clients`
- Verify tenant_id header matches

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Backend Logs

Watch for these log messages:
- `[INQUIRY] Welcome email sent to {email}`
- `[INTAKE] Intake form submitted for client {id}`
- `[INTAKE] Client {id} completed onboarding - now active`
- `[INTAKE] Completion email sent to {email}`

## Contact

For questions or issues:
- Email: support@irteqa.com
- GitHub Issues: [repository]/issues
