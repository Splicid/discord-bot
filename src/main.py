import discord
import os
import threading
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button, Select
from werkzeug.serving import make_server
from flask import Flask, request, jsonify
from helpers import google_api

#discord key
DISCORD_KEY = os.getenv("DISCORD_TOKEN")

# Set up the bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask
app = Flask(__name__)

# Define Modal
class MyModal(Modal):
    def __init__(self):
        super().__init__(title="Your Modal Title")
        self.add_item(TextInput(label="Name", placeholder="Your name here..."))
        self.add_item(TextInput(label="Name", placeholder="Your name here..."))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Thanks for submitting!", ephemeral=True)


# Flask route to handle POST request
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
        return jsonify({"error": str(e)}), 500


# Function to Send Modal to User
async def send_modal_to_user(user_id):
    try:
        user = await bot.fetch_user(user_id)  # Fetch the user by ID
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
        print(f"Modal button sent to {user.name}.")
    except discord.Forbidden:
        print(f"Could not send DM to user {user_id}. They might have DMs disabled.")
    except Exception as e:
        print(f"Error in sending modal: {e}")


# Bot ready event
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# Flask thread to run Flask app in parallel with the bot
class FlaskThread(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.server = make_server("127.0.0.1", 8080, app)
        self.context = app.app_context()

    def run(self):
        with self.context:
            self.server.serve_forever()

@app.route('/send_message', methods=['POST'])
def send_message_direct():
    data = request.json
    user_id = "245018124280135681"
    message = data.get("message")
    
    if not user_id or not message:
        return jsonify({"error": "missing user_id or message"})

    async def send_dm():
        try:
            # Get calendar events
            calendar = google_api.Connection()
            data = calendar.get_cal()
            user = await bot.fetch_user(int(user_id))
            await user.send(data)
        except Exception as e:
            print(f"Failed to send message: {e}")
    
    bot.loop.create_task(send_dm())
    return jsonify({"status": "Message send"}), 200

# Start Flask app in a thread
flask_thread = FlaskThread(app)
flask_thread.start()

# Run the bot
bot.run(DISCORD_KEY)