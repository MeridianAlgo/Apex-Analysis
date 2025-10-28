# Security and Vulnerability Disclosure

We take security seriously. If you discover a security vulnerability in this project, please report it privately to the maintainers so we can respond and remediate before public disclosure.

Contact
- Email: meridianaglo@gmail.com

What to include in a report
- Affected component/file (for example: `src/fetch_data.py`)
- A clear description of the vulnerability and the potential impact
- Reproduction steps and/or proof-of-concept code
- The version of the repository or a git commit hash where the issue is present
- Any suggested mitigation or fix (optional)

How we handle reports
- We'll acknowledge receipt within 48 hours.
- We'll triage and provide an estimated timeline for a fix within 7 business days.
- For critical vulnerabilities, we aim to produce a patch within 30 days where feasible.
- We will coordinate a disclosure plan and notify you when a patched release is available.

Responsible disclosure
- Do not publicly disclose the vulnerability until a fix has been released and the maintainers have agreed to a coordinated disclosure schedule.

Third-party dependencies
- This project uses several third-party Python packages (see `requirements.txt`). If you discover a vulnerability in a dependency, consider reporting it to the upstream project as well as notifying us.

Security best practices for contributors
- Avoid committing secrets (API keys, credentials) to the repository.
- Use environment variables or a secrets manager for any sensitive configuration.
- Keep dependencies up-to-date and apply security updates promptly.

If you need to send sensitive information (e.g., exploit code) securely, request a secure channel via the contact email.
