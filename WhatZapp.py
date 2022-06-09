#!/usr/bin/env python3
import time, shutil, random
from selenium import webdriver
from selenium.common import exceptions as selexcept
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains


class Zapper():

    _textbox_path = '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[2]'

    def __init__(self,persistence=False,login=True,headless=False):
        import os
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

        if login: self.login()

    def login(self):
        self.driver.get("https://web.whatsapp.com/")
        try:
            wait = WebDriverWait(self.driver,timeout=150).until(EC.visibility_of_element_located((By.CLASS_NAME,"_3yZPA")))
        except selexcept.TimeoutException:
            print("Error: Timeout occurred during login.")
            self.quit()

    def quit(self):
        self.driver.delete_all_cookies()
        self.driver.quit()

    def load_target(self,target:str):
        self.driver.get(f"https://web.whatsapp.com/send/?phone={target}")

    def send(self,message,text_box,count=1):
        """
        Sends given string to the given text_box and sends the message.
        Note: To send a paragraph, use newline characters to seperate lines.
        """
        for _ in range(count):
            if "\n" in message:
                for frag in message.split("\n"):
                    text_box.send_keys(frag)
                    ActionChains(self.driver).key_down(Keys.SHIFT).key_down(Keys.ENTER).perform()
                    ActionChains(self.driver).key_up(Keys.SHIFT).key_up(Keys.ENTER).perform()
                text_box.send_keys("\n")
                text_box.send_keys("\n")
            else:
                text_box.send_keys(message)
                text_box.send_keys("\n")

    def wait_for_element(self,xpath:str,timeout:int):
        """
        Waits until the web eliment becomes visible on page, then finds the element and returns it.
        The element is identified using it's xpath.
        """
        wait = WebDriverWait(self.driver,timeout=timeout).until(EC.visibility_of_element_located((By.XPATH,xpath)))
        time.sleep(0.5)
        element = self.driver.find_element(By.XPATH,xpath)
        return element

    def send_message(self,target:str,message:str,count=1,timeout=60):
        self.load_target(target)
        text_box = self.wait_for_element(self._textbox_path,timeout)
        self.send(message,text_box,count)
        time.sleep(1)

    def get_incoming(self):
        incoming = self.driver.find_elements(By.CLASS_NAME,'_2wUmf.message-in.focusable-list-item')
        return incoming

    def wait_for_response(self,old_incoming:list,freq=3,timeout=180):
        for _ in range(0,timeout,freq):
            new_incoming = self.get_incoming()
            if new_incoming[-1].id != old_incoming[-1].id:
                return new_incoming[-1].text.split("\n")[0]
            time.sleep(freq)
        raise ResponseWaitTimeout

    def deploy_bot(self, target:str, prompt:str, parser):
        self.load_target(target)
        # Wait and get the message text box
        text_box = self.wait_for_element(self._textbox_path,timeout=60)
        # Send initial prompt message to target
        self.send(prompt,text_box)
        # Get current incoming messages
        old_incoming = self.get_incoming()

        while True:
            # Wait and get new response
            user_response = self.wait_for_response(old_incoming)
            # Parse and formulate my response
            my_response = parser(user_response)
            # If parser returns exit, end the loop
            if my_response == "exit":
                self.send("Goodbye!",text_box)
                break
            # Send my response only if I have anything to say
            else:
                self.send(my_response,text_box)
                old_incoming = self.get_incoming()

    def clean_up(self):
        """
        Cleans up session files created during a persistent run in the working directory.
        """
        self.quit()
        shutil.rmtree(self.session_path)

class ResponseWaitTimeout(Exception):
    pass

def z_parser(response:str):
    my_response = ""
    match response.lower():
        case "who is this?" | "who are you?":
            my_response = "You're talking to Maaz Ahmed's chat bot"
        case "hi"|"hey"|"hello":
            my_response = random.choice(["Yo!","Hello hello!","Namaste!"])
        case "bye":
            my_response = "exit"
        case _:
            my_response = "Sorry, my creator didn't program me to respond to that.\nI am still 0 years old, so please be patient with me."
    return my_response
