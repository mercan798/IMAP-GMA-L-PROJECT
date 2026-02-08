from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Button, Label
from textual.screen import Screen
import backend
import threading
import time
import os
import subprocess
import hashlib
import importlib.util
from pathlib import Path

try:
    import ip as _ip
except Exception:
    _ip = None

if _ip is None or not hasattr(_ip, "get_ip_async"):
    _ip_path = Path(__file__).with_name("ip.py")
    _spec = importlib.util.spec_from_file_location("local_ip", _ip_path)
    _ip = importlib.util.module_from_spec(_spec) if _spec else None
    if _spec and _spec.loader and _ip is not None:
        _spec.loader.exec_module(_ip)

ip = _ip


class LoginScreen(Screen):
    CSS = """
    LoginScreen {
        align: center middle;
    }
    
    #login-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2;
        background: $surface;
    }
    
    Label {
        margin: 1 0;
    }
    
    Input {
        width: 100%;
        margin: 1 0;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    
    #error-msg {
        color: $error;
        text-align: center;
        margin-top: 1;
    }
    
    #success-msg {
        color: $success;
        text-align: center;
        margin-top: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(id="login-container"):
            yield Label("Gmail Watcher - Login")
            yield Label("Enter your Gmail credentials")
            
            yield Label("Gmail Address:")
            yield Input(placeholder="your.email@gmail.com", id="email-input")
            
            yield Label("App Password:")
            yield Input(password=True, placeholder="16-character app password", id="password-input")
            
            yield Button("LOGIN", variant="primary", id="login-btn")
            yield Static("", id="error-msg")
            yield Static("", id="success-msg")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self.handle_login()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.handle_login()
    
    def handle_login(self) -> None:
        try:
            email = self.query_one("#email-input", Input).value.strip()
            password = self.query_one("#password-input", Input).value.strip()
            error_msg = self.query_one("#error-msg", Static)
            success_msg = self.query_one("#success-msg", Static)
            
            if not email or not password:
                error_msg.update("Please enter both email and password")
                success_msg.update("")
                return
            
            error_msg.update("Testing connection...")
            success_msg.update("")
            
            success, error = backend.test_connection(email, password)
            
            if success:
                backend.save_credentials(email, password)
                success_msg.update("Login successful!")
                error_msg.update("")
                self.app.push_screen(MonitoringScreen(email, password))
            else:
                error_msg.update(f"Login failed: {error}")
                success_msg.update("")
                
        except Exception as e:
            self.query_one("#error-msg", Static).update(f"Error: {str(e)}")


class MonitoringScreen(Screen):
    CSS_PATH = "monitoring.css"
    
    def __init__(self, email_user, email_pass):
        super().__init__()
        self.email_user = email_user
        self.email_pass = email_pass
        self.monitor = None
        self.monitor_running = False
        self.user_ip = "Getting IP..."
        self.alert_playing = False
        self.alert_playing_thread = None
        self.last_alert_email = None
        self.cached_mails = []

        try:
            self.monitor = backend.EmailMonitor(email_user, email_pass, callback=self.on_new_email)
            self.monitor.start()
            self.monitor_running = True
        except Exception as e:
            print(f"Monitor error: {e}")
            self.monitor_running = False
        
        if ip and hasattr(ip, "get_ip_async"):
            ip.get_ip_async(self.on_ip_fetched)
        else:
            self.on_ip_fetched("Unknown")
    
    def on_ip_fetched(self, ip_address: str) -> None:
        self.user_ip = ip_address
        try:
            ip_display = self.query_one("#ip-display", Static)
            ip_display.update(f"Your IP: {self.user_ip}")
        except Exception as e:
            pass
    
    def compose(self) -> ComposeResult:
        with Vertical(id="header"):
            yield Label(f"Monitoring: {self.email_user}")
        
        yield Static("", id="notification")
        
        with ScrollableContainer(id="email-list"):
            yield Static("Loading emails...", id="email-status")
        
        with Horizontal(id="footer-bar"):
            yield Label("[L] Log Out", id="logout-label")
            yield Button("", variant="error", id="logout-btn")
            yield Label("[S] Alarm Stop", id="stop-label")
            yield Button("", variant="warning", id="stop-alarm-btn")
            yield Static("", id="action-status")
            yield Static(f"Your IP: {self.user_ip}", id="ip-display")
    
    def on_mount(self) -> None:
        try:
            self.load_emails()
            self.set_interval(5, self.load_emails)
            if ip and hasattr(ip, "get_ip_async"):
                ip.get_ip_async(self.on_ip_fetched)
        except Exception as e:
            print(f"Mount error: {e}")
    
    def load_emails(self) -> None:
        try:
            if self.monitor and self.monitor_running:
                mails = self.monitor.get_mails(10)
                self.display_emails(mails)
        except Exception as e:
            print(f"Load error: {e}")
    
    def display_emails(self, mails) -> None:
        try:
            if not mails:
                mails = []
            
            self.cached_mails = mails
            email_list = self.query_one("#email-list", ScrollableContainer)
            
            for child in list(email_list.children):
                try:
                    child.remove()
                except:
                    pass
            
            if mails and len(mails) > 0:
                for mail in reversed(mails):
                    try:
                        from_addr = mail.get('from', 'Unknown')
                        subject = mail.get('subject', 'No Subject')
                        date = mail.get('date', 'Unknown')
                        mail_text = f"From: {from_addr}\nSubject: {subject}\nDate: {date}"
                        item = Static(mail_text, classes="email-item")
                        email_list.mount(item)
                    except Exception as e:
                        print(f"Error adding email: {e}")
            else:
                email_list.mount(Static("No emails yet.", id="email-status"))
        except Exception as e:
            print(f"Display error: {e}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        try:
            if event.button.id == "logout-btn":
                self.show_notification("Logging out...")
                self.update_action_status("Logging out...")
                self.logout()
            elif event.button.id == "stop-alarm-btn":
                self.stop_alarm()
                self.show_notification("Alarm stopped")
                self.update_action_status("Alarm stopped")
        except Exception as e:
            print(f"Button error: {e}")
    
    def on_new_email(self, mail) -> None:
        try:
            email_id = f"{mail.get('from', '')}{mail.get('subject', '')}{mail.get('date', '')}"
            email_hash = hashlib.md5(email_id.encode()).hexdigest()
            
            if self.last_alert_email == email_hash:
                return
            
            self.last_alert_email = email_hash
            
            print(f"New email detected: {mail.get('subject', 'No Subject')}")
            
            try:
                time.sleep(0.5)
                self.load_emails()
                time.sleep(0.3)
                self.load_emails()
            except Exception as e:
                print(f"Reload error: {e}")
            
            self.play_alert_background()
            
        except Exception as e:
            print(f"New email error: {e}")
    
    def play_alert_background(self) -> None:
        def play_mp3():
            try:
                mp3_file = os.getenv("ALERT_MP3", "alert.mp3")
                
                if not os.path.exists(mp3_file):
                    print(f"MP3 not found: {mp3_file}")
                    return
                
                os.system("killall ffplay ffmpeg mpg123 paplay 2>/dev/null")
                time.sleep(0.2)
                
                try:
                    proc = subprocess.Popen(
                        ["ffplay", "-nodisp", "-autoexit", "-ss", "50", "-t", "30", mp3_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    proc.wait(timeout=40)
                    return
                except Exception as e:
                    print(f"ffplay attempt failed: {e}")
                
                try:
                    proc = subprocess.Popen(
                        ["mpg123", mp3_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    time.sleep(30)
                    proc.terminate()
                    return
                except Exception as e:
                    print(f"mpg123 attempt failed: {e}")
                
            except Exception as e:
                print(f"Alert error: {e}")
        
        self.alert_playing = True
        self.alert_playing_thread = threading.Thread(target=play_mp3, daemon=True)
        self.alert_playing_thread.start()
    
    def show_notification(self, message: str) -> None:
        try:
            notification = self.query_one("#notification", Static)
            notification.update(message)
            self.set_timer(3, self.clear_notification)
        except Exception:
            pass

    def clear_notification(self) -> None:
        try:
            notification = self.query_one("#notification", Static)
            notification.update("")
        except:
            pass

    def update_action_status(self, message: str) -> None:
        try:
            status = self.query_one("#action-status", Static)
            status.update(message)
        except Exception:
            pass
            
    def stop_alarm(self) -> None:
        try:
            self.alert_playing = False
            os.system("killall ffplay ffmpeg mpg123 paplay 2>/dev/null")
            os.system("pkill -f 'ffplay|ffmpeg|mpg123|paplay' 2>/dev/null")
            print("Alarm stopped")
        except:
            pass
    
    def logout(self) -> None:
        try:
            self.stop_alarm()
            self.last_alert_email = None
            self.monitor_running = False
            
            if self.monitor:
                try:
                    if hasattr(self.monitor, 'is_running') and self.monitor.is_running():
                        self.monitor.stop()
                except:
                    pass
            
            try:
                backend.delete_credentials()
            except:
                pass
            
            self.app.pop_screen()
            self.app.push_screen(LoginScreen())
        except Exception as e:
            print(f"Logout error: {e}")


class GmailWatcherApp(App):
    TITLE = "Gmail Watcher"
    
    def on_mount(self) -> None:
        try:
            creds = backend.load_credentials()
            if creds and creds.get('email') and creds.get('password'):
                self.push_screen(MonitoringScreen(creds['email'], creds['password']))
            else:
                self.push_screen(LoginScreen())
        except Exception as e:
            print(f"App error: {e}")
            self.push_screen(LoginScreen())


if __name__ == "__main__":
    try:
        app = GmailWatcherApp()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()