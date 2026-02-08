# Gmail Watcher

Gmail Watcher is a terminal UI app that monitors a Gmail inbox via IMAP, displays recent emails in real-time, and plays a 30-second alert sound when a new email arrives.

## Features

- Login with Gmail address and app password
- Real-time background polling for new emails (10-second intervals)
- Displays the last 10 emails in a scrollable list
- 30-second audio alert when new email arrives
- Stop alarm button to silence the alert
- Shows public IP address
- Persistent email history (doesn't clear on new emails)
- Log Out button to clear credentials and return to login

## Requirements

- Python 3.10+
- A Gmail account with 2-Step Verification enabled
- A Gmail App Password (required for IMAP login)
- FFplay, FFmpeg, or MPG123 for audio playback

## Setup

1. Create and activate a virtual environment

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies

   ```bash
   python -m pip install textual requests
   ```

3. Place an alert sound file

   Put your MP3 file in the project root as `alert.mp3`, or set the environment variable `ALERT_MP3` to an absolute path.

4. Install audio player (one of the following)

   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

## Running

Use the virtual environment Python to run the UI:

```bash
python uı.py
```

### Auto-start on Boot (Linux with systemd)

To automatically start Gmail Watcher when your computer boots:

1. Update the service file paths (if needed):

   ```bash
   sudo nano /home/daisy/gmail/gmail-watcher.service
   ```

2. Install the service:

   ```bash
   sudo cp /home/daisy/gmail/gmail-watcher.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable gmail-watcher.service
   sudo systemctl start gmail-watcher.service
   ```

3. Check service status:

   ```bash
   sudo systemctl status gmail-watcher.service
   ```

4. View logs:

   ```bash
   sudo journalctl -u gmail-watcher.service -f
   ```

5. Stop the service:

   ```bash
   sudo systemctl stop gmail-watcher.service
   ```

6. Disable auto-start:

   ```bash
   sudo systemctl disable gmail-watcher.service
   ```

## Controls

- **[L] Log Out**: Log out and return to login screen
- **[S] Alarm Stop**: Stop the currently playing alarm alert

## Gmail App Password

If login fails with "Invalid credentials", you need a Gmail App Password:
1. Go to your Google Account security settings
2. Enable 2-Step Verification if not already enabled
3. Generate an App Password for Mail
4. Use that 16-character password in the login screen

## Files

- `backend.py`: IMAP logic, state management, and mail polling
- `ip.py`: Public IP lookup helper
- `uı.py`: Textual terminal UI with real-time email display
- `monitoring.css`: UI styling

## Data Storage

- The app stores credentials in `credentials.json` in the project root
- Last seen email UID is stored in `watcher_state.json` to track new emails
- Credentials are deleted when you log out

## Alarm Behavior

- Alarm plays for 30 seconds when a new email arrives
- Use "Alarm Stop" button to silence the alert before it ends
- Alarm will not play again until a new email arrives (same email won't trigger multiple alerts)

## Troubleshooting

- **No emails displayed after login**: Make sure the monitor started successfully. Check the console for error messages.
- **New email doesn't show up**: Wait 10 seconds (polling interval) for the app to detect new mail
- **Alarm doesn't play**: 
  - Ensure `alert.mp3` exists in the project root
  - Check that ffplay, ffmpeg, or mpg123 is installed
  - Test audio with: `ffplay alert.mp3`
- **Login fails**: Use a Gmail App Password, not your regular Gmail password
- **Module import errors**: Ensure virtual environment is active and dependencies are installed

## License

Created for Gmail inbox monitoring and alerts.

