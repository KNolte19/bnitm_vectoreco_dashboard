import dropbox

DROPBOX_APP_KEY="cvg3inakt19tj78"
DROPBOX_APP_SECRET="z8y6dn6jath4frm"
DROPBOX_REFRESH_TOKEN="h1KoICWIXBoAAAAAAAAAAXVvOmyp3sj4QHtodyi5LLIIy_kCyFnB4RNCLmHsExJG"

dbx = dropbox.Dropbox(
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
)

def list_folders(path=""):
    result = dbx.files_list_folder(path, recursive=False)
    for entry in result.entries:
        if isinstance(entry, dropbox.files.FolderMetadata):
            print(f"[FOLDER] {entry.path_display}")
        else:
            print(f"[FILE]   {entry.path_display}")

    # Handle pagination
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                print(f"[FOLDER] {entry.path_display}")

# List root
list_folders("")