# Statement on the Use of AI Tools in the `jakadac` Ada Compiler Project

**Date:** April 20, 2025

**Author:** John Akujobi

## Introduction

This document outlines the use of Artificial Intelligence (AI) tools during the development of the `jakadac` Ada compiler project for CSC 446 - Compiler Construction. The purpose of this statement is to provide transparency regarding how these tools were employed as aids in the development process while affirming that the core intellectual work adheres strictly to academic integrity policies.

## Core Principle: AI as an Augmentative Tool

AI tools were utilized selectively as assistants to enhance productivity, learning, and code quality. They were **NOT** used to generate complete solutions, bypass fundamental learning objectives, or substitute for the core problem-solving, design, and implementation efforts required by the assignments. The final project represents my own understanding, design choices, and coding efforts.

## Specific AI Tool Usage

The following AI tools were consulted or used for specific, limited tasks:

* **Concept Exploration and Learning:**
  * **Perplexity AI:** Used for searching and retrieving information regarding specific compiler construction concepts or algorithms encountered during the project.
  * **ChatGPT (Advanced Voice Mode):** Engaged conversationally to discuss and deepen understanding of complex theoretical concepts related to compilers, acting as a virtual tutor.
  * **NotebookLM:** Utilized to review and query personal notes taken during class lectures and study sessions.
* **Code Review and Refinement:**
  * **Google Assistant / GitHub Copilot Review:** Employed after making pull requests to perform code reviews on self-written code, identifying potential areas for improvement, suggesting alternative implementations, or pointing out possible bugs based on patterns. The suggestions were critically evaluated before any adoption.
* **Code Assistance and Generation (Limited Scope):**
  * **DeepCoder (Run Locally):** Used occasionally to generate small, utility code snippets (e.g., specific helper functions or methods) based on clear specifications provided by me. Also used to assist in generating routine comments and docstrings for self-written code.
  * **Cody AI:** Utilized to generate examples of test data structures or inputs based on defined requirements, helping to create comprehensive test cases.
* **Documentation:**
  * AI assistance was used moderately to help draft or refine sections of project documentation, primarily for clarity and formatting.

## Developer Contribution and Academic Integrity

While the tools above provided assistance in specific areas, the following core aspects of the project were solely my own work:

* **Overall Program Design and Architecture:** The high-level structure, modularization choices, and data flow were designed and planned by me.
* **Problem-Solving and Algorithm Implementation:** The core logic for the lexical analyzer, parser (including grammar interpretation and implementation), semantic analyzer (including symbol table logic and type checking rules), and overall compiler pipeline was developed through my own problem-solving efforts based on course materials and concepts.
* **Debugging:** Identifying and resolving logical errors, runtime issues, and algorithmic flaws was primarily my own undertaking, though AI tools occasionally helped identify syntax errors or suggest debugging approaches.
* **Majority of Code Implementation:** The substantial majority of the functional code across all modules was written and implemented by me. AI-generated snippets were limited to small, well-defined utility functions and were integrated and adapted as needed.

---



## Example Workflow

### Planning

- I gather all information together and breakdown the requirements.

  - This includes notes, assignment information
- I make a requirments plan
- I design an architecture and design plan which contains:

  - the classes needed, their modules
  - methods in the classes
  - How the data flows and program works

### Implementation

- Make the files needed and make the structures
- I write the functions as  pseudocode first
- Convert some of the pseudocode to python code manually
- Review plan with local model to see what issues there might be and get an outside perspective
- I make changes to to plan, architecture and pseudocode if needed
- Translate snippets and small functions from pseudocode to syntactically correct code with help from locally run model

### Testing

- I design test cases to test the classes and modules
- Add or improve testcases with the help of locally run model
- Test the program as i write the code.

### Debugging

Throughout my program, i place log statements using a logger module i created. An instance of it is shared accross modules.

Logs are printed to the terminal and to a file (more verbose). When there are issues:

- I read the logs from the terminal
- Look through the modules related and do a manual walkthrough
  - Because of the assistance, errors are very rarely syntactic, so I get to focus on the problem solving, and troubleshooting logical errors
- Make manual fixes, run tests and repeat.

If fixing fails after several multiple attempts.

- Use the python debugger in VsCode to track the execution
- If there is a unique problem, search online using Perplexity
- If the problem is fundamental, make a new branch from a last stable commit and work on it

Assistance from model

- I explain the issue i am having.
  - Sometimes, i use voice to text while talking with a 3D printed Rabbit on my desk
- I explain the steps i took to fix it.
- Add the log file as context of what happened
- Ask it to provide suggestions, but not to solve it outright
  - Ask it to provide multiple different perspectives separate from the one i have
- Look for potential issues with the program

All through this, i commit, test and retry the program


## Other tools

The other tools i used were:

- VS Code: IDE
- Edge browser: Web browsing and accessing D2L
- Git: Source control
- GitHub: Hosting code
- Obsidian: Writing notes in latex and markdown
- LM Studio: Running local models
- NotebookLM: For studying with my notes

Operating Systems

- Windows 11: Mobile workstation
- Linux Mint: Home workstation

Extensions:

- autoDocstring: auto documenting python
- Better Comments: Adding todos
- Blockman
- Code Runner
- Code Spell Checker
- Error Lens
- GitHub Pull Request
- GitLen
- Hide Comments
- indent-rainbow
- IntelliCode
- LanguageTool
- Martkdiwn All in One
- Markown Collapsible headers
- Markdown Preview
- markdownlint
- Office Viewer
- Output Colorizer
- Path intllisense
- Prettier
- Pylance
- Python
- Pthon DebuggerPython Envy
- Python Indent
- Python Preview
- Spacetime
- Toggle Bracket Guides
- VS Code Counter

## Conclusion

The use of AI in this project was intended to mirror modern software development practices where AI tools assist developers, without compromising the academic integrity or the learning objectives of the course. All work submitted reflects my own understanding and effort in designing and building the `jakadac` compiler.
