# CS 131 Spring 2023: Project Starter

Hey there! This is a template repository that contains the necessary boilerplate for [CS 131](https://ucla-cs-131.github.io/spring-23/)'s quarter-long project: making an interpreter. The project specs are as follows:

1. [Project 1 Spec](https://docs.google.com/document/d/1pPQ2qZKbbsbZGBSwvuy1Ir-NZLPMgVt95WPQuI5aPho)

There are three stages to the project; students are currently at the first. Thus, this folder contains the necessary bootstrapping code:

- `intbase.py`, the base class and enum definitions for the interpreter
- `bparser.py`, a static `parser` class to parse Brewin programs

Some notes on your submission (for Project 1)

1. You **must have a top-level, versioned `interpreterv1.py` file** that **exports the `Interpreter` class**. If not, **your code will not run on our autograder**.
2. You may also submit one or more additional `.py` modules that your interpreter uses, if you decide to break up your solution into multiple `.py` files.
3. You **should not modify/submit `intbase.py` or `bparser.py`**; we will use our own when grading.

You can find out more about our autograder, including how to run it, in [its accompanying repo](https://github.com/UCLA-CS-131/spring-23-autograder).

## Licensing and Attribution

This is an unlicensed repository; even though the source code is public, it is **not** governed by an open-source license.

This code was primarily written by [Carey Nachenberg](http://careynachenberg.weebly.com/), with support from his TAs for the [Spring 2023 iteration of CS 131](https://ucla-cs-131.github.io/spring-23/).
# CS 131 Spring 2023 - Project Autograder

Hi there! This is a repo that contains an open-source subset of the autograder we'll be using for [CS 131 - Spring 2023](https://ucla-cs-131.github.io/spring-23/)'s course-long project: making an interpreter.

Using this repository / testing locally is **entirely optional**. It does not directly affect your grade. **You are free to only submit to Gradescope!**

This repository contains:

- the **full source code** for the autograder we deploy to Gradescope
- 10% of the test cases we evaluate your code on; these are the test cases that are public on Gradescope
    - each version of the project is in a `v*` folder;
    - the `tests` subdirectory contains source (`.brewin`), expected (`.exp`), and standard input (`.in`) files for programs that should interpret and run without errors
    - the `fails` subdirectory contains source (`.brewin`), expected (`.exp`), and standard input (`.in`) files for programs that should interpret successfully, but error

This repository does not contain:

- 90% of the test cases we evaluate your code on (until *after* the project is due)
- the plagiarism checker, which is closed-source
- the Docker configuration for the deployment; this is managed by Gradescope.
- canonical solutions for the past projects - those are in the [project template repo](https://github.com/UCLA-CS-131/spring-23-project-starter)

We'll note that with the current setup, we grant **five seconds for each test case to run**.

We've made a [separate repository for project template code](https://github.com/UCLA-CS-131/spring-23-project-starter).

## Usage

### Setup

This grader uses features of Python 3.11. So, **you must be running Python 3.11 locally**.

Next, clone this repository and make it your working directory:

```sh
$ git clone
# or, with SSH
$ git clone git@github.com:UCLA-CS-131/spring-23-autograder.git
...
cd spring-23-autograder
```

Now, you're ready to test locally.

### Testing Locally

To test locally, you will additionally need a **working implementation** of the project; the minimum example is an `interpreterv1.py`/`interpreterv2.py`/`interpreterv3.py` that implements the `Interpreter` class.

Place this in the same directory as `tester.py`. Then, to test project 1,

```sh
$ python3 tester.py 1
Running 5 tests...
Running v1/tests/test_inputi.brewin...  PASSED
Running v1/tests/test_recursion1.brewin...  PASSED
Running v1/tests/test_set_field.brewin...  PASSED
Running v1/fails/test_if.brewin...  PASSED
Running v1/fails/test_incompat_operands1.brewin...  PASSED
5/5 tests passed.
Total Score:    100.00%
```

The output of this command is **identical to what is visible on Gradescope pre-due date**, and they are the same cases that display on every submission. If there is a discrepancy, please let the teaching team know!

Note: we also output the results of the terminal output to `results.json`.

## Bug Bounty

If you're a student and you've found a bug - please let the TAs know (confidentially)! If you're able to provide a minimum-reproducible example, we'll buy you a coffee - if not more!

## Licensing and Attribution

This code is distributed under the [MIT License](https://github.com/UCLA-CS-131/spring-23-autograder/blob/main/LICENSE).

Have you used this code? We'd love to hear from you! [Submit an issue](https://github.com/UCLA-CS-131/spring-23-autograder/issues) or send us an email ([matt@matthewwang.me](mailto:matt@matthewwang.me)).
