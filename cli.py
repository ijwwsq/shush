import gc
import typer
import getpass
import pyperclip

from core.config import MASTER_KEY_PATH

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
pyperclip.set_clipboard("xclip") # fix later, wsl problem

@app.command()
def init():
    initialize_gpg()
    initialize_db()

    if MASTER_KEY_PATH.exists():
        typer.echo("error: repository already initialized", err=True)
        raise typer.Exit(code=1)

    password = getpass.getpass("create master password: ")
    password_confirm = getpass.getpass("confirm master password: ")
    if password != password_confirm:
        typer.echo("error: passwords do not match", err=True)
        raise typer.Exit(code=1)

    encrypt_master_key(password)
    # optional: del password, password_confirm; gc.collect()
    typer.echo("shush initialized.")

@app.command()
def add(key: str):
    passphrase = getpass.getpass("enter your master password: ")
    master = decrypt_master_key(passphrase)
    fernet = derive_fernet_key(master)

    value = getpass.getpass(f"enter secret for '{key}': ")
    save_secret(key, value, fernet)
    typer.echo(f"secret '{key}' saved.")

    del fernet, master, passphrase, value
    gc.collect()

@app.command()
def get(
    key: str,
    copy: bool = typer.Option(False, "--copy", help="copy secret to clipboard")
):
    passphrase = getpass.getpass("enter your master password: ")
    password = decrypt_master_key(passphrase)
    fernet = derive_fernet_key(password)
    value = get_secret(key, fernet)

    if copy:
        pyperclip.copy(value)
        typer.echo(f"secret '{key}' copied to clipboard.")
    else:
        typer.echo(value)

    del fernet, password, passphrase, value
    gc.collect()

@app.command()
def remove(key: str):
    passphrase = getpass.getpass("enter master password: ")
    master = decrypt_master_key(passphrase)
    fernet = derive_fernet_key(master)

    success = delete_secret(key)
    if success:
        typer.echo(f"secret '{key}' removed.")
    else:
        typer.echo(f"no secret found for key '{key}'.")

    del password
    gc.collect()

@app.command()
def status():
    try:
        info = get_status()
        typer.echo(f"stored keys: {info['keys_count']}")
        typer.echo(f"last activity: {info['last_access']}")
        typer.echo(f"last modification: {info['last_modified']}")
        typer.echo(f"db size: {info['db_size_bytes']} bytes")
    except Exception as e:
        typer.echo(f"error: {e}")

if __name__ == '__main__':
    app()
