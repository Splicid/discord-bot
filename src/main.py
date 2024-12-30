# src/main.py

import discord
import os
import logging
import threading
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
from werkzeug.serving import make_server
from flask import Flask, request, jsonify
from helpers.google_api import Connection  # Adjusted import

# Load environment variables (ensure DISCORD_TOKEN is set)
DISCORD_KEY = os.getenv("DISCORD_TOKEN")
if not DISCORD_KEY:
    raise ValueError("DISCORD_TOKEN environment variable not set.")

# Set up the bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True  # Ensure message content intent is enabled if needed
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask
app = Flask(__name__)

# Define Modal
class MyModal(Modal):
    def __init__(self):
        super().__init__(title="Your Modal Title")
        self.add_item(TextInput(label="Name", placeholder="Your name here..."))
        self.add_item(TextInput(label="Email", placeholder="Your email here..."))  # Changed label for clarity

    async def on_submit(self, interaction: discord.Interaction):
        name = self.children[0].value
        email = self.children[1].value
        # Process the data as needed
        await interaction.response.send_message(f"Thanks for submitting, {name}!", ephemeral=True)

# Flask route to handle POST request for sending modal
@app.route('/modal', methods=['POST'])
def send_modal_dm():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing 'user_id' in request"}), 400
    try:
        # Trigger bot action in the background
        bot.loop.create_task(send_modal_to_user(int(user_id)))
        return jsonify({"message": "Modal trigger initiated"}), 200
    except Exception as e:
        logging.error(f"Error in /modal route: {e}")
        return jsonify({"error": str(e)}), 500

# Function to Send Modal to User
@app.route('/send_modal', methods=['POST'])
async def send_modal_to_user(user_id):
    try:
        user = await bot.fetch_user(user_id)  # Fetch the user by ID
        if not user:
            logging.Warning(f"User with ID {user_id} not found.")
            return
        view = View()  # Create a view to hold the button

        # Define and add the button
        button = Button(label="Open Modal", style=discord.ButtonStyle.primary)

        # Button callback
        async def button_callback(interaction: discord.Interaction):
            modal = MyModal()  # Create the modal instance
            await interaction.response.send_modal(modal)  # Send the modal

        button.callback = button_callback  # Attach the callback to the button
        view.add_item(button)  # Add the button to the view

        # Send a DM with the button
        await user.send("Click the button below to open the modal:", view=view)
        logging.info(f"Modal button sent to {user.name} ({user.id}).")
    except discord.Forbidden:
        logging.warning(f"Could not send DM to user {user_id}. They might have DMs disabled.")
    except Exception as e:
        logging.critical(f"Error in sending modal: {e}")

# Flask route to handle POST request for sending a message
@app.route('/send_message', methods=['POST'])
def send_message_direct():
    data = request.json
    user_id = data.get("user_id")  # Accept user_id from request
    message = data.get("message")
    
    if not user_id or not message:
        return jsonify({"error": "Missing 'user_id' or 'message' in request"}), 400

    async def send_dm():
        try:
            # Get calendar events
            calendar = Connection()
            calendar_data = calendar.get_cal()
            user = await bot.fetch_user(int(user_id))
            logging.info(calendar_data)
            await user.send(calendar_data)
            logging.info(f"Sent calendar data to {user.name} ({user.id}).")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")
    
    bot.loop.create_task(send_dm())
    return jsonify({"status": "Message sent"}), 200

# Bot ready event
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

# Flask thread to run Flask app in parallel with the bot
class FlaskThread(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.server = make_server("127.0.0.1", 8250, app)
        self.ctx = app.app_context()

    def run(self):
        with self.ctx:
            self.server.serve_forever()

# Start Flask app in a thread
flask_thread = FlaskThread(app)
flask_thread.start()
logging.debug("Flask server started on http://127.0.0.1:8250")

# Run the bot
bot.run(DISCORD_KEY)