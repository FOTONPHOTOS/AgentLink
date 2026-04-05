from .neural_link import NeuralLink
import time

class RemoteBrowser:
    def __init__(self, neural_link):
        self.brain = neural_link

    def focus(self):
        """Ensures Chrome is focused by clicking the 'Chrome' title bar or icon."""
        coords = self.brain.find_text("Google Chrome")
        if coords:
            self.brain.act("click", coords)
        else:
            # Fallback: Search for it
            self.brain.act("type", "google-chrome") # If search bar is open

    def goto(self, url):
        """Navigates to a URL."""
        self.focus()
        # Ctrl+L to highlight URL bar
        self.brain.act("exec", "export DISPLAY=:10 && xdotool key ctrl+l")
        time.sleep(0.5)
        self.brain.act("type", url) 
        # Type hits enter automatically

    def read_page(self):
        """Returns the text content of the current page via OCR."""
        return self.brain.see()

    def click_text(self, text):
        """Clicks on a link/button with specific text."""
        coords = self.brain.find_text(text)
        if coords:
            return self.brain.act("click", coords)
        return {"success": False, "reason": "Text not found"}
