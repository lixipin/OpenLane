#!/usr/bin/env python3
# Copyright 2020 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os 
import subprocess
import collections
import re

# private
def d2nt(dictionary):
    return collections.namedtuple('metadata', dictionary.keys())(**dictionary)

def export_env(key, value):
    with open(os.getenv("GITHUB_ENV"), "a") as f:
        f.write("%s=%s\n" % (key, value))

class Repo(object):
    def __init__(self, name, url, branch_rx=None, extraction_rx=None):
        print("[Repo Object] Initializing repo %s with URL %s…" % (name, url))
        self.name = name
        self.url = url
        self.commit = None
        self.branch_rx = branch_rx
        self.extraction_rx = extraction_rx

        self._latest_commit = None
        self._branches = None
        self._tags = None

    @property
    def latest_commit(self):
        if self._latest_commit is None:
            print("[Repo Object] Fetching latest commit for %s…" % self.name)
            p = subprocess.check_output([
                "git",
                "ls-remote",
                self.url
            ]).decode("utf8")
            for line in p.split("\n"):
                if "HEAD" in line:
                    self._latest_commit = line[:40]
        return self._latest_commit

    @property
    def branches(self):
        if self._branches is None:
            print("[Repo Object] Fetching branches for %s…" % self.name)
            p = subprocess.check_output([
                "git", "ls-remote", "--heads", self.url
            ]).decode("utf8")
            branches = []
            for line in p.split("\n"):
                if line.strip() == "":
                    continue

                match = line.split()

                hash = match[0]
                name = match[1]
                
                branches.append((hash, name))
            self._branches = branches
        return self._branches

    @property
    def tags(self):
        if self._tags is None:
            print("[Repo Object] Fetching tags for %s…" % self.name)
            p = subprocess.check_output([
                "git", "ls-remote", "--tags", "--sort=v:refname",
                self.url
            ]).decode("utf8")

            tags = []
            for line in p.split("\n"):
                if line.strip() == "":
                    continue

                match = line.split()

                hash = match[0]
                name = match[1].split("/")[2]
                
                tags.append((hash, name))
            self._tags = tags
        return self._tags

    # Helper Functions
    def match_branch(self, line):
        match = re.match(self.branch_rx, line)
        if match is not None:
            return match[1]

    def match_line(self, line):
        match = re.match(self.extraction_rx, line)
        if match is not None:
            return match[1]

    def out_of_date(self):
        return self.commit != self.latest_commit

origin = os.getenv("REPO_URL")
repo = Repo("Openlane", origin)

# public
gh = d2nt({
    "origin": origin,
    "branch": os.getenv("BRANCH_NAME"),
    "image": os.getenv("IMAGE_NAME"),
    "root": os.getenv("GITHUB_WORKSPACE"),
    "pdk": os.getenv("PDK_ROOT"),
    "tool": os.getenv("TOOL"),
    "event": d2nt({
        "name": os.getenv("GITHUB_EVENT_NAME")
    }),
    "export_env": export_env,
    "Repo": Repo,
    "openlane": repo
})