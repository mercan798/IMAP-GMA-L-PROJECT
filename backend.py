
import os
import json
import imaplib
import email
from email.header import decode_header
import threading
import time

STATEF = "watcher_state.json"
CREDENTIALSF = "credentials.json"
ALERT_MP3 = "alert.mp3"

def decode_mime(s):
    if not s:
        return "-"
    out = []
    for part, enc in decode_header(s):
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(part)
    return "".join(out).strip() or "-"

def load_state():
    try:
        with open(STATEF, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_uid": None}

def save_state(st_data):
    try:
        with open(STATEF, "w", encoding="utf-8") as f:
            json.dump(st_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

def load_credentials():
    try:
        with open(CREDENTIALSF, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_credentials(email_user, email_pass):
    try:
        with open(CREDENTIALSF, "w", encoding="utf-8") as f:
            json.dump({"email": email_user, "password": email_pass}, f)
    except Exception as e:
        print(f"Error saving credentials: {e}")

def delete_credentials():
    try:
        if os.path.exists(CREDENTIALSF):
            os.remove(CREDENTIALSF)
    except Exception as e:
        print(f"Error deleting credentials: {e}")

def test_connection(email_user, email_pass):
    try:
        M = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        M.login(email_user, email_pass)
        M.select("INBOX")
        M.logout()
        return True, None
    except Exception as e:
        raw = str(e)
        if isinstance(getattr(e, "args", None), tuple) and e.args:
            try:
                if isinstance(e.args[0], bytes):
                    raw = e.args[0].decode("utf-8", errors="replace")
                else:
                    raw = str(e.args[0])
            except Exception:
                pass
        msg = raw.strip("b\"'")
        if "Invalid credentials" in msg or "AUTHENTICATIONFAILED" in msg.upper():
            msg = "Invalid credentials. Use a Gmail App Password."
        return False, msg

def imap_login(email_user, email_pass): 
    M = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    M.login(email_user, email_pass)
    M.select("INBOX")
    return M

def last_uid(m):
    ok, data = m.uid("search", None, "ALL")
    if ok != "OK" or not data or not data[0]:
        return None
    uids = data[0].split()
    return uids[-1] if uids else None

def header(m, uid):
    ok, data = m.uid("fetch", uid, "(RFC822.HEADER)")
    if ok != "OK" or not data or not data[0]:
        return None
    msg = email.message_from_bytes(data[0][1])
    return {
        "subject": decode_mime(msg.get("Subject")),
        "from": decode_mime(msg.get("From")),
        "date": decode_mime(msg.get("Date")),
        "uid": uid.decode() if isinstance(uid, bytes) else str(uid)
    }

def check_new_mail(state, email_user, email_pass):
    try:
        M = imap_login(email_user, email_pass)
        uid = last_uid(M)
        
        if uid:
            uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
            
            if uid_str != state.get("last_uid"):
                hdr = header(M, uid)
                if hdr:
                    state["last_uid"] = uid_str
                    save_state(state)
                    M.logout()
                    return hdr, True, None
        
        M.logout()
        return None, False, None
    except Exception as e:
        return None, False, str(e)

def get_last_mails(email_user, email_pass, n=10):
    try:
        M = imap_login(email_user, email_pass)
        ok, data = M.uid("search", None, "ALL")
        if ok != "OK" or not data or not data[0]:
            M.logout()
            return []
        
        uids = data[0].split()[-n:]
        mails = []
        
        for uid in uids:
            hdr = header(M, uid)
            if hdr:
                mails.append(hdr)
        
        M.logout()
        return mails
    except Exception as e:
        print(f"Error getting mails: {e}")
        return []

def play_alarm_mp3(mp3_path, duration=30):
    if not os.path.exists(mp3_path):
        print(f"Alert sound not found: {mp3_path}")
        return
    
    try:
        from playsound import playsound
        playsound(mp3_path)
        print("Alert played")
        return
    except Exception as e:
        print(f"playsound failed: {e}")
    
    try:
        os.system(f'timeout {duration}s ffplay -nodisp -autoexit "{mp3_path}" 2>/dev/null &')
        return
    except:
        pass
    
    try:
        os.system(f'timeout {duration}s mpg123 "{mp3_path}" 2>/dev/null &')
        return
    except:
        pass
    
    print("Could not play alert")

def play_alarm_thread(mp3_path, duration=30):
    thread = threading.Thread(target=play_alarm_mp3, args=(mp3_path, duration), daemon=True)
    thread.start()



class EmailMonitor:
    
    def __init__(self, email_user, email_pass, callback=None, interval=10):
        self.email_user = email_user
        self.email_pass = email_pass
        self.callback = callback
        self.interval = interval
        self.running = False
        self.thread = None
        self.state = load_state()
        
    def start(self):
        if not self.running:
            self.running = True
            try:
                if not self.state.get("last_uid"):
                    M = imap_login(self.email_user, self.email_pass)
                    uid = last_uid(M)
                    if uid:
                        uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)
                        self.state["last_uid"] = uid_str
                        save_state(self.state)
                    M.logout()
            except Exception as e:
                print(f"Init state error: {e}")
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _monitor_loop(self):
        while self.running:
            try:
                mail, is_new, error = check_new_mail(self.state, self.email_user, self.email_pass)
                
                if is_new and mail and self.callback:
                    self.callback(mail)
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(self.interval)
    
    def get_mails(self, n=10):
        return get_last_mails(self.email_user, self.email_pass, n)