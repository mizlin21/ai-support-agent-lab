# KB-001: Login Issues After Password Reset

## Symptoms
- User cannot log in after resetting password
- "Invalid credentials" error appears
- Login fails immediately after password change

## Likely Causes
- Password reset did not fully propagate
- Cached credentials in browser
- Incorrect password re-entry
- Account lock due to repeated attempts

## Resolution Steps
1. Confirm the user is entering the correct updated password
2. Ask the user to log in using an incognito/private browser window
3. Clear browser cache and cookies
4. Wait 5–10 minutes and retry login (to allow system sync)
5. Attempt password reset again and use the newest password

## Escalate If
- User cannot log in after multiple password resets
- Issue affects multiple users
- Account appears locked or disabled

## Tags
authentication, login, password, access