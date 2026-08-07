# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper to package and register skills with the GCP Agent Registry."""

import base64
import io
import os
import sys
import zipfile
import google.auth
from google.auth.transport.requests import Request
import httpx
import yaml


def zip_dir(dir_path: str) -> bytes:
    """Zips the contents of a directory into memory.

    Args:
        dir_path: Path to the local directory.

    Returns:
        Zipped bytes of the directory contents.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Compute relative path to store in zip
                arcname = os.path.relpath(file_path, dir_path)
                zip_file.write(file_path, arcname)
    return zip_buffer.getvalue()


def register_skill(
    skill_dir: str,
    project_id: str,
    location: str,
    skill_id: str,
) -> dict:
    """Zips and uploads a skill directory to the GCP Agent Registry.

    Args:
        skill_dir: Local path to the skill directory containing SKILL.md.
        project_id: GCP Project ID.
        location: GCP location (e.g. us-central1, eu).
        skill_id: Unique ID for the skill to register.

    Returns:
        The response dictionary from the CreateSkill API call.

    Raises:
        ValueError: If the skill_dir is invalid.
        RuntimeError: If authentication or the API request fails.
    """
    if not os.path.isdir(skill_dir):
        raise ValueError(f"'{skill_dir}' is not a valid directory.")

    # 1. Zip local folder contents
    zip_bytes = zip_dir(skill_dir)
    zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")

    # 2. Extract metadata from SKILL.md frontmatter if available
    display_name = skill_id
    description = f"Skill for {skill_id}"

    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(skill_md_path):
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                parts = content.split("---")
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        display_name = frontmatter.get("name", display_name)
                        description = frontmatter.get(
                            "description", description
                        )
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass

    # 3. Authenticate with Google Cloud
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not credentials.valid:
        credentials.refresh(Request())

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "x-goog-user-project": project_id,
    }

    url = (
        f"https://agentregistry.googleapis.com/v1alpha/"
        f"projects/{project_id}/locations/{location}/skills"
    )
    params = {"skillId": skill_id}

    body = {
        "displayName": display_name,
        "description": description,
        "type": "SIMPLE",
        "targetState": "TARGET_STATE_DRAFT",
        "initialRevision": {
            "archiveUploadSource": {
                "archiveContent": zip_b64
            }
        }
    }

    # 4. Make request to CreateSkill API
    response = httpx.post(
        url, headers=headers, params=params, json=body, timeout=60.0
    )

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 409:
        # Skill already exists, upload as a new revision instead.
        # Manual uploads get prefixed with 'private-' by the server.
        full_skill_id = f"private-{skill_id}"
        revision_url = f"{url}/{full_skill_id}/revisions"
        revision_body = {
            "archiveUploadSource": {
                "archiveContent": zip_b64
            }
        }

        print(f"Skill '{skill_id}' already exists. Uploading new revision...")
        rev_response = httpx.post(
            revision_url, headers=headers, json=revision_body, timeout=60.0
        )
        if rev_response.status_code == 200:
            return rev_response.json()
        else:
            raise RuntimeError(
                f"Failed to upload revision for existing skill '{skill_id}': "
                f"{rev_response.status_code} - {rev_response.text}"
            )
    else:
        raise RuntimeError(
            f"Failed to register skill: {response.status_code} - {response.text}"
        )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python -m app.helpers.register_skill "
            "<project_id> <location> [<skill_dir> <skill_id>]"
        )
        print(
            "If <skill_dir> and <skill_id> are omitted, all skills in "
            "'../sysman-common/skills/' will be registered."
        )
        sys.exit(1)

    project_id_arg = sys.argv[1]
    location_arg = sys.argv[2]

    if len(sys.argv) >= 5:
        # Register a single skill
        skill_dir_arg = sys.argv[3]
        skill_id_arg = sys.argv[4]
        try:
            res_dict = register_skill(
                project_id=project_id_arg,
                location=location_arg,
                skill_dir=skill_dir_arg,
                skill_id=skill_id_arg,
            )
            print(f"Successfully registered: {res_dict.get('name')}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Register all skills in sysman-common/skills
        default_skills_dir = "../sysman-common/skills"
        if not os.path.isdir(default_skills_dir):
            print(f"Error: Default skills directory '{default_skills_dir}' not found.")
            sys.exit(1)

        print(f"Scanning for skills in '{default_skills_dir}'...")
        success_count = 0
        failure_count = 0
        for entry in os.scandir(default_skills_dir):
            if entry.is_dir():
                skill_id_arg = entry.name
                skill_path = entry.path
                try:
                    res_dict = register_skill(
                        project_id=project_id_arg,
                        location=location_arg,
                        skill_dir=skill_path,
                        skill_id=skill_id_arg,
                    )
                    print(f"Successfully registered '{skill_id_arg}': {res_dict.get('name')}")
                    success_count += 1
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Failed to register skill '{skill_id_arg}': {e}")
                    failure_count += 1

        print(f"\nScan finished. Success: {success_count}, Failure: {failure_count}")
        if failure_count > 0:
            sys.exit(1)
