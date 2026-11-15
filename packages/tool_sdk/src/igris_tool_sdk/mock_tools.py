"""Mock Tool Implementations for Testing in Phase 1.

These mock tools provide verifiable execution targets to validate the mediation pipeline
without connecting to real email servers, production clouds, or client repositories.
"""

from typing import Dict, Any, List


def mock_read_email(folder: str = "INBOX", limit: int = 5) -> List[Dict[str, Any]]:
    return [
        {"id": "msg_1", "subject": "Acme Project Updates", "from": "john@acme.com"},
        {"id": "msg_2", "subject": "Weekly Newsletter", "from": "news@tech.com"},
    ]


def mock_search_repo(query: str, path: str = ".") -> List[str]:
    return [f"found match for '{query}' in src/main.py", "match in README.md"]


def mock_view_diff(path: str = ".") -> str:
    return "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old_code()\n+new_code()"


def mock_write_file(path: str, content: str) -> Dict[str, Any]:
    return {"status": "written", "bytes": len(content), "path": path}


def mock_git_branch_commit(branch: str, message: str) -> Dict[str, Any]:
    return {"status": "committed", "branch": branch, "commit_hash": "a1b2c3d4"}


def mock_deploy_staging(service: str, commit: str) -> Dict[str, Any]:
    return {"status": "deployed", "environment": "staging", "service": service, "commit": commit}


def mock_send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    return {"status": "sent", "recipient": to, "subject": subject}


def mock_send_client_email(client_id: str, subject: str, body: str) -> Dict[str, Any]:
    return {"status": "sent_to_client", "client_id": client_id, "subject": subject}

