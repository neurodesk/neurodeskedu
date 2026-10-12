# NeurodeskEDU - writing example notebooks

#### Table of Contents
**[Getting Started](#getting-started)**<br>
**[Design Principles](#design-principles)**<br>
**[Tips](#tips)**<br>

If you're planning to create a new example notebook, please follow these steps:

## Getting Started
1. **Access the Template**: Start by accessing the `template.ipynb` file. This is our standard template for creating new example notebooks which includes the standard metadata requirements, `watermark` for dependency tracking, and `module load` commands for neuroimaging software, and a table of contents example for structuring longer notebooks.
2. **Create a New Notebook**: Make sure your notebook runs as expected. An automatic GitHub Action will block the publication of your Example Notebook if it does not run entirely.
3. **Save and Submit**: Once you're done, save your notebook and submit it for review by creating a pull request on our GitHub repository.

## Design Principles

Our example notebooks follow best practices from [Rule et al. (2019) "Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks"](https://doi.org/10.1371/journal.pcbi.1007007). Below are the key principles adapted for the Neurodesk platform:

### 1. Tell a Story for Your Audience
- Interleave explanatory markdown with code and results to create an interactive tutorial
- Identify your target audience early (e.g., clinical researchers, students, those new to neuroimaging)
- Don't assume prior knowledge: over-explanation is better than under-explanation

### 2. Document Your Process and Reasoning
- Document not just what you did, but *why* you made specific choices
- Explain parameter selections and decision points in your analysis
- Include your reasoning and intuition alongside reproducible code

### 3. Use Clear Cell and Notebook Structure
- Keep each cell focused on one meaningful analysis step
- Avoid long cells (>100 lines of code)
- Use descriptive markdown headers to organize your notebook into clear sections
- Consider splitting very long analyses into a series of connected notebooks
- Use markdown to create a table of contents for longer notebooks
- For cells with lengthy output, add the `scroll-output` tag via Property Inspector to enable scrolling

### 4. Modularise Your Code
- Create reusable helper functions for repetitive tasks; this makes your notebook more modular and helps users adapt your code to their own data

### 5. Build a Reproducible Pipeline
- Declare key variables and parameters at the beginning of your notebook
- Perform all preparatory steps (like data cleaning) within the notebook—avoid manual interventions
- Before submitting, restart the kernel and run all cells to ensure full reproducibility

### 6. Use Open, Well-Documented Data
- Base your examples on openly available datasets and cite them at the beginning of your notebook with DOIs or permanent links (see template for format)
- Document all data preprocessing steps and explain any derived dataset transformations

### 7. Design for READ, RUN, and EXPLORE

**We provide for you:**
- Version control via GitHub with automated testing via GitHub Actions
- Zero-install testing environment via Neurodesk Play
- Template with `watermark` and `module load` for dependency management
- Static rendering on GitHub Pages

**When creating your notebook:**
- **READ**: Write clear explanations so users can understand your analysis without running it
- **RUN**: Your notebook executes completely from top to bottom without errors (GitHub Actions will verify this, but test locally first to save time)
- **EXPLORE**: Structure your code so users can easily modify parameters, use their own data, or extract specific sections for reuse

### 8. Advocate for Open, Reproducible Research
- Before submitting, ask a colleague to run your notebook and note any difficulties
- Consider how users might adapt your notebook for their own research questions
- Think of your notebook as both a tutorial and a template for others

## Tips

### Build the website locally

The website uses Jupyter Book 2 and the MyST book theme. Install Python 3.12
and Node.js 22, then run these commands from the repository root:

```bash
python -m venv .venv-book
source .venv-book/bin/activate
pip install -r requirements-book.txt
python .github/scripts/build_book.py --base-url ''
python .github/scripts/verify_book.py
python -m http.server --directory books/_build/html 8000
```

Open `http://localhost:8000`. The build reads saved notebook outputs and never
executes code cells. CI executes notebooks separately before it builds the site.

Edit `books/myst.yml` for theme options and `books/publishing.yml` for launch
servers, the deployment path, and redirects. The build discovers Markdown files
and notebooks automatically. Each content directory needs an `intro.md` landing
page. Generated configuration and page metadata stay in `books/_build/myst-source`.

CI passes a snapshot of the original sources through `--raw-books` so that
downloads exclude executed outputs and generated publication controls. Reviews
come from the registry refreshed before publication. DOI links come from
`doi-mapping.json`. Legacy `.html` links redirect to the new MyST page routes.

Run the migration tests from the repository root:

```bash
python -m unittest discover -s .github/scripts -p test_build_book.py
```

Set `BOOK_INTEGRATION_TEST=1` to include an actual engine build that checks saved
outputs without running notebook code.

For browser checks, install `requirements-book-browser.txt`, run
`playwright install chromium`, and serve the site as above. Then run
`python .github/scripts/verify_book_browser.py http://localhost:8000`.
This checks the launch menu, source download, page navigation, and the RISE
redirect. Add `--widgets` when the build contains the published brain extraction
notebook's five saved NiiVue viewers.

The build renders saved Jupyter widgets in separate HTML frames because MyST's
static renderer removes widget views. These frames use the Jupyter widget
runtime and retain the saved models and their dependencies. They need network
access to load the runtime and any hosted imaging data.
Source notebooks without saved widget state show their text fallback. CI uses
the executed artifacts that contain this state.

### GitHub Pages staging

Publication uses `build_book.py --with-preview` to keep the production `/edu`
bundle at the root of `gh-pages` and build a second, independent bundle for
`https://neurodesk.github.io/neurodeskedu/preview/`. Existing GitHub Pages entry
links (including `intro.html`) forward into this preview, preserving the page,
query string and fragment. The preview is marked `noindex`.

The production promotion workflow copies the `gh-pages` root into `/edu`, so its
root layout and production base must not change. The nested preview also gets
copied by that consumer; it has its own base and forwards to GitHub Pages when
opened under production. A single build with a changed base, or removing the
wrong-base redirect, would break links and assets on one of the two hosts.

Both builds use the same saved outputs and raw-source snapshot; neither executes
notebooks. A regular local build without `--with-preview` still emits one bundle.

### Publication reruns

CI runs notebooks containing local NiiVue files twice: once to produce results,
then again to render viewers using hosted URLs. Tag cells that create output
directories or perform expensive processing with `skip-on-publish` to run them
only on the first pass. Normal interactive Run All still executes these cells.
Keep variables needed by later cells and result-validation cells untagged, so
the publication pass can inspect the same results in a fresh kernel. CI stops
at the first cell error and only starts publication after a successful first pass.

### Managing Long Outputs

**For cells that produce long outputs** (e.g., extensive logs, large dataframes, verbose model training), add the `scroll-output` tag to make the output scrollable when rendered on GitHub Pages.

**How to add:**
1. Select the cell with long output
2. Open the Property Inspector (right or left sidebar, or View → Show Property Inspector)
3. Under "Common Tools" → "Cell Tags", add Tag: `scroll-output`

This prevents long outputs from dominating the page layout.
