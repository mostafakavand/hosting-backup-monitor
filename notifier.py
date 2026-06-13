import asyncio
import requests
import logging
import config

class BaleNotifier:
    async def send(self, message, max_retries=3):
        """Send message to Bale channel using bot with retry mechanism"""
        url = f"https://tapi.bale.ai/bot{config.BALE_TOKEN}/sendMessage"
        data = {
            "chat_id": config.BALE_CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                return
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logging.error(f"Error sending Bale message after {max_retries} attempts: {str(e)}")
                else:
                    logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(2)  # Wait before retrying