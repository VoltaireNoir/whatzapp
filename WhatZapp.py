#!/usr/bin/env python3
import time, shutil, random, os
from selenium import webdriver
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
        "menu": '//*[@id="side"]/header/div[2]/div/span/div[3]/div/span',
        "logout1": '//*[@id="side"]/header/div[2]/div/span/div[3]/span/div/ul/li[4]/div[1]',
        "logout2": '//*[@id="app"]/div/span[2]/div/div/div/div/div/div/div[3]/div/div[2]'
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
        """Takes you to WhatsApp login page and waits until login is complete"""
        self.driver.get("https://web.whatsapp.com/")
        self.wait_for_element("_3yZPA",180,by="class name")
        return True

    def logout(self):
        """Logs you out of WhatsApp if logged in, otherwise it raises a timeout exception."""
        if "web.whatsapp.com" not in self.driver.current_url:
            self.driver.get("https://web.whatsapp.com/")
        self.wait_for_element(self.path["menu"],60).click()
        self.wait_for_element(self.path["logout1"],60).click()
        self.wait_for_element(self.path["logout2"],60).click()

    def quit(self):
        """Quits Chrome and ends web-driver session. Zapper needs to be initialized again to use after quitting."""
        self.driver.delete_all_cookies()
        self.driver.quit()

    def load_target(self, target: str,force_load=False):
        """Loads target number's WhatsApp chat if not already open. Won't work without country code."""
        if force_load:
            self.driver.get(f"https://web.whatsapp.com/send/?phone={target}")
        # Try to check if already on target page
        incoming = self.get_incoming()
        if incoming != []:
           if self.is_target(incoming[0],target):
               return
        # Load target as usual
        self.driver.get(f"https://web.whatsapp.com/send/?phone={target}")

    def is_target(self,incoming_sample, target: str) -> bool:
        """Uses the incoming messages as a sample to check whether they are from the given target number and returns True or False."""
        data_id = incoming_sample.get_attribute("data-id")
        if target in data_id:
            return True
        else:
            return False

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

    def wait_for_element(self, loc: str, timeout: int, by='xpath'):
        """
        Waits until the web eliment becomes accissible on page, then finds the element and returns it.
        The element is identified using it's xpath by default, unless class_name is specified.
        """
        element = WebDriverWait(self.driver, timeout=timeout).until(
            lambda x: x.find_element(by, loc)
        )
        return element

    def send_message(self, target: str, message: str, count=1, timeout=60):
        """Loads target chat and sends them the message. Target can be an empty string or None object if target chat is already open."""
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
        """Gets all the available incoming messages on the chat page and returns them in a list."""
        incoming = self.driver.find_elements(
            By.CLASS_NAME, "_2wUmf.message-in.focusable-list-item"
        )
        return incoming

    def wait_for_response(self, old_incoming: list, timeout: int, freq=3):
        """Uses a list of old_incoming messages for comparison and waits for a new message, and returns it."""
        for _ in range(0, timeout, freq):
            new_incoming = self.get_incoming()
            if old_incoming == []:
                if len(new_incoming) > len(old_incoming):
                    return new_incoming[-1].text.split("\n")[0]
            elif new_incoming[-1].id != old_incoming[-1].id:
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
        """
        Deploys a simple bot on the given target. It waits for target responses and uses the parser to respond accordingly.
        This enters an infite while loop, which can only be broken when the parser returns "exit" string or when the timeout exception is raised.
        The heart of the bot lies in the parser, which is a function passed as an argument. Use pre-defined parsers (z_parser,z_gather,z_custom) or define your own.
        Read documentation to learn how to use a custom defined parser.
        """

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
    This parser only responds to messages using hardcoded replies and nothing else.
    The z_parser doesn't take additional arguments, so any arguments passed to parser_args parameter of deploy_bot method will be ignored.
    """
    my_response = ""
    match response.lower():
        case "who is this" | "who is this?" | "who are you?" | "who are you":
            my_response = "You're talking to Maaz Ahmed's chat bot"
        case "hi" | "hey" | "hello":
            my_response = random.choice(["Hola!", "Hello hello!", "Namaste!"])
        case "bye":
            my_response = "exit"
        case _:
            my_response = "Sorry, my creator didn't program me to respond to that.\nI am still 0 years old, so please be patient with me."
    return my_response

def z_custom(response: str, replies: dict, default_reply: str):
    """
    A very simple parser made to be used with the bot (Zapper.deploy_bot()).
    It takes a dictionary as an argument, which should contain strings of responses/conditions as keys, and their replies as values.
    And a default_reply, which is a string used whenever the target reponds something that isn't within the scope of provided replies.
    Example: {"hi":"Hey, how are you doing?","Who is this?":"I am a bot","Bye":"exit"}
    Note: The dictionary should be passed wrapped in a list or tuple as an argument to parser_args parameter.
    """
    response = response.strip().lower()
    if response in replies:
        return replies[response]
    else:
        return default_reply

def z_gather(response: str, fields: dict, delimiter=":"):
    """
    A slighly advanced parser compared to the z_parser to be used with the bot (Zapper.deploy_bot()).
    Note: The arguments should be passed to the deploy_bot method wrapped in a list or tuple to 'parser_args' parameter.

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
    elif response == "stop":
        return "exit", "Thank you for your time."
    else:
        return f"Invalid reponse.\nTry {list(fields)[0]}{delimiter} Your Response.\nOr send 'stop' to end this session."
