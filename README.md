# shush

shush is a local, password-encrypted secrets manager for the command line. it allows you to securely store and retrieve secrets like api tokens, passwords, or environment variables using gpg encryption and a local sqlite database. designed to be minimal, offline, and developer-focused.

## features

- local-first architecture, no cloud or remote storage
- gpg-based symmetric encryption
- sqlite backend for secret storage
- simple cli interface powered by typer
- fernet encryption layer for stored values
- secure key hashing and cleanup
- works fully offline

## requirements

- python 3.8+
- gpg installed and available in $path

## installation

```bash
git clone git@github.com:ijwwsq/shush.git  
cd shush
python -m venv env
source env/bin/activate
pip install -r requirements.txt
chmod +x shush
ln -s $(pwd)/shush ~/.local/bin/shush  # optional: to use 'shush' globally
````

## usage

### initialize

create gpg environment, sqlite db, and store master password (encrypted using itself). prevents reinitialization if already set:

```bash
shush init
```

### add a secret

encrypt and save a secret by key. key is hashed before storing:

```bash
shush add github_token
```

### get a secret

decrypt and print a stored secret:

```bash
shush get github_token
```

### get and copy to clipboard

```bash
shush get github_token --copy
```

### remove a secret

```bash
shush remove github_token
```

### status

shows number of stored keys, last activity time, and db size:

```bash
shush status
```

example:

```bash
stored keys: 2
last activity: 2025-07-07 20:56:56.893925
last modification: 2025-07-07 20:56:56.891874
db size: 20480 bytes
```

## security

* all secrets are encrypted using fernet (symmetric aes)
* the fernet key is derived from your master password using sha-256
* the master password itself is stored encrypted with gpg, and only accessible by re-entering it
* secret keys are hashed with sha-256 before storing
* everything remains local and under your control
* recommended to use in a personal environment with disk encryption enabled

additional guarantees:

* sensitive data is explicitly cleared from memory after each operation
* the fernet key and master password live only within the scope of a single command
* no plaintext passwords or secrets are ever written to disk or held in memory longer than needed
* initialization is blocked if a repository already exists

## contributing

shush is a small but serious project. contributions, ideas, or feedback are very welcome — even a single suggestion can make it better.