"""
Created on 2022-08-25

@author: wf
"""
import asyncio
import selenium.common
from selenium.webdriver.common.by import By
import justpy as jp
from tests.browser_test import SeleniumBrowsers
from tests.base_server_test import BaseAsynctest
from tests.basetest import Basetest
from examples.basedemo import Demo
from testfixtures import LogCapture

class TestWithSelenium(BaseAsynctest):
    """
    testing actual browser behavior with selenium
    """

    async def setUp(self):
        await super().setUp(port=8124)

    async def onDivClick(self, msg):
        """
        handle the click of the div
        """
        print(msg)
        self.clickCount += 1
        msg.target.text = f"I was clicked {self.clickCount} times"

    async def wp_to_test(self):
        """
        the example Webpage under test
        """
        wp = jp.WebPage(debug=True)
        self.clickCount = 0
        d = jp.Div(
            text="Not clicked yet",
            a=wp,
            classes="w-48 text-xl m-2 p-1 bg-blue-500 text-white",
        )
        d.on("click", self.onDivClick)
        d.additional_properties = [
            "screenX",
            "pageY",
            "altKey",
            "which",
            "movementX",
            "button",
            "buttons",
        ]
        return wp

    async def testClickDemo(self):
        """
        this will actually start a firefox browser and the websocket reload dialog will appear
        """
        # do not run automatically in CI yet
        # need to fix
        # if Basetest.inPublicCI():
        #    return
        self.browser = SeleniumBrowsers(headless=Basetest.inPublicCI()).getFirst()
        await asyncio.sleep(self.server.sleep_time)
        await self.server.start(self.wp_to_test)
        url = self.server.get_url("/")
        self.browser.get(url)
        await asyncio.sleep(self.server.sleep_time)
        divs = self.browser.find_elements(By.TAG_NAME, "div")
        # get the clickable div
        div = divs[1]
        self.assertEqual("Not clicked yet", div.text)
        for i in range(5):
            div.click()
            await asyncio.sleep(self.server.sleep_time)
            self.assertEqual(f"I was clicked {i+1} times", div.text)
        self.browser.close()
        await asyncio.sleep(self.server.sleep_time)
        await self.server.stop()
        
    async def testIssue279(self):
        """
        see https://github.com/justpy-org/justpy/issues/279
        
        """
        self.browser = SeleniumBrowsers(headless=Basetest.inPublicCI()).getFirst()
        await asyncio.sleep(self.server.sleep_time)
        Demo.testmode=True
        from examples.issues.issue_279_key_error import issue_279
        await self.server.start(issue_279)
        url = self.server.get_url("/")
        self.browser.get(url)
        await asyncio.sleep(self.server.sleep_time)
        buttons = self.browser.find_elements(By.TAG_NAME, "button")
        debug=True
        if debug:
            print(f"found {len(buttons)} buttons")
        await asyncio.sleep(0.5)
        ok='False'
        with LogCapture() as lc:
            try:
                for buttonIndex in [0,1,2,3]:
                    buttons[buttonIndex].click()
                    await asyncio.sleep(0.25)
                await asyncio.sleep(1.0)
                for buttonIndex in [0,1,2,3]:
                    buttons[buttonIndex].click()
                    await asyncio.sleep(0.25)
            except selenium.common.exceptions.StaleElementReferenceException:
                if debug:
                    print("Expected sideeffect: Selenium already complains about missing button")
                ok=True
                pass
            await asyncio.sleep(3.2)
            if debug:
                print(f"log capture: {str(lc)}")
            expecteds=[
                "component with id",
                "doesn't exist (anymore ...) it might have been deleted before the event handling was triggered"
            ]
            for i,expected in enumerate(expecteds):
                if not ok:
                    self.assertTrue(expected in str(lc),f"{i}:{expected}")
                else:
                    if not expected in str(lc):
                        print(f"{i}:{expected} missing in captured log")
        
        self.browser.close()
        await self.server.stop()