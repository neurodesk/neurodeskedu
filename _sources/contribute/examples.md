---
title: "Contribute Example Notebooks"
linkTitle: "Contribute examples"
weight: 1
aliases:
  - /tutorials/tutorial-template
  - /tutorials-examples/contribute/contribute-examples
description: >
  A brief guide for contributing new example notebooks.
---

We welcome example notebooks that demonstrate how to use tools within Neurodesk. These notebooks serve as valuable learning resources and promote reproducible workflows across the neuroimaging community.

Example notebooks are hosted in the <a href="https://github.com/neurodesk/neurodeskedu/tree/main/books/examples" target="_blank" rel="noopener">
  `neurodesk/neurodeskedu:examples`
</a> repository and are intended to be lightweight, self-contained, and easy to follow.

---
# Contribute Example Notebooks

## Getting Started

To contribute a new notebook, follow the steps below:

### 1. Start from the template

Use the official <a href="https://github.com/neurodesk/neurodeskedu/tree/main/books/examples/template.ipynb" target="_blank" rel="noopener">
  example notebook template
</a> as a starting point. It includes guidance on formatting, structure, metadata, and citation instructions.

Each notebook should contain:

- A clear title and short description - aim for a short title that will fit in the left menu
- An overview of the tool or workflow demonstrated 
- The container/tool version used
- Code cells with explanatory comments
- Example data (or guidance on how to access it)

**Python packages** please consult the python packages included in the base image <a href="https://github.com/neurodesk/neurodesktop/blob/main/Dockerfile" target="_blank" rel="noopener">
  see list here
</a>. If you are using python packages different than these, be sure to `pip install` them in the workflow

### 2. Follow best practices

- Keep notebooks self-contained and executable top to bottom. Before being published, a Github Action will confirm the Notebook is working.
- Avoid hardcoded file paths where possible
- Use publicly accessible datasets
- Include inline comments and Markdown cells for explanation

For more detail, consult the <a href="https://github.com/neurodesk/neurodeskedu/blob/main/README.md" target="_blank" rel="noopener">
  README in the neurodeskedu repository
</a>.


---

## Saving and Submitting

1. Add your completed notebook to the appropriate folder under:

   <a href="https://github.com/neurodesk/neurodeskedu/tree/main/books/examples" target="_blank" rel="noopener">
  `/books/examples/`
</a>

2. Open a pull request in the <a href="https://github.com/neurodesk/neurodeskedu" target="_blank" rel="noopener">
  neurodeskedu repository
</a>

3. In your pull request, include:
   - A short description of your notebook
   - Any dependencies or expected output

---

## Attribution

All notebooks contributors are acknowledged on the <a href="https://neurodesk.org/developers/contributors/" target="_blank" rel="noopener">
  Contributors page
</a>.  
To be listed, include your name and a short description in your pull request using <a href="https://github.com/neurodesk/neurodesk.github.io/blob/main/.github/content-templates/contributor-format.md" target="_blank" rel="noopener">
  this format
</a>.

---

## Need Help?

If you have questions or would like feedback before submitting:

- Open a [discussion](https://github.com/orgs/neurodesk/discussions)

We look forward to your contributions and thank you for supporting open and reproducible neuroimaging.
