set dotenv-load := true

remote_server := env("REMOTE_SERVER")
remote_path := env("REMOTE_PLUGIN_PATH")
rsync_remote := remote_server + ":" + remote_path
rsync_flags := "-avLh --progress --stats --itemize-changes --delete"
upload_excludes := """--exclude=.jj/ --exclude=.git/ --exclude=.ruff_cache/ --exclude=.venv/ --exclude=data/ --exclude=__pycache__"""

upload:
    rsync {{ rsync_flags }} {{ upload_excludes }} . {{ rsync_remote }}

export-deps:
    uv export --no-dev --prune astrbot --format requirements.txt --output-file requirements.txt
