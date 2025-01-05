# src/main.py

import discord
import os
import logging
import threading
from datetime import datetime
from discord.ext import commands
from discord.embeds import Embed
from discord.ui import Modal, TextInput, View, Button
from discord import Interaction, ButtonStyle
from werkzeug.serving import make_server
from flask import Flask, request, jsonify
from helpers.google_api import Connection  # Adjusted import

from functools import partial

# Load environment variables (ensure DISCORD_TOKEN is set)
DISCORD_KEY = os.getenv("DISCORD_TOKEN")
if not DISCORD_KEY:
    raise ValueError("DISCORD_TOKEN environment variable not set.")

# Set up logging
logging.basicConfig(filename="app.log", level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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
        self.add_item(TextInput(label="Email", placeholder="Your email here..."))

    async def on_submit(self, interaction: discord.Interaction):
        name = self.children[0].value
        email = self.children[1].value
        await interaction.response.send_message(f"Thanks for submitting, {name}!", ephemeral=True)

# Factory function to create button callbacks
def create_button_callback(task_id, task_name):
    async def button_callback(interaction: Interaction):
        # Perform action to mark task as done
        try:
            # Update Google Calendar
            calendar = Connection()
            event = calendar.calendar_service.events().get(calendarId=calendar.user, eventId=task_id).execute()
            event['status'] = 'cancelled'  # Mark as cancelled or any other status

            # Update calendar event color to green
            event['colorId'] = 9
            updated_event = calendar.calendar_service.events().update(calendarId=calendar.user, eventId=task_id, body=event).execute()
            
            # Inform the user
            await interaction.response.send_message(f"Task '{task_name}' has been marked as done and updated in your calendar.", ephemeral=True)
            logger.info(f"Task '{task_name}' marked as done and updated in calendar.")
            
            # Optionally, edit the original embed to reflect the completion
            # Note: Editing the message requires storing a reference to it
        except Exception as e:
            logger.error(f"Failed to update task '{task_name}' in calendar: {e}")
            await interaction.response.send_message(f"Failed to mark task '{task_name}' as done.", ephemeral=True)
    return button_callback

# Define the custom View with 'Done' buttons per task
class TaskDoneView(View):
    def __init__(self, tasks):
        super().__init__(timeout=None)
        for task in tasks:
            task_id = task['id']
            task_name = task.get('summary', 'No Title')
            # Define a 'Done' button for each task with a unique custom_id
            button = Button(label=f"Done: {task_name}", style=ButtonStyle.success, custom_id=f"done_{task_id}")
            # Assign a unique callback to each button
            button.callback = create_button_callback(task_id, task_name)
            self.add_item(button)

# Flask route to handle POST request for sending an embed with 'Done' buttons
@app.route('/send_calendar', methods=['POST'])
def send_calendar():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    async def send_calendar_task():
        try:
            # Get calendar events
            calendar = Connection()
            tasks = calendar.get_cal()  # Should return list of event dicts
            if not tasks:
                embed = Embed(title="Today's Tasks", description="No upcoming events found for today.", color=0x3498db)
                user = await bot.fetch_user(int(user_id))
                if user:
                    await user.send(embed=embed)
                    logger.info(f"Sent 'No events' embed to {user.name} ({user.id}).")
                else:
                    logger.error(f"User with ID {user_id} not found.")
                return
            
            # Create embed with tasks
            embed = Embed(title="Today's Tasks", color=0x3498db)

            # Add each task as a field in the embed
            for idx, event in enumerate(tasks, start=1):
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'No Title')
                embed.add_field(name=f"{idx}. {summary}", value=start, inline=False)

            # Create the View with 'Done' buttons
            view = TaskDoneView(tasks)

            # Fetch user and send
            user = await bot.fetch_user(int(user_id))
            if user is None:
                logger.error(f"User with ID {user_id} not found.")
                return
            await user.send(embed=embed, view=view)
            logger.info(f"Embed with 'Done' buttons sent to {user.name} ({user.id}).")
        except discord.Forbidden:
            logger.error(f"Could not send DM to user {user_id}. They might have DMs disabled.")
        except Exception as e:
            logger.error(f"Error sending embed to user {user_id}: {e}")
    
    # Schedule the async task
    bot.loop.create_task(send_calendar_task())
    
    return jsonify({'status': 'Embed with buttons sent'}), 200

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
            tasks = calendar.get_cal()  # Should return list of event dicts
            if not tasks:
                embed = Embed(title="Today's Tasks", description="No upcoming events found for today.", color=0x3498db)
                user = await bot.fetch_user(int(user_id))
                if user:
                    await user.send(embed=embed)
                    logger.info(f"Sent 'No events' embed to {user.name} ({user.id}).")
                else:
                    logger.error(f"User with ID {user_id} not found.")
                return
            
            # Create embed with tasks
            embed = Embed(title="Today's Tasks", color=0x3498db)
            readable_time = "%B %d, %Y at %I:%M %p %Z"
            for idx, event in enumerate(tasks, start=1):
                start = event['start'].get('dateTime', event['start'].get('date'))
                parsed_datetime = datetime.fromisoformat(start)
                readable_datetime = parsed_datetime.strftime(readable_time)
                summary = event.get('summary')
                embed.add_field(name=f"{idx}. {summary}", value=readable_datetime, inline=False)

            # Create the View with 'Done' buttons
            view = TaskDoneView(tasks)

            # Fetch user and send
            user = await bot.fetch_user(int(user_id))
            if user is None:
                logger.error(f"User with ID {user_id} not found.")
                return
            await user.send(embed=embed, view=view)
            logger.info(f"Sent calendar data to {user.name} ({user.id}).")
        except discord.Forbidden:
            logger.error(f"Could not send DM to user {user_id}. They might have DMs disabled.")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    bot.loop.create_task(send_dm())
    return jsonify({"status": "Message sent"}), 200

# Function to Send Modal to User
async def send_modal_to_user(user_id):
    try:
        user = await bot.fetch_user(user_id)  # Fetch the user by ID
        if not user:
            logger.error(f"User with ID {user_id} not found.")
            return
        view = View()  # Create a view to hold the button

        # Define and add the button
        button = Button(label="Open Modal", style=discord.ButtonStyle.primary, custom_id="open_modal_button")

        # Button callback
        async def button_callback(interaction: discord.Interaction):
            modal = MyModal()  # Create the modal instance
            await interaction.response.send_modal(modal)  # Send the modal

        button.callback = button_callback  # Attach the callback to the button
        view.add_item(button)  # Add the button to the view

        # Send a DM with the button
        await user.send("Click the button below to open the modal:", view=view)
        logger.info(f"Modal button sent to {user.name} ({user.id}).")
    except discord.Forbidden:
        logger.error(f"Could not send DM to user {user_id}. They might have DMs disabled.")
    except Exception as e:
        logger.error(f"Error in sending modal: {e}")

# Bot ready event
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    # No need to register TaskDoneView globally since it's dynamic per message

# Flask thread to run Flask app in parallel with the bot
class FlaskThread(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.server = make_server("127.0.0.1", 8080, app)
        self.ctx = app.app_context()

    def run(self):
        with self.ctx:
            self.server.serve_forever()

# Start Flask app in a thread
flask_thread = FlaskThread(app)
flask_thread.start()
logger.debug(f"Flask server started on http://127.0.0.1:8080")

# Run the bot
bot.run(DISCORD_KEY)
