#!/usr/bin/env python3
import time, shutil, random, os
from selenium import webdriver
from selenium.common import exceptions as selexcept
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains


class Zapper:

    path = {
        "text": '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]',
        "attach": '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/div',
        "media": '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/span/div/div/ul/li[1]/button/input',
        "caption": '//*[@id="app"]/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[2]',
    }

    def __init__(self, persistence=False, login=True, headless=False):

        self.session_path = os.path.join(os.getcwd(), "session")
        if persistence:
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.session_path}")
            options.headless = headless
            self.driver = webdriver.Chrome(options=options)
            self.persistence = persistence
        else:
            self.driver = webdriver.Chrome()
            self.persistence = persistence

        if login:
            self.login()

    def login(self):
        self.driver.get("https://web.whatsapp.com/")
        try:
            wait = WebDriverWait(self.driver, timeout=150).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "_3yZPA"))
            )
        except selexcept.TimeoutException:
            print("Error: Timeout occurred during login.")
            self.quit()

    def quit(self):
        self.driver.delete_all_cookies()
        self.driver.quit()

    def load_target(self, target: str):
        self.driver.get(f"https://web.whatsapp.com/send/?phone={target}")

    def send(self, message, text_box, count=1):
        """
        Sends given string to the given text_box and sends the message.
        Note: To send a paragraph, use newline characters to seperate lines.
        """
        for _ in range(count):
            if "\n" in message:
                for frag in message.split("\n"):
                    text_box.send_keys(frag)
                    ActionChains(self.driver).key_down(Keys.SHIFT).key_down(
                        Keys.ENTER
                    ).perform()
                    ActionChains(self.driver).key_up(Keys.SHIFT).key_up(
                        Keys.ENTER
                    ).perform()
                text_box.send_keys("\n")
                text_box.send_keys("\n")
            else:
                text_box.send_keys(message)
                text_box.send_keys("\n")

    def wait_for_element(self, xpath: str, timeout: int):
        """
        Waits until the web eliment becomes accissible on page, then finds the element and returns it.
        The element is identified using it's xpath.
        """
        element = WebDriverWait(self.driver, timeout=timeout).until(
            lambda x: x.find_element(By.XPATH, xpath)
        )
        return element

    def send_message(self, target: str, message: str, count=1, timeout=60):
        if target:
            self.load_target(target)
        text_box = self.wait_for_element(self.path["text"], timeout)
        self.send(message, text_box, count)
        time.sleep(1)

    def send_media(self, target: str, file_path: str, caption: str, timeout=60):
        """
        Sends media along with a caption to the current contact or to the target (if provided).
        """
        if target:
            self.load_target(target)
        self.wait_for_element(self.path["attach"], timeout).click()
        self.wait_for_element(self.path["media"], timeout).send_keys(file_path)
        text_box = self.wait_for_element(self.path["caption"], timeout)
        self.send(caption, text_box)

    def get_incoming(self):
        incoming = self.driver.find_elements(
            By.CLASS_NAME, "_2wUmf.message-in.focusable-list-item"
        )
        return incoming

    def wait_for_response(self, old_incoming: list, timeout: int, freq=3):
        for _ in range(0, timeout, freq):
            new_incoming = self.get_incoming()
            if new_incoming[-1].id != old_incoming[-1].id:
                return new_incoming[-1].text.split("\n")[0]
            time.sleep(freq)
        raise ResponseWaitTimeout

    def deploy_bot(
        self,
        target: str,
        prompt: str,
        parser,
        parser_args=(),
        exit_msg: str = "Goodbye!",
        response_timeout: int = 300,
        check_freqency: int = 3,
    ):

        self.load_target(target)
        # Wait and get the message text box
        text_box = self.wait_for_element(self.path["text"], 60)
        # Send initial prompt message to target
        self.send(prompt, text_box)
        # Get current incoming messages
        old_incoming = self.get_incoming()

        while True:
            # Wait and get new response
            user_response = self.wait_for_response(
                old_incoming, response_timeout, check_freqency
            )
            # Parse and formulate my response
            my_response = parser(user_response, *parser_args)
            # If parser returns exit, end the loop
            match my_response:
                case "exit":
                    self.send(exit_msg, text_box)
                    break
                case "exit", message:
                    self.send(message, text_box)
                    break
                # Send my response only if I have anything to say
                case _:
                    self.send(my_response, text_box)
                    old_incoming = self.get_incoming()

        return True

    def clean_up(self):
        """
        Cleans up session files created during a persistent run in the working directory.
        """
        self.quit()
        shutil.rmtree(self.session_path)


# Custom exceptions


class ResponseWaitTimeout(Exception):
    pass


# Example Parsers


def z_parser(response: str, *_):
    """
    A simple parser to be used with the bot (Zapper.deploy_bot())
    This parser only responds to messages and nothing else.
    The z_parser doesn't take additional arguments, so any arguments passed to parser_args parameter of deploy_bot method will be ignored.
    """
    my_response = ""
    match response.lower():
        case "who is this?" | "who are you?":
            my_response = "You're talking to Maaz Ahmed's chat bot"
        case "hi" | "hey" | "hello":
            my_response = random.choice(["Hola!", "Hello hello!", "Namaste!"])
        case "bye":
            my_response = "exit"
        case _:
            my_response = "Sorry, my creator didn't program me to respond to that.\nI am still 0 years old, so please be patient with me."
    return my_response


def z_gather(response: str, fields: dict, delimiter=":"):
    """
    A slighly advanced parser compared to the z_parser to be used with the bot (Zapper.deploy_bot()).
    Note: The arguments should be passed to the deploy_bot method in the form of a list or tuple to 'parser_args' parameter.

    Fields: A dictionary of string keys that you'd like to get the response to from the target.
        Example: {"name":"","address":"","country":""}
    Delimiter: The delimiter used to seperate keys from their supposed value entered by the target.
        Example: If delimiter == ";", the target must be asked to send data in this form "key/field; their response"
    """
    if delimiter in response:
        x = response.lower().strip().split(delimiter)
        key = x[0].strip()
        response = x[1].strip()
        if key in fields:
            fields[key] = response
            # Check if responses have been recorded for all provided fields
            if len([val for val in fields.values() if val != "" or None]) == len(fields):
                return "exit", "Responses for all fields have been recorded. Thank you!"
            return f"Your response for '{key}' has been recorded."
    elif response.lower() == "stop":
        return "exit"
    else:
        return f"Invalid reponse. Please provide information as instructed, or send 'stop' to end this session.\nTry {list(fields)[0]}{delimiter} Your Response"
