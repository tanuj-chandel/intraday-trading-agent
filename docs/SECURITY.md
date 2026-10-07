# Security and Safety Policy

## Fundamental Operational Rules

1. **Paper Trading / Simulation Enforcement**:
   - Initial operational mode is hardcoded to `PAPER TRADING`.
   - Real money broker execution is disabled.

2. **No Hardcoded Credentials**:
   - No API keys, passwords, broker tokens, or secrets are hardcoded in the codebase.
   - All sensitive configurations are managed via environment variables (`.env`).

3. **No Secrets in Frontend / Git**:
   - The Next.js frontend strictly communicates via the `/api` backend proxy.
   - Broker secrets or database credentials are never transmitted to client browsers.

4. **Emergency Stop Safeguard**:
   - Prominent red Emergency Kill Switch available at all times.
   - Immediate execution cancellation and position squareoff.
