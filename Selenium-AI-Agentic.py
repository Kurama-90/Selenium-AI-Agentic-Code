import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import json
from pathlib import Path
from urllib.parse import urlparse
import sys

class AgenticAIBot:
    def __init__(self):
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.GEMINI_API_KEY = self.config.get('GEMINI_API_KEY')
        self._validate_api_key()
        self.driver = self._initialize_browser()
        self.wait = WebDriverWait(self.driver, self.config.get("timeout", 30))
        self.GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.GEMINI_API_KEY}"
        self.session = requests.Session()
        self.history = []

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('agentic_ai.log'),
                logging.StreamHandler()
            ]
        )

    def _initialize_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())

        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.logger.error(f"Erreur d'initialisation du navigateur: {str(e)}")
            raise

    def _load_config(self):
        default_config = {
            "max_retries": 3,
            "default_wait_time": 5,
            "timeout": 30,
            "safe_mode": True
        }
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        except (FileNotFoundError, json.JSONDecodeError):
            self.logger.warning("Utilisation de la configuration par défaut")
            return default_config

    def _validate_api_key(self):
        if not self.GEMINI_API_KEY or len(self.GEMINI_API_KEY) < 30:
            self.logger.error("Clé API invalide ou manquante")
            raise ValueError("Clé API invalide ou manquante")

    def ask_gemini(self, instruction: str, max_retries: int = 3):
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": instruction}],
                "role": "user"
            }]
        }

        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.GEMINI_URL,
                    headers=headers,
                    json=data,
                    timeout=self.config["timeout"]
                )
                response.raise_for_status()
                try:
                    result = response.json()['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    self.logger.error("Format de réponse inattendu depuis l'API Gemini")
                    return None
                self._log_interaction(instruction, result)
                return result
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Tentative {attempt + 1} échouée: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error("Échec après plusieurs tentatives")
                    return None

    def _log_interaction(self, prompt, response):
        interaction = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": prompt,
            "response": response
        }
        self.history.append(interaction)
        with open('interaction_history.json', 'a') as f:
            f.write(json.dumps(interaction) + '\n')

    def execute_task(self, instructions: str):
        if not instructions:
            self.logger.warning("Aucune instruction à exécuter")
            return

        lines = [line.strip() for line in instructions.strip().split('\n') if line.strip()]

        for line in lines:
            try:
                if match := re.match(r'OPEN\("(.+?)"\)', line):
                    self.open_url(match.group(1))
                elif match := re.match(r'TYPE\("(.+?)",\s*"(.+?)"\)', line):
                    self.fill_field(match.group(1), match.group(2))
                elif match := re.match(r'CLICK\("(.+?)"\)', line):
                    self.click_element(match.group(1))
                elif match := re.match(r'WAIT\((\d+)\)', line):
                    self.wait_seconds(int(match.group(1)))
                else:
                    self.logger.warning(f"Commande non reconnue: {line}")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'exécution: {str(e)}")
                if not self.config["safe_mode"]:
                    raise

    def open_url(self, url: str):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.logger.info(f"Ouverture de l'URL: {url}")
        self.driver.get(url)

    def fill_field(self, selector: str, text: str):
        self.logger.info(f"Saisie dans '{selector}': {text}")
        element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        element.clear()
        element.send_keys(text)

    def click_element(self, selector: str):
        self.logger.info(f"Clic sur l'élément: {selector}")
        element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        element.click()

    def wait_seconds(self, seconds: int):
        self.logger.info(f"Attente de {seconds} seconde(s)")
        time.sleep(seconds)

    def generate_prompt(self, user_command: str) -> str:
        return f"""Génère des commandes Selenium pour : {user_command}
Formats disponibles:
- OPEN(\"url\")
- TYPE(\"selector\", \"text\")
- CLICK(\"selector\")
- WAIT(seconds)

Exemple :
OPEN(\"https://google.com\")
TYPE(\"textarea[name='q']\", \"recherche\")
CLICK(\"button[type='submit']\")
WAIT(3)
"""

    def run(self):
        print("Agentic AI Bot - Tapez 'exit' pour quitter")
        try:
            while True:
                command = input("\nInstruction : ").strip()
                if command.lower() in ('exit', 'quit'):
                    break

                prompt = self.generate_prompt(command)
                instructions = self.ask_gemini(prompt)

                if instructions:
                    print("\nInstructions générées:")
                    print(instructions)
                    self.execute_task(instructions)
                else:
                    print("Aucune instruction générée")
        except KeyboardInterrupt:
            print("\nArrêt demandé")
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.session.close()
            print("Agent arrêté")

if __name__ == "__main__":
    bot = AgenticAIBot()
    bot.run()
