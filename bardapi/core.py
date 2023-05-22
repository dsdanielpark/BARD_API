import os
import string
import random
import json
import re
import requests
from deep_translator import GoogleTranslator

ALLOWED_LANGUAGES = {"en", "ko", "ja", "english", "korean", "japanese"}


class Bard:
    """
    Bard class for interacting with the Bard API.
    """

    HEADERS = {
        "Host": "bard.google.com",
        "X-Same-Domain": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Origin": "https://bard.google.com",
        "Referer": "https://bard.google.com/",
    }

    def __init__(
        self,
        token: str = None,
        timeout: int = 20,
        proxies: dict = None,
        session: requests.Session = None,
        language: str = None,
    ):
        """
        Initialize the Bard instance.

        Args:
            token (str): Bard API token.
            timeout (int): Request timeout in seconds.
            proxies (dict): Proxy configuration for requests.
            session (requests.Session): Requests session object.
            language (str): Language code for translation (e.g., "en", "ko", "ja").
        """
        self.token = token or os.getenv("_BARD_API_KEY")
        self.proxies = proxies
        self.timeout = timeout
        self._reqid = int("".join(random.choices(string.digits, k=4)))
        self.conversation_id = ""
        self.response_id = ""
        self.choice_id = ""
        self.session = session or requests.Session()
        self.session.headers = self.HEADERS
        self.session.cookies.set("__Secure-1PSID", self.token)
        self.SNlM0e = self._get_snim0e()
        self.language = language or os.getenv("_BARD_API_LANG")

    def _get_snim0e(self):
        """
        Get the SNlM0e value from the Bard API response.

        Returns:
            str: SNlM0e value.
        Raises:
            Exception: If the __Secure-1PSID value is invalid or SNlM0e value is not found in the response.
        """
        if not self.token or self.token[-1] != ".":
            raise Exception("__Secure-1PSID value must end with a single dot. Enter correct __Secure-1PSID value.")
        resp = self.session.get("https://bard.google.com/", timeout=self.timeout, proxies=self.proxies)
        if resp.status_code != 200:
            raise Exception(f"Response code not 200. Response Status is {resp.status_code}")
        snim0e = re.search(r"SNlM0e\":\"(.*?)\"", resp.text)
        if not snim0e:
            raise Exception("SNlM0e value not found in response. Check __Secure-1PSID value.")
        return snim0e.group(1)

    def get_answer(self, input_text: str) -> dict:
        """
        Get an answer from the Bard API for the given input text.

        Example:
        >>> token = 'xxxxxxxxxx'
        >>> bard = Bard(token=token)
        >>> response = bard.get_answer("나와 내 동년배들이 좋아하는 뉴진스에 대해서 알려줘")
        >>> print(response['content'])

        Args:
            input_text (str): Input text for the query.

        Returns:
            dict: Answer from the Bard API in the following format:
                {
                    "content": str,
                    "conversation_id": str,
                    "response_id": str,
                    "factualityQueries": list,
                    "textQuery": str,
                    "choices": list
                }
        """
        params = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }
        if self.language is not None and self.language not in ALLOWED_LANGUAGES:
            translator_to_eng = GoogleTranslator(source="auto", target="en")
            input_text = translator_to_eng.translate(input_text)
        input_text_struct = [
            [input_text],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        data = {
            "f.req": json.dumps([None, json.dumps(input_text_struct)]),
            "at": self.SNlM0e,
        }
        resp = self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        resp_dict = json.loads(resp.content.splitlines()[3])[0][2]

        if not resp_dict:
            return {"content": f"Response Error: {resp.content}."}
        parsed_answer = json.loads(resp_dict)
        if self.language is not None and self.language not in ALLOWED_LANGUAGES:
            translator_to_lang = GoogleTranslator(source="auto", target=self.language)
            parsed_answer[0][0] = translator_to_lang.translate(parsed_answer[0][0])
            parsed_answer[4] = [
                (x[0], translator_to_lang.translate(x[1][0])) for x in parsed_answer[4]
            ]
        bard_answer = {
            "content": parsed_answer[0][0],
            "conversation_id": parsed_answer[1][0],
            "response_id": parsed_answer[1][1],
            "factualityQueries": parsed_answer[3],
            "textQuery": parsed_answer[2][0] if parsed_answer[2] else "",
            "choices": [{"id": x[0], "content": x[1]} for x in parsed_answer[4]],
        }
        self.conversation_id, self.response_id, self.choice_id = (
            bard_answer["conversation_id"],
            bard_answer["response_id"],
            bard_answer["choices"][0]["id"],
        )
        self._reqid += 100000

        return bard_answer
    
    def get_quote(self,quote_type: str = "random",number_of_quotes:int = 1) -> str:
        """
        Get a random quote from the Bard API.

        Args:
            quote_ype (str): Quote Type.
            number_of_quotes (int): Number of quotes to return.

        Returns:
            dict: Quote from the Bard API in the following format:
                {
                    "content": str,
                    "conversation_id": str,
                    "response_id": str,
                    "factualityQueries": list,
                    "textQuery": str,
                    "choices": list
                }
        """
        params = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }
        
        if self.language is not None and self.language not in ALLOWED_LANGUAGES:
            translator_to_eng = GoogleTranslator(source="auto", target="en")
            quote_type= translator_to_eng.translate(quote_type)
        
        input_text_struct = [
            [f"{number_of_quotes}"+quote_type+"Quote"],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        
        data = {
            "f.req": json.dumps([None, json.dumps(input_text_struct)]),
            "at": self.SNlM0e,
        }
        
        resp = self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=self.timeout,
            proxies=self.proxies,
        )
        
        
        resp_dict = json.loads(resp.content.splitlines()[3])[0][2]

        if not resp_dict:
            return {"content": f"Response Error: {resp.content}."}
        
        parsed_answer = json.loads(resp_dict)
        if self.language is not None and self.language not in ALLOWED_LANGUAGES:
            translator_to_lang = GoogleTranslator(source="auto", target=self.language)
            parsed_answer[0][0] = translator_to_lang.translate(parsed_answer[0][0])
            parsed_answer[4] = [
                (x[0], translator_to_lang.translate(x[1][0])) for x in parsed_answer[4]
            ]
        quote = {
            "content": parsed_answer[0][0],
            "conversation_id": parsed_answer[1][0],
            "response_id": parsed_answer[1][1],
            "factualityQueries": parsed_answer[3],
            "textQuery": parsed_answer[2][0] if parsed_answer[2] else "",
            "choices": [{"id": x[0], "content": x[1]} for x in parsed_answer[4]],
        }
        self.conversation_id, self.response_id, self.choice_id = (
            quote["conversation_id"],
            quote["response_id"],
            quote["choices"][0]["id"],
        )
        self._reqid += 100000

        return quote
    