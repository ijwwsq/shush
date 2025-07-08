import gc
import re
import typer
import getpass
import pyperclip

from datetime import datetime, timedelta, timezone

from core.config import MASTER_KEY_PATH, LOG_PATH
from core.logs import log_event, parse_time_expr
from core.storage import (
    initialize_db, 
    get_secret, 
    save_secret, 
    delete_secret,
    get_status
)
from core.crypto import (
    initialize_gpg,
    encrypt_master_key,
    decrypt_master_key,
    derive_fernet_key
)

app = typer.Typer()
pyperclip.set_clipboard("xclip")  # fix later, wsl problem

@app.command()
def init():
    initialize_gpg()
    initialize_db()

    if MASTER_KEY_PATH.exists():
        typer.echo("error: repository already initialized", err=True)
        log_event("init_failed", "repository already initialized")
        raise typer.Exit(code=1)

    raw_password = bytearray(getpass.getpass("create master password: ").encode())
    raw_confirm = bytearray(getpass.getpass("confirm master password: ").encode())

    if raw_password != raw_confirm:
        typer.echo("error: passwords do not match", err=True)
        log_event("init_failed", "passwords did not match")
        for i in range(len(raw_password)): raw_password[i] = 0
        for i in range(len(raw_confirm)): raw_confirm[i] = 0
        del raw_password, raw_confirm
        gc.collect()
        raise typer.Exit(code=1)

    encrypt_master_key(raw_password.decode())
    log_event("init_success")

    for i in range(len(raw_password)): raw_password[i] = 0
    for i in range(len(raw_confirm)): raw_confirm[i] = 0
    del raw_password, raw_confirm
    gc.collect()

    typer.echo("shush initialized.")

@app.command()
def add(key: str):
    raw_pass = bytearray(getpass.getpass("enter your master password: ").encode())
    
    try:
        master = decrypt_master_key(raw_pass.decode())
    except RuntimeError as e:
        typer.echo(f"error: {e}", err=True)
        log_event("add_failed", f"decryption failed for key '{key}'")
        for i in range(len(raw_pass)): raw_pass[i] = 0
        del raw_pass
        gc.collect()
        raise typer.Exit(code=1)

    fernet = derive_fernet_key(master)
    raw_secret = bytearray(getpass.getpass(f"enter secret for '{key}': ").encode())
    save_secret(key, raw_secret.decode(), fernet)
    log_event("add", key=key)

    typer.echo(f"secret '{key}' saved.")

    for i in range(len(raw_pass)): raw_pass[i] = 0
    for i in range(len(raw_secret)): raw_secret[i] = 0
    del fernet, master, raw_pass, raw_secret
    gc.collect()

@app.command()
def get(key: str, copy: bool = typer.Option(False, "--copy", help="copy secret to clipboard")):
    raw_pass = bytearray(getpass.getpass("enter your master password: ").encode())
    
    try:
        password = decrypt_master_key(raw_pass.decode())
    except RuntimeError as e:
        typer.echo(f"error: {e}", err=True)
        log_event("get_failed", f"decryption failed for key '{key}'")
        del raw_pass
        gc.collect()
        raise typer.Exit(code=1)
    
    fernet = derive_fernet_key(password)
    value = get_secret(key, fernet)

    if copy:
        pyperclip.copy(value)
        typer.echo(f"secret '{key}' copied to clipboard.")
        typer.echo("warning: please clear your clipboard manually. ttl feature is coming soon")
        log_event("get", key=key, note="copied to clipboard")
    else:
        typer.echo(value)
        log_event("get", f"retrieved secret for key '{key}'")

    for i in range(len(raw_pass)): raw_pass[i] = 0
    del raw_pass, fernet, password, value
    gc.collect()

@app.command()
def remove(key: str):
    raw_pass = bytearray(getpass.getpass("enter master password: ").encode())
    master = decrypt_master_key(raw_pass.decode())
    fernet = derive_fernet_key(master)

    success = delete_secret(key)
    if success:
        typer.echo(f"secret '{key}' removed.")
        log_event("remove", f"removed secret for key '{key}'")
    else:
        typer.echo(f"no secret found for key '{key}'.")
        log_event("remove", key=key, status="failed", note="not found")

    for i in range(len(raw_pass)): raw_pass[i] = 0
    del raw_pass, master, fernet
    gc.collect()

@app.command()
def status():
    try:
        info = get_status()
        typer.echo(f"stored keys: {info['keys_count']}")
        typer.echo(f"last activity: {info['last_access']}")
        typer.echo(f"last modification: {info['last_modified']}")
        typer.echo(f"db size: {info['db_size_bytes']} bytes")
        log_event("status_checked")
    except Exception as e:
        typer.echo(f"error: {e}")
        log_event("status_failed", str(e))
    
@app.command()
def logs(
    since: str = typer.Option(None, help="filter logs since (e.g., 'today', '2h', '2025-07-08T10:00:00')"),
    until: str = typer.Option(None, help="filter logs until (e.g., '1h', '2025-07-08T12:00:00')"),
):
    entries = []

    with open(LOG_PATH, "r") as f:
        for line in f:
            try:
                ts = line[1:line.index("]")]
                dt = datetime.fromisoformat(ts).astimezone(timezone.utc)
                entries.append((dt, line.strip()))
            except Exception:
                continue

    if since:
        since_dt = parse_time_expr(since)
        entries = [e for e in entries if e[0] >= since_dt]

    if until:
        until_dt = parse_time_expr(until)
        entries = [e for e in entries if e[0] <= until_dt]

    for _, line in entries:
        print(line)

    log_event("log", status="succes", note="log file accessed")

if __name__ == '__main__':
    app()
