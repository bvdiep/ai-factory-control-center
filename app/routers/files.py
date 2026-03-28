import os
import shutil
import subprocess
import tempfile
from starlette.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.datastructures import UploadFile
from fasthtml.common import *
from sqlmodel import Session
from app.core.database import engine
from app.models import User, Project
from app.core.config import settings

file_modal_css = Style('''
    .file-modal::backdrop {
        background: rgba(0, 0, 0, 0.5);
    }
    .file-modal {
        max-width: 80vw;
        width: 80vw;
        max-height: 85vh;
        border: none;
        border-radius: 8px;
        padding: 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        overflow: hidden;
    }
    .file-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--pico-muted-border-color);
        background: var(--pico-card-background-color);
        position: sticky;
        top: 0;
        z-index: 1;
    }
    .file-modal-header h3 {
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .file-modal-content {
        padding: 1rem 1.5rem;
        overflow: auto;
        overflow-x: hidden;
        max-height: calc(85vh - 60px);
        max-width: 100%;
    }
    .file-modal-content pre {
        background: #f4f4f4;
        padding: 1rem;
        border-radius: 8px;
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
        word-break: break-all;
        overflow-x: hidden;
        max-width: 100%;
    }
    .file-modal-content code {
        white-space: pre-wrap;
        word-wrap: break-word;
        word-break: break-all;
    }
    .file-modal-loading {
        padding: 2rem;
        text-align: center;
        color: var(--pico-muted-color);
    }
    .file-table-type {
        width: 100px;
        min-width: 100px;
        max-width: 100px;
        text-align: right;
    }
    .file-actions {
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
    }
    .file-actions button, .file-actions a {
        padding: 0.25rem 0.5rem;
        font-size: 0.875rem;
        margin: 0;
    }
    table.striped th:not(:first-child),
    table.striped td:not(:first-child) {
        text-align: right;
    }
    table.striped th:first-child,
    table.striped td:first-child {
        width: 100%;
    }
    .breadcrumb-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        font-size: 1.1em;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .file-actions-bar {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        position: relative;
    }
    .file-actions-bar a {
        cursor: pointer;
        font-size: 0.9em;
    }
    .file-popup {
        display: none;
        position: absolute;
        top: 100%;
        right: 0;
        z-index: 10;
        background: var(--pico-card-background-color);
        border: 1px solid var(--pico-muted-border-color);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        margin-top: 0.25rem;
        min-width: 560px;
    }
    .file-popup.active {
        display: block;
    }
    .file-popup form {
        display: flex;
        gap: 0.75rem;
        align-items: stretch;
        margin: 0;
    }
    .file-popup input[type="file"] {
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        flex: 1;
        min-width: 300px;
    }
    .file-popup input[type="text"] {
        font-size: 1rem;
        padding: 0.5rem 0.75rem;
        flex: 1;
        min-width: 300px;
    }
    .file-popup button {
        padding: 0.25rem 0.25rem;
        font-size: 1rem;
        white-space: nowrap;
    }
''')

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'txt', 'md', 'csv', 'jpg', 'png', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_temp_dir(temp_dir: str):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def setup_file_routes(rt, render_nav):
    @rt('/projects/{project_id}/files')
    def project_files_root(project_id: int, session):
        return RedirectResponse(f'/projects/{project_id}/files/', status_code=303)

    @rt('/projects/{project_id}/files-content/{path:path}')
    def project_file_content(project_id: int, path: str, session):
        """API endpoint that returns raw file content for modal display."""
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            project = db_session.get(Project, project_id)
            if not user or not project:
                return P("Unauthorized", style="color: red; padding: 1rem;")

            base_dir = os.path.join(settings.PROJECT_ROOT, project.path)
            target_path = os.path.join(base_dir, path)

            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return P("Access Denied", style="color: red; padding: 1rem;")

            if not os.path.exists(target_path) or os.path.isdir(target_path):
                return P("File not found", style="color: red; padding: 1rem;")

            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                content = "Binary file or unsupported encoding."
            except Exception as e:
                content = f"Error reading file: {e}"

            return Pre(Code(content), style="background: #f4f4f4; padding: 1rem; border-radius: 8px; margin: 0; white-space: pre-wrap; word-wrap: break-word; word-break: break-all; max-width: 100%;")

    @rt('/projects/{project_id}/files/upload/{path:path}', methods=['POST'])
    async def upload_file(project_id: int, path: str, session, file: UploadFile):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            project = db_session.get(Project, project_id)
            if not user or not project:
                return RedirectResponse('/dashboard', status_code=303)

            base_dir = os.path.join(settings.PROJECT_ROOT, project.path)
            target_path = os.path.join(base_dir, path)

            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return RedirectResponse(f'/projects/{project_id}/files/{path}', status_code=303)

            if file.filename and allowed_file(file.filename):
                file_path = os.path.join(target_path, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

            return RedirectResponse(f'/projects/{project_id}/files/{path}', status_code=303)

    @rt('/projects/{project_id}/files/create-folder/{path:path}', methods=['POST'])
    async def create_folder(project_id: int, path: str, session, folder_name: str):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            project = db_session.get(Project, project_id)
            if not user or not project:
                return RedirectResponse('/dashboard', status_code=303)

            base_dir = os.path.join(settings.PROJECT_ROOT, project.path)
            target_path = os.path.join(base_dir, path)

            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return RedirectResponse(f'/projects/{project_id}/files/{path}', status_code=303)

            if folder_name:
                new_folder_path = os.path.join(target_path, folder_name)
                os.makedirs(new_folder_path, exist_ok=True)

            return RedirectResponse(f'/projects/{project_id}/files/{path}', status_code=303)

    @rt('/projects/{project_id}/files/delete/{path:path}', methods=['POST'])
    async def delete_item(project_id: int, path: str, session):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            project = db_session.get(Project, project_id)
            if not user or not project:
                return RedirectResponse('/dashboard', status_code=303)

            base_dir = os.path.join(settings.PROJECT_ROOT, project.path)
            target_path = os.path.join(base_dir, path)

            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return RedirectResponse(f'/projects/{project_id}/files/', status_code=303)

            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                else:
                    os.remove(target_path)

            parent_path = '/'.join(path.strip('/').split('/')[:-1])
            if parent_path:
                parent_path += '/'
            return RedirectResponse(f'/projects/{project_id}/files/{parent_path}', status_code=303)

    @rt('/projects/{project_id}/files/download/{path:path}')
    async def download_item(project_id: int, path: str, session):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            project = db_session.get(Project, project_id)
            if not user or not project:
                return RedirectResponse('/dashboard', status_code=303)

            base_dir = os.path.join(settings.PROJECT_ROOT, project.path)
            target_path = os.path.join(base_dir, path)

            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return RedirectResponse(f'/projects/{project_id}/files/', status_code=303)

            if not os.path.exists(target_path):
                return RedirectResponse(f'/projects/{project_id}/files/', status_code=303)

            if os.path.isfile(target_path):
                return FileResponse(target_path, filename=os.path.basename(target_path))
            else:
                # It's a directory
                is_root = (os.path.abspath(target_path) == os.path.abspath(base_dir))
                temp_dir = tempfile.mkdtemp()
                zip_filename = f"{os.path.basename(target_path) or project.name}.zip"
                zip_path = os.path.join(temp_dir, zip_filename)

                if is_root:
                    # Use rsync to exclude .gitignore files
                    gitignore_path = os.path.join(target_path, '.gitignore')
                    temp_sync_dir = os.path.join(temp_dir, 'sync')
                    os.makedirs(temp_sync_dir)
                    
                    rsync_cmd = ['rsync', '-a']
                    if os.path.exists(gitignore_path):
                        rsync_cmd.extend(['--exclude-from', gitignore_path])
                    rsync_cmd.extend(['--exclude', '.git'])
                    rsync_cmd.extend([f"{target_path}/", temp_sync_dir])
                    
                    subprocess.run(rsync_cmd, check=True)
                    
                    shutil.make_archive(zip_path[:-4], 'zip', temp_sync_dir)
                else:
                    shutil.make_archive(zip_path[:-4], 'zip', target_path)

                return FileResponse(zip_path, filename=zip_filename, background=BackgroundTask(cleanup_temp_dir, temp_dir))

    @rt('/projects/{project_id}/files/{path:path}')
    def project_files(project_id: int, path: str, session):
        user_id = session.get('user_id')
        with Session(engine) as db_session:
            user = db_session.get(User, user_id)
            project = db_session.get(Project, project_id)
            if not user or not project:
                return RedirectResponse('/dashboard', status_code=303)

            base_dir = os.path.join(settings.PROJECT_ROOT, project.path)
            target_path = os.path.join(base_dir, path)

            # Security check to prevent directory traversal
            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return Title("Error"), render_nav(user), Main(H1("Access Denied"), cls="container")

            if not os.path.exists(target_path):
                return Title("Error"), render_nav(user), Main(H1("File or directory not found"), cls="container")

            if os.path.isdir(target_path):
                # List directory
                items = []
                try:
                    for item in os.listdir(target_path):
                        item_path = os.path.join(target_path, item)
                        is_dir = os.path.isdir(item_path)
                        items.append({
                            'name': item,
                            'is_dir': is_dir,
                            'path': os.path.join(path, item).strip('/')
                        })
                except Exception as e:
                    return Title("Error"), render_nav(user), Main(H1(f"Error reading directory: {e}"), cls="container")

                # Sort: directories first, then files, both alphabetically
                items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

                # Breadcrumbs
                parts = path.strip('/').split('/') if path.strip('/') else []
                breadcrumbs = [A(project.name, href=f"/projects/{project_id}/files/")]
                current_path = ""
                for part in parts:
                    current_path += f"{part}/"
                    breadcrumbs.append(Span(" / "))
                    breadcrumbs.append(A(part, href=f"/projects/{project_id}/files/{current_path}"))

                file_list = []
                if path.strip('/'):
                    parent_path = '/'.join(parts[:-1])
                    file_list.append(
                        Tr(
                            Td(A("📁 ..", href=f"/projects/{project_id}/files/{parent_path}/" if parent_path else f"/projects/{project_id}/files/")),
                            Td(""),
                            Td("")
                        )
                    )

                for item in items:
                    icon = "📁 " if item['is_dir'] else "📄 "
                    
                    actions = Div(
                        A("Download", href=f"/projects/{project_id}/files/download/{item['path']}", cls="secondary outline"),
                        Form(
                            Button("Delete", type="submit", cls="secondary outline", style="color: red; border-color: red;"),
                            action=f"/projects/{project_id}/files/delete/{item['path']}",
                            method="post",
                            onsubmit="return confirm('Are you sure you want to delete this item?');",
                            style="margin: 0; display: inline;"
                        ),
                        cls="file-actions"
                    )

                    if item['is_dir']:
                        file_list.append(
                            Tr(
                                Td(A(f"{icon}{item['name']}", href=f"/projects/{project_id}/files/{item['path']}/")),
                                Td("Directory", cls="file-table-type"),
                                Td(actions)
                            )
                        )
                    else:
                        file_list.append(
                            Tr(
                                Td(A(
                                    f"{icon}{item['name']}",
                                    href="#",
                                    onclick=f"openFileModal('{item['name']}', '/projects/{project_id}/files-content/{item['path']}'); return false;"
                                )),
                                Td("File", cls="file-table-type"),
                                Td(actions)
                            )
                        )

                file_modal = Dialog(
                    Div(
                        Div(
                            H3("", id="file-modal-title"),
                            Button("✕", onclick="document.getElementById('file-modal').close()", cls="secondary outline", style="padding: 0.25rem 0.75rem;"),
                            cls="file-modal-header"
                        ),
                        Div(
                            P("Loading...", cls="file-modal-loading"),
                            id="file-modal-body",
                            cls="file-modal-content"
                        ),
                    ),
                    id="file-modal",
                    cls="file-modal"
                )

                upload_popup = Div(
                    Form(
                        Input(type="file", name="file", accept=".docx,.pdf,.txt,.md,.csv,.jpg,.png,.jpeg,.gif", required=True),
                        Button("Upload", type="submit"),
                        action=f"/projects/{project_id}/files/upload/{path}",
                        method="post",
                        enctype="multipart/form-data"
                    ),
                    id="upload-popup",
                    cls="file-popup"
                )

                folder_popup = Div(
                    Form(
                        Input(type="text", name="folder_name", placeholder="New Folder Name", required=True),
                        Button("Create", type="submit"),
                        action=f"/projects/{project_id}/files/create-folder/{path}",
                        method="post"
                    ),
                    id="folder-popup",
                    cls="file-popup"
                )

                actions_bar = Div(
                    A("Upload", onclick="togglePopup('upload-popup'); return false;", cls="outline", style="font-size: 0.9em; cursor: pointer;"),
                    A("New Folder", onclick="togglePopup('folder-popup'); return false;", cls="outline", style="font-size: 0.9em; cursor: pointer;"),
                    A("Download Current Folder", href=f"/projects/{project_id}/files/download/{path}", cls="outline", style="font-size: 0.9em;"),
                    upload_popup,
                    folder_popup,
                    cls="file-actions-bar"
                )

                breadcrumb_row = Div(
                    Div(*breadcrumbs),
                    actions_bar,
                    cls="breadcrumb-row"
                )

                file_modal_js = Script("""
                    function openFileModal(name, url) {
                        const modal = document.getElementById('file-modal');
                        const title = document.getElementById('file-modal-title');
                        const body = document.getElementById('file-modal-body');
                        title.textContent = name;
                        body.innerHTML = '<p class="file-modal-loading">Loading...</p>';
                        modal.showModal();
                        fetch(url)
                            .then(r => r.text())
                            .then(html => { body.innerHTML = html; })
                            .catch(() => { body.innerHTML = '<p class="file-modal-loading">Error loading file.</p>'; });
                    }
                    function togglePopup(id) {
                        document.querySelectorAll('.file-popup').forEach(p => {
                            if (p.id !== id) p.classList.remove('active');
                        });
                        document.getElementById(id).classList.toggle('active');
                    }
                    document.addEventListener('click', function(e) {
                        if (!e.target.closest('.file-actions-bar')) {
                            document.querySelectorAll('.file-popup').forEach(p => p.classList.remove('active'));
                        }
                    });
                """)

                return Title(f"Files - {project.name}"), file_modal_css, render_nav(user), Main(
                    file_modal_js,
                    Div(
                        H2(f"Files: {project.name}", style="margin-bottom: 0;"),
                        A("Back to Activity", href="/my-activity", cls="outline", style="margin-bottom: 0;"),
                        style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;"
                    ),
                    breadcrumb_row,
                    Table(
                        Thead(Tr(Th("Name"), Th("Type", cls="file-table-type"), Th("Actions"))),
                        Tbody(*file_list),
                        cls="striped"
                    ),
                    file_modal,
                    cls="container"
                )
            else:
                # View file - redirect to parent directory and open in modal
                parts = path.strip('/').split('/')
                parent_path = '/'.join(parts[:-1])
                return RedirectResponse(f'/projects/{project_id}/files/{parent_path}/', status_code=303)
