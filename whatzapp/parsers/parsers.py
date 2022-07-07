#!/usr/bin/env python3
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
