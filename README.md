# AgenticAIBot — Technical Overview

## Objective
Transform natural language instructions into automated browser interactions using Selenium, powered by Google Gemini’s generative language API.

## Architecture & Features

- **Generative AI Integration**  
  Utilizes Google Gemini API to convert user prompts into executable Selenium command scripts.

- **Browser Automation Layer**  
  Employs Selenium WebDriver with ChromeDriver and applies anti-detection techniques (e.g., user-agent spoofing, webdriver masking).

- **Command Parsing & Execution**  
  Supports a simple DSL with commands:  
  - `OPEN("url")` — navigate to a URL  
  - `TYPE("selector", "text")` — input text into a DOM element  
  - `CLICK("selector")` — click on an element  
  - `WAIT(seconds)` — pause execution for given seconds

- **Reliability & Logging**  
  Implements robust error handling, exponential backoff retry on API calls, detailed logging to file and console.

- **Persistence & Traceability**  
  Saves prompt-response pairs with timestamps in JSON format for audit trails and debugging.

- **Configuration Management**  
  Loads API keys and runtime parameters from `config.json`, with sensible defaults for fallback.

## Execution Flow

1. User inputs high-level natural language instruction.  
2. Instruction is wrapped into a prompt and sent to Google Gemini API.  
3. Received Selenium command script is parsed and executed step-by-step in Chrome browser.  
4. All interactions and errors are logged and persisted.

---


![Diagramme d'architecture](https://drive.google.com/uc?export=view&id=1kx8bAUrDhHS5gGwgMODPy44E3gA3SzOH)

---

This design enables flexible, AI-driven browser automation suitable for a wide range of tasks requiring natural language control.

