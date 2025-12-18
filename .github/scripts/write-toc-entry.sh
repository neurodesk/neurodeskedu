#!/bin/bash

# Build a 3-tier TOC that is actually visible in the theme:
#   Examples -> (topic) -> (notebooks)
#   Tutorials -> (topic) -> (pages)
#   Contribute -> (guides)
#
# We intentionally generate top-level `chapters:` (not `parts:`) because the
# sidebar/theme commonly flattens/hides part labels.
#
# NOTE: Jupyter Book's external TOC schema requires every item under `chapters:` / `sections:`
# to contain one of: file/url/glob.

set -eo pipefail

# Function to capitalize the first letter of each word (snake_case -> Title Case)
capitalize() {
  echo "$1" | awk -F'_' '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))}1' OFS=' '
}

# Collect notebooks/markdown files, ignoring build/git artifacts and the root intro
readarray -t notebook_list < <(find . -type f \( -name "*.ipynb" -o -name "*.md" \) \
  ! -path "./_build/*" ! -path "./.git/*" | sed 's|^\./||' | sort)

declare -A section_entries   # key: "parent|||subfolder" -> list of section lines (4-space indent)
declare -A direct_entries    # key: parent -> list of direct section lines (6-space indent)
declare -A subfolders        # key: parent -> space-delimited subfolder list
declare -A subfolder_intro   # key: "parent|||subfolder" -> intro file path (no ext)
declare -A parent_intro      # key: parent -> intro file path (no ext)
declare -A parents_seen
parents=()

for file in "${notebook_list[@]}"; do
  # Skip the global intro; it is the book root
  [[ "$file" == "intro.md" ]] && continue

  # Require at least one slash so we know the parent folder
  [[ "$file" != */* ]] && continue

  parent=${file%%/*}
  rest=${file#*/}

  # Track parents in stable order of discovery
  if [[ -z "${parents_seen[$parent]}" ]]; then
    parents_seen[$parent]=1
    parents+=("$parent")
  fi

  # If there is no deeper subfolder, treat the file as a direct chapter under the part
  if [[ "$rest" != */* ]]; then
    file_no_ext="${file%.*}"
    if [[ "$rest" == "intro.md" ]]; then
      parent_intro[$parent]="$file_no_ext"
    else
      # direct pages under parent (rare); include them under the parent's intro page
      direct_entries[$parent]+="      - file: $file_no_ext\n"
    fi
    continue
  fi

  # Otherwise capture the subfolder and section entry
  subfolder=${rest%%/*}
  file_no_ext="${file%.*}"
  key="$parent|||$subfolder"

  # Skip subfolder intro pages from the nested section list (they are used as the parent item)
  if [[ "${rest}" == "${subfolder}/intro.md" ]]; then
    subfolder_intro[$key]="${parent}/${subfolder}/intro"
    continue
  fi

  # Track unique subfolders per parent
  if [[ " ${subfolders[$parent]} " != *" ${subfolder} "* ]]; then
    subfolders[$parent]+=" ${subfolder}"
  fi

  section_entries[$key]+="          - file: $file_no_ext\n"
done

# Write the TOC
{
  echo "format: jb-book"
  echo "root: intro"
  echo "chapters:"

  # Explicit order to match desired UX
  ordered_parents=(examples tutorials contribute)

  # Append any other parents (alphabetical), just in case
  extras=$(printf "%s\n" "${parents[@]}" | sort)
  for p in $extras; do
    case "$p" in
      examples|tutorials|contribute) ;;
      *) ordered_parents+=("$p") ;;
    esac
  done

  for parent in "${ordered_parents[@]}"; do
    [[ -z "${parents_seen[$parent]:-}" ]] && continue

    parent_intro_no_ext="${parent_intro[$parent]:-${parent}/intro}"
    if [[ ! -f "${parent_intro_no_ext}.md" ]]; then
      echo "ERROR: Missing required parent intro page: ${parent_intro_no_ext}.md" >&2
      echo "Create it (minimal is fine) so the TOC can show a visible top-level entry." >&2
      exit 1
    fi

    echo "  - file: ${parent_intro_no_ext}"
    echo "    sections:"

    # Parent direct pages (if any)
    if [[ -n "${direct_entries[$parent]:-}" ]]; then
      echo -e "${direct_entries[$parent]}"
    fi

    # Subfolder intro -> sections under it
    read -ra subs <<< "${subfolders[$parent]:-}"
    if (( ${#subs[@]} )); then
      for subfolder in $(printf "%s\n" "${subs[@]}" | sort); do
        key="$parent|||$subfolder"
        intro_no_ext="${subfolder_intro[$key]:-${parent}/${subfolder}/intro}"
        if [[ ! -f "${intro_no_ext}.md" ]]; then
          echo "ERROR: Missing required subfolder intro page: ${intro_no_ext}.md" >&2
          echo "Create it (minimal is fine) so the TOC can reference a real file." >&2
          exit 1
        fi

        echo "      - file: ${intro_no_ext}"
        echo "        sections:"
        if [[ -n "${section_entries[$key]:-}" ]]; then
          echo -e "${section_entries[$key]}"
        fi
      done
    fi
  done
} > _toc.yml