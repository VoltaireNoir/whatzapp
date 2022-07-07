#!/usr/bin/env python3
import time, shutil, os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains


class Zapper:

    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    path = {
        "text": '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]',
        "attach": '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/div',
        "media": '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[1]/div[2]/div/span/div/div/ul/li[1]/button/input',
        "caption": '//*[@id="app"]/div/div/div[2]/div[2]/span/div/span/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[2]',
        "menu": '//*[@id="side"]/header/div[2]/div/span/div[3]/div/span',
        "logout1": '//*[@id="side"]/header/div[2]/div/span/div[3]/span/div/ul/li[4]/div[1]',
        "logout2": '//*[@id="app"]/div/span[2]/div/div/div/div/div/div/div[3]/div/div[2]',
    }

    def __init__(
        self, persistence=False, login=True, headless=False, autostart=True, logs=False
    ):

        self.__session_path = os.path.join(os.getcwd(), "session")
        self.__persistence = persistence
        self.__headless = headless
        self.__login_enabled = login
        self.__logs = logs
        self.__driver = None
        self.schedule = []

        if logs:
            logger(
                f"Zapper Initialized: auto:{autostart}, persist:{persistence}, login:{login}, head:{headless}"
            )
        if autostart:
            self.start(persistence, login, headless)

    def __webdriver_check(self):
        if self.__driver is None:
            raise ZapperSessionNotStarted(
                "Session needs to be running for this functionality to work."
            )

    def start(self, persistence=None, login=None, headless=None):
        if self.__driver is not None:
            return
        if persistence is not None:
            self.__persistence = persistence
        if login is not None:
            self.__login_enabled = login
        if headless is not None:
            self.__headless = headless

        if self.__persistence:
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.__session_path}")
            if self.__headless:
                options.add_argument("--headless")
            self.__driver = webdriver.Chrome(options=options)
        else:
            self.__driver = webdriver.Chrome()

        self.__driver.execute_cdp_cmd(
                "Network.setUserAgentOverride", {"userAgent": self.user_agent}
            )

        if self.__logs:
            logger("Session started")

        if self.__login_enabled:
            self.login()

    @property
    def persistence(self):
        return self.__persistence

    @property
    def session_path(self):
        return self.__session_path

    @property
    def headless_mode(self):
        return self.__headless

    @property
    def login_enabled(self):
        return self.__login_enabled

    @property
    def logs(self):
        return self.__logs

    @property
    def driver(self):
        return self.__driver

    def stop(self):
        """Quits Chrome and ends web-driver session. Zapper needs to be initialized again to use after quitting."""
        if self.__driver is not None:
            self.__driver.delete_all_cookies()
            self.__driver.quit()
            self.__driver = None
            if self.__logs:
                logger("Session stopped")

    def login(self, timeout=180):
        """Takes you to WhatsApp login page and waits until login is complete"""
        self.__webdriver_check()
        self.__driver.get("https://web.whatsapp.com/")
        self.wait_for_element("_3yZPA", timeout, by="class name")
        if self.__logs:
            logger("WhatsApp login successful")
        return True

    def logout(self):
        """Logs you out of WhatsApp if logged in, otherwise it raises a timeout exception."""
        self.__webdriver_check()
        if "web.whatsapp.com" not in self.__driver.current_url:
            self.__driver.get("https://web.whatsapp.com/")
        self.wait_for_element(self.path["menu"], 60).click()
        self.wait_for_element(self.path["logout1"], 60).click()
        self.wait_for_element(self.path["logout2"], 60).click()

    def load_target(self, target: str, force_load=False):
        """Loads target number's WhatsApp chat if not already open. Won't work without country code."""
        self.__webdriver_check()
        if force_load:
            self.__driver.get(f"https://web.whatsapp.com/send/?phone={target}")
        # Try to check if already on target page
        if self.is_target(target):
                return
        # Load target as usual
        self.__driver.get(f"https://web.whatsapp.com/send/?phone={target}")

        if self.__logs:
            logger(f"Loading target: {target}")

    def is_target(self, target: str) -> bool:
        """Uses the incoming message as a sample to check whether they are from the given target number and returns True or False."""
        self.__webdriver_check
        return target in self.__driver.page_source

    def wait_for_element(self, loc: str, timeout: int, by="xpath"):
        """
        Waits until the web eliment becomes accissible on page, then finds the element and returns it.
        The element is identified using it's xpath by default, unless class_name is specified.
        """
        self.__webdriver_check()
        try:
            element = WebDriverWait(self.__driver, timeout=timeout).until(
                lambda x: x.find_element(by, loc)
            )
        except:
            raise ElementWaitTimeout(
                "Either the page didn't load or the target element was not found on the page."
            )
        return element

    def send(self, message, text_box, count=1):
        """
        Sends given string to the given text_box and sends the message.
        Note: To send a paragraph, use newline characters to seperate lines.
        """
        for _ in range(count):
            if "\n" in message:
                for frag in message.split("\n"):
                    text_box.send_keys(frag)
                    ActionChains(self.__driver).key_down(Keys.SHIFT).key_down(
                        Keys.ENTER
                    ).perform()
                    ActionChains(self.__driver).key_up(Keys.SHIFT).key_up(
                        Keys.ENTER
                    ).perform()
                text_box.send_keys("\n")
                text_box.send_keys("\n")
            else:
                text_box.send_keys(message)
                text_box.send_keys("\n")
        if self.__logs:
            logger(f"Message sent: {message}")

    def send_message(self, target: str, message: str, count=1, timeout=60):
        """Loads target chat and sends them the message. Target can be an empty string or None object if target chat is already open."""
        self.__webdriver_check()
        if target:
            self.load_target(target)
        text_box = self.wait_for_element(self.path["text"], timeout)
        if self.__logs:
            logger(f"Sending message to target: {target}")
        self.send(message, text_box, count)
        time.sleep(0.5)

    def send_media(self, target: str, file_path: str, caption: str, timeout=60):
        """
        Sends media along with a caption to the current contact or to the target (if provided).
        """
        self.__webdriver_check()
        if target:
            self.load_target(target)
        self.wait_for_element(self.path["attach"], timeout).click()
        self.wait_for_element(self.path["media"], timeout).send_keys(file_path)
        text_box = self.wait_for_element(self.path["caption"], timeout)
        self.send(caption, text_box)
        time.sleep(0.5)
        if self.__logs:
            logger(f"Media file ({file_path}) sent to {target}")

    def schedule_message(
        self, target: str, message: str, day=0, hour=0, minute=0, second=0
    ):
        """
        Schedule messages to be sent later. If none of the time related arguments are given, current time is used, meaning that the message will be sent without waiting.
        If only time related argument passed is for second, current time is used for the rest (i.e. message to be sent at given second of the current minute and hour).
        Same applies to minute and hour. Example: if hour = 2, the message willl be scueduled to be sent at hour 2 of the current day (2 AM).
        Note: day, hour, minute, and second parameters are for scheduling given time, and it is not wait time.
        To clear the schedule or to make any manual changes, you can directly access Zapper.schedule, which is a list. (Example: Zapper.schedule.clear())
        """
        if not day:
            day = datetime.now().day
        if second and not minute and not hour:
            minute, hour = datetime.now().minute, datetime.now().hour
        if minute and not hour:
            hour = datetime.now().hour
        year, month = datetime.now().year, datetime.now().month
        self.schedule.append(
            (target, message, datetime(year, month, day, hour, minute, second))
        )

    def run_schedular(self, schedule: list = []):
        """
        Run already scheduled messages or schedule multiple or single messages by passing a list with tuples containing (target,message,scheduled time) as an argument (Here scheduled time is a datetime object)
        If current time is already past the scheduled time, the job will be executed without waiting. Only successful jobs are removed from the schedule. Failed ones are kept so that they can be run again.
        """
        self.__webdriver_check()
        if not schedule:
            schedule = self.schedule[:]
        if schedule:
            self.schedule = schedule[:]
        schedule = sorted(schedule, key=lambda x: x[2])
        if self.__logs:
            logger(f"Message schedular started with {len(schedule)} jobs")
        err = 0
        for i, event in enumerate(schedule):
            target, message, schtime = event
            diff = schtime - datetime.now()
            try:
                if self.__logs:
                    logger(f"Starting job {i+1}: target {target}, scheduled {schtime}")
                if diff.days >= 0:
                    if self.__logs:
                        logger(f"Sleeping for {diff.seconds}s")
                    time.sleep(diff.seconds)
                    self.send_message(target, message)
                else:
                    self.send_message(target, message)
                if self.__logs:
                    logger(f"Job {i+1} completed sucessfully")
                self.schedule.remove(event)
            except Exception as e:
                err += 1
                if self.__logs:
                    logger(f"Job {i+1} failed.\n  Error occured: {e}")
                continue
        if self.__logs:
            logger(
                f"Schedular finished: {len(schedule) - err} jobs completed with {err} errors"
            )

    def get_incoming(self):
        """Gets all the available incoming messages on the chat page and returns them in a list."""
        self.__webdriver_check()
        incoming = self.__driver.find_elements(
            By.CLASS_NAME, "_2wUmf.message-in.focusable-list-item"
        )
        return incoming

    def wait_for_response(self, old_incoming: list, timeout: int, freq=3):
        """Uses a list of old_incoming messages for comparison and waits for a new message, and returns it. Raises ResponseWaitTimeout if there's no response and the timeout is reached."""
        for _ in range(0, timeout, freq):
            new_incoming = self.get_incoming()
            if old_incoming == []:
                if len(new_incoming) > len(old_incoming):
                    return new_incoming[-1].text.split("\n")[0]
            elif new_incoming[-1].id != old_incoming[-1].id:
                return new_incoming[-1].text.split("\n")[0]
            time.sleep(freq)
        raise ResponseWaitTimeout(
            "No user response was detected before timeout was reached."
        )

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
        The heart of the bot lies in the parser, which is a function passed as an argument. Use pre-defined parsers (z_parser,z_gather,z_custom) or define your own.
        This enters an infite while loop, which can only be broken when the parser returns "exit" string or when the response timeout exception is raised.
        Read documentation to learn how to use a custom defined parser.
        """

        self.__webdriver_check()

        self.load_target(target)
        # Wait and get the message text box
        text_box = self.wait_for_element(self.path["text"], 60)

        if self.__logs:
            logger(f"Deploying bot on target: {target}")

        # Send initial prompt message to target
        self.send(prompt, text_box)
        # Get current incoming messages
        old_incoming = self.get_incoming()
        while True:
            # Wait and get new response
            user_response = self.wait_for_response(
                old_incoming, response_timeout, check_freqency
            )
            if self.__logs:
                logger(f"Message received: {user_response}")
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
        time.sleep(0.5)
        if self.__logs:
            logger("Bot session ended")
        return True

    def clean_up(self):
        """
        Cleans up session files created during a persistent run in the working directory.
        """
        self.stop()
        shutil.rmtree(self.__session_path)
        if self.__logs:
            logger("Cleanup complete")


# Exceptions


class ResponseWaitTimeout(Exception):
    pass


class ElementWaitTimeout(Exception):
    pass


class ZapperSessionNotStarted(Exception):
    pass


# Example Parsers


def z_parser(response: str):
    """
    A simple parser to be used with the bot (Zapper.deploy_bot())
    This parser only responds to messages using hardcoded replies and nothing else.
    The z_parser doesn't take additional arguments, so any arguments passed to parser_args parameter of deploy_bot method will be ignored.
    """
    import random

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
        x = response.strip().lower().split(delimiter)
        key = x[0].strip()
        response = x[1].strip()
        if key in fields:
            fields[key] = response
            # Check if responses have been recorded for all provided fields
            if len([val for val in fields.values() if val != "" or None]) == len(
                fields
            ):
                return "exit", "Responses for all fields have been recorded. Thank you!"
            return f"Your response for '{key}' has been recorded."
    elif response == "stop":
        return "exit", "Thank you for your time."
    else:
        return f"Invalid reponse.\nTry {list(fields)[0]}{delimiter} Your Response.\nOr send 'stop' to end this session."


def z_cat_facts(response: str):
    """
    A simple parser to be used with Zapper.deploy_bot(). This parser returns a random cat fact from the internet (retreived from catfact.ninja) whenever it receives 'cat' 'fact' or 'cat fact' as user-response.
    The parser returns the exit message when the user response is "stop".
    """
    import requests

    response = response.strip().lower()
    if response in ("cat", "fact", "cat fact"):
        fact = requests.api.get("https://catfact.ninja/fact").json()
        return f"Here's a cat fact for you:\n{fact['fact']}"
    elif response == "stop":
        return "exit", "Time for a catnap... Zzzz..."
    else:
        return "You have been chosen to receive cat facts.\nSend 'cat' or 'fact' or 'cat fact' to receive wisdom.\nSend 'stop' to go back to being miserable again."


# Logger


def logger(message: str):
    logmessage = f"LOG [{datetime.now().strftime('%b %d %T')}]: {message}"
    print(logmessage)
    with open("z_log", "a") as f:
        f.write(logmessage + "\n")


if __name__ == "__main__":
    pass
