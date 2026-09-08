# Frontend (Angular)

This folder contains the frontend SPA for the Talent Acquisition platform.

## Suggested stack
- Angular (standalone components)
- RxJS
- TypeScript

## Quick start
1. Install dependencies:
   npm install
2. Start dev server:
   npm run start

The app is configured to run at `http://localhost:4200`.

## Auth behavior
- Protected routes use an `AuthGuard` that redirects unauthenticated users to `/login`.
- An HTTP auth interceptor attaches `Authorization: Bearer <token>` to API requests.
- Any `401` response clears local session state and redirects to Sign In.

## Integration status behavior
- Dashboard and Sync Candidates pages show a live Zoho Recruit status pill (`Connected` / `Disconnected`).
- `IntegrationService` polls `GET /api/v1/integrations/zoho/status` and drives UI state.
- Sync action on the Sync Candidates page is disabled when Zoho status is disconnected.
