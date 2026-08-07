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

"""Helper to set registered skills to ACTIVE state in GCP Agent Registry."""

import os
import sys
import google.auth
from google.auth.transport.requests import Request
import httpx


def activate_skill(
    project_id: str,
    location: str,
    skill_id: str,
) -> bool:
    """Sets a skill's targetState to ACTIVE and configures its defaultRevision.

    Args:
        project_id: GCP Project ID.
        location: GCP location.
        skill_id: The resource ID of the skill (without 'private-' prefix).

    Returns:
        True if activation succeeded, False otherwise.

    Raises:
        RuntimeError: If authentication or API calls fail.
    """
    # Prepend 'private-' because manual uploads are prefixed by the backend
    full_skill_id = f"private-{skill_id}"

    # Get credentials
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

    # 1. Fetch revisions to find the active compiled revision
    rev_url = (
        f"https://agentregistry.googleapis.com/v1alpha/"
        f"projects/{project_id}/locations/{location}/skills/{full_skill_id}/revisions"
    )
    rev_res = httpx.get(rev_url, headers=headers, timeout=30.0)

    if rev_res.status_code != 200:
        raise RuntimeError(
            f"Failed to query revisions for {full_skill_id}: "
            f"{rev_res.status_code} - {rev_res.text}"
        )

    revisions = rev_res.json().get("skillRevisions", [])
    active_rev = None
    for rev in revisions:
        if rev.get("state") == "ACTIVE":
            active_rev = rev.get("name")
            break

    if not active_rev:
        print(f"Warning: Skill {full_skill_id} has no active revisions compiled yet.")
        return False

    # 2. Patch skill to set defaultRevision and targetState = TARGET_STATE_ACTIVE
    patch_url = (
        f"https://agentregistry.googleapis.com/v1alpha/"
        f"projects/{project_id}/locations/{location}/skills/{full_skill_id}"
    )
    params = {"updateMask": "defaultRevision,targetState"}
    body = {
        "defaultRevision": active_rev,
        "targetState": "TARGET_STATE_ACTIVE",
    }

    patch_res = httpx.patch(
        patch_url, headers=headers, params=params, json=body, timeout=30.0
    )

    if patch_res.status_code == 200:
        print(
            f"Successfully activated {full_skill_id} "
            f"pointing to revision '{active_rev.split('/')[-1]}'"
        )
        return True
    else:
        raise RuntimeError(
            f"Failed to activate skill {full_skill_id}: "
            f"{patch_res.status_code} - {patch_res.text}"
        )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python -m app.helpers.activate_skills "
            "<project_id> <location> [<skill_id>]"
        )
        print(
            "If <skill_id> is omitted, all skills in '../sysman-common/skills/' "
            "will be activated."
        )
        sys.exit(1)

    project_id_arg = sys.argv[1]
    location_arg = sys.argv[2]

    if len(sys.argv) >= 4:
        skill_id_arg = sys.argv[3]
        try:
            activate_skill(project_id_arg, location_arg, skill_id_arg)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Scan and activate all skills in sysman-common/skills
        default_skills_dir = "../sysman-common/skills"
        if not os.path.isdir(default_skills_dir):
            print(f"Error: Default skills directory '{default_skills_dir}' not found.")
            sys.exit(1)

        print(f"Scanning for skills to activate in '{default_skills_dir}'...")
        success_count = 0
        failure_count = 0
        for entry in os.scandir(default_skills_dir):
            if entry.is_dir():
                skill_id_arg = entry.name
                try:
                    if activate_skill(project_id_arg, location_arg, skill_id_arg):
                        success_count += 1
                    else:
                        failure_count += 1
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Failed to activate '{skill_id_arg}': {e}")
                    failure_count += 1

        print(
            f"\nActivation finished. Success: {success_count}, Failure: {failure_count}"
        )
        if failure_count > 0:
            sys.exit(1)
