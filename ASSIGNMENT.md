CSE 4095 — Agentic Programming
Programming Assignment: Build and Deploy a Web-Based Hangman Game
Assignment Type: Individual

Duration: One week

Total Points: 100

Development Tools: Cursor or another AI coding agent, Python, Flask, HTML, CSS, JavaScript, GitHub, and Render

1. Overview
In this assignment, you will use an AI coding agent to develop and deploy a web-based Hangman game.

You will be provided with three reference materials:

SPECIFICATION.md — The original software specification for the Hangman project.
TODO.md — The original phased implementation plan.
Instructor's Cursor Transcript — A record of how the instructor used Cursor to implement and deploy the Hangman application.
Your task is to use these materials to guide the development of your own Hangman web application.

The original specification describes a larger system with several types of clients and automated bot functionality. For this assignment, you only need to implement the Hangman server and browser-based client.

You do not need to implement a terminal client, automated Hangman bots, bot evaluation, or a leaderboard.

You may explore the instructor's deployed application as a reference:

https://hangman-ex89.onrender.com/

However, you must develop and deploy your own implementation.

2. Learning Objectives
By completing this assignment, you should be able to:

Use a software specification to guide AI-assisted software development.
Adapt an existing implementation plan to a reduced project scope.
Use Cursor or another AI coding agent to implement a multi-component application.
Understand client-server architecture.
Develop a Flask server that exposes REST API endpoints.
Use HTML, CSS, and JavaScript to build an interactive browser interface.
Understand how HTTP requests and JSON responses connect the frontend and backend.
Test and debug an AI-generated application.
Deploy a complete web application to a cloud hosting platform.
3. Project Requirements
Your application must include the following components.

A. Hangman Game Engine
Implement the Hangman game logic in Python.

The game engine must support:

Random word selection.
Easy, Medium, and Hard difficulty levels.
Validating letter guesses.
Tracking correct and incorrect guesses.
Displaying the current word pattern.
Tracking remaining incorrect guesses.
Detecting wins and losses.
Preventing further guesses after a game ends.
The game engine should be independent of the browser interface.

B. Flask Server and REST API
Implement a Flask server that manages games and provides a REST API.

At minimum, implement these endpoints:

   Method

 Endpoint

 Purpose

   POST

 /api/games

 Create a new Hangman game

   GET

 /api/games/{game_id}

 Retrieve the current game state

   POST

 /api/games/{game_id}/guess

 Submit a letter guess

   Your server must:

Accept and return JSON.
Generate unique game identifiers.
Maintain separate game states.
Validate incoming requests.
Return appropriate HTTP status codes.
Keep the hidden word on the server during active gameplay.
The browser must communicate with the Flask server through the REST API.

C. Web-Based Client
Implement an interactive browser interface using HTML, CSS, and JavaScript.

Your interface must allow users to:

Select Easy, Medium, or Hard difficulty.
Start a new Hangman game.
Guess letters by clicking buttons or using the keyboard.
See the current word pattern.
See previously guessed letters.
See the number of remaining incorrect guesses.
See a Hangman drawing that changes as incorrect guesses accumulate.
See a message when the game is won or lost.
Start another game without reloading the application.
The web interface should communicate with Flask using JavaScript fetch() or an equivalent mechanism.

You may use SVG, HTML elements, or another suitable approach to draw the Hangman figure.

Important: The browser must not implement its own independent game engine or contain the hidden word during active gameplay. The Flask server is responsible for determining the results of guesses.

D. Testing
Test both the game engine and the web application.

At minimum, verify:

Starting games at all three difficulty levels.
Making correct and incorrect guesses.
Repeated or invalid guesses.
Winning and losing games.
Starting a new game after completing one.
Handling invalid API requests.
Ensuring the hidden word is not exposed during active gameplay.
Updating the browser correctly after each guess.
You may use AI-generated automated tests, manual browser testing, or both. Automated tests for the game engine and API are strongly encouraged.

E. Cloud Deployment
Deploy your application to Render or another suitable cloud hosting platform.

Your deployed application must:

Be accessible through a public HTTPS URL.
Display the Hangman web interface.
Support the required REST API endpoints.
Allow a user to play a complete game through the browser.
Work without requiring the user to install Python or run a local server.
4. Development Instructions
Step 1 — Review the Provided Materials
Read SPECIFICATION.md, TODO.md, and the instructor's Cursor transcript.

Identify which features are required for this assignment and which are outside its scope.

Use Cursor to revise the original TODO file so it focuses on:

Game engine and word management.
Flask server and REST API.
Browser-based client.
Testing and debugging.
Cloud deployment.
You should remove or mark as out of scope the tasks related to terminal clients, automated bots, evaluation, and leaderboards.

Step 2 — Initialize the Project
Create a project directory and GitHub repository.

Open the project in Cursor and provide the specification and TODO file.

Suggested initial prompt:

Read SPECIFICATION.md and TODO.md carefully. I need to build and deploy a web-based Hangman game with a Flask backend and an HTML/CSS/JavaScript frontend. Terminal clients, automated bots, evaluation, and leaderboards are outside the scope of this assignment. Revise TODO.md into a phased implementation plan for the required features. Do not implement code yet.

Review the revised plan before proceeding.

Step 3 — Implement the Application Incrementally
Work through the revised TODO file one phase at a time.

Suggested prompt:

Implement the next incomplete phase in TODO.md according to SPECIFICATION.md and the reduced assignment scope. Run relevant tests, explain the changes, and update TODO.md only after verifying the implementation.

After each phase:

Review the generated code.
Run the application or relevant tests.
Identify and resolve errors.
Update TODO.md.
Commit your changes to GitHub.
You should not ask the AI agent to implement the entire application in a single prompt.

Step 4 — Test the Application Locally
Run the Flask application on your computer.

Open the web interface in a browser and play several games.

Use Chrome Developer Tools to inspect at least one REST API request.

Verify that:

JavaScript sends an HTTP request when a user guesses a letter.
Flask processes the request.
The server returns JSON containing the updated game state.
JavaScript updates the webpage using the response.
You should be able to explain this sequence.

Step 5 — Deploy the Application
Push your project to GitHub.

Deploy the application to Render or another suitable cloud hosting service.

If using Gunicorn, an example startup command is:

gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app
Adjust the command to match your project structure.

After deployment, open the public URL and play a complete game.

Verify that the deployed application works independently of your local development environment.

5. Suggested One-Week Schedule
   Day

 Recommended Work

   Day 1

 Review materials, revise TODO, create repository

   Day 2

 Implement game engine and word management

   Day 3

 Implement Flask server and REST API

   Day 4

 Implement web interface

   Day 5

 Test and debug the complete application

   Day 6

 Deploy to Render and verify functionality

   Day 7

 Prepare submission and final demonstration

   6. Submission Requirements
Submit the following through HuskyCT.

A. GitHub Repository URL

Your repository should contain:

Python game engine and Flask server.
HTML, CSS, and JavaScript frontend.
Word lists and other required resources.
Original specification.
Updated TODO file.
Dependency and deployment configuration.
Tests, if developed.
README with instructions for running the application locally.
B. Deployed Application URL

Provide the public URL of your Hangman web application.

The application must remain accessible during grading.

C. Short Development Report (1–2 Pages)

Submit a PDF report covering:

Development process: How you used Cursor or another AI coding agent.
Implementation: Briefly describe the game engine, Flask server, REST API, and browser interface.
Testing: Describe how you verified the application.
Deployment: Explain how you deployed the application.
Challenges: Describe at least one problem and how you resolved it.
Reflection: What did you learn about AI-assisted development?
Include two or three representative prompts from your interactions with the coding agent.

D. Demonstration

Submit a short screen recording (approximately 2–3 minutes) showing:

Your deployed Hangman webpage.
Starting a game and guessing letters.
A complete game ending in a win or loss.
Starting a new game.
At least one HTTP request and JSON response in Chrome Developer Tools.
7. Grading Rubric
   Component

 Points

   Hangman game engine and correctness

 20

   Flask server and REST API

 20

   Web interface and usability

 20

   Testing and reliability

 15

   Cloud deployment

 15

   Agentic development process and report

 10

   Total

 100

   8. Important Guidelines
This is an individual assignment.
You may use AI coding agents extensively.
You are responsible for verifying the correctness of AI-generated code.
You may refer to the instructor's Cursor transcript, but you should develop your own implementation and prompts.
Do not copy the instructor's completed source code.
You are not required to implement a terminal client, automated bots, bot evaluation, or leaderboard functionality.
You must be able to explain how your application works.
Do not commit credentials or other secrets to GitHub.
Clearly document any incomplete functionality or known limitations.
9. Expected Outcome
By the end of the assignment, you should have a fully functioning, publicly accessible Hangman web application.

More importantly, you should understand how to guide an AI coding agent through a complete development process, from software specification and implementation planning to testing and cloud deployment.