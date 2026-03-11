# Phase 5: Message Composer & AI Rephrasing

## Goal
Build the Compose page where the user writes a primary message and previews AI-generated variants before broadcasting.

## Backend Tasks

### 5.1 Message service (`services/message.py`)
- `MessageService` class
- `generate_variants(base_message, count=5)`:
  - Call Claude API with a prompt like:
    ```
    Rephrase the following message {count} different ways.
    Keep the same meaning and intent but vary the wording,
    sentence structure, and tone slightly. Make each version
    sound natural and human-written. Do not add or remove
    any key information.

    Original message:
    "{base_message}"

    Return each variant on a new line, numbered 1-{count}.
    ```
  - Parse response into a list of message variants
  - Return variants
- `generate_single_variant(base_message)`:
  - Generate one unique variant (used during broadcast for each contact)
  - Slightly different prompt to maximize variation

### 5.2 Compose routes (`routes/compose.py`)
- `POST /api/compose/preview` — Body: `{base_message, count}` → returns list of variants
  - Validates: message not empty, count between 1-10

## Frontend Tasks

### 5.3 Compose page (`pages/Compose.jsx`)
- **Message input**: Large textarea for writing the primary message
- **Preview count**: Dropdown or input (1-10, default 5)
- **"Generate Previews" button** → POST /api/compose/preview
- **Variants display**: Cards showing each AI-generated variant
  - Each variant in a styled card with variant number
  - "Regenerate" button to get new variants
- **Message stats**: Character count, word count
- **Note to user**: "During broadcast, each contact will receive a uniquely rephrased version of your message"

### 5.4 UX details
- Loading state while AI generates variants
- Copy-to-clipboard on each variant (for manual use)
- Warn if message is too long (>500 chars) — longer messages = more variation but slower
- Save the primary message to use in broadcast

## Verification
- Write a message → click Generate → 5 unique variants appear
- Each variant conveys the same meaning but reads differently
- Regenerate → new set of variants
- Empty message → validation error
- Claude API key not set → clear error pointing to Settings
