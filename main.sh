#!/bin/bash

# Colors for UI
GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"
CYAN="\e[36m"
RESET="\e[0m"

while true; do
    clear
    echo -e "${CYAN}================================"
    echo "         TIX HOSTING"
    echo -e "================================${RESET}"
    echo "1) Create a Python file"
    echo "2) Run an existing Python file"
    echo "3) Install Discord Bot requirements"
    echo "4) Exit"
    echo -n -e "${YELLOW}Enter choice: ${RESET}"
    read choice

    case $choice in
        1)
            echo -n "Enter new file name (without .py): "
            read filename
            filepath="${filename}.py"

            if [ ! -f "$filepath" ]; then
                echo -n "Do you want a sample bot template? (y/n): "
                read template_choice

                if [[ "$template_choice" == "y" || "$template_choice" == "Y" ]]; then
                    cat > "$filepath" <<EOL
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# Replace 'YOUR_TOKEN_HERE' with your bot token
bot.run("YOUR_TOKEN_HERE")
EOL
                    echo -e "${GREEN}Sample bot template created in $filepath${RESET}"
                else
                    echo "# Write your Discord bot code here" > "$filepath"
                    echo -e "${YELLOW}Empty file $filepath created.${RESET}"
                fi
            fi

            nano "$filepath"

            echo -e "${YELLOW}Running $filepath ...${RESET}"
            python "$filepath" || echo -e "${RED}Error: Your code crashed.${RESET}"
            read -p "Press Enter to return to menu..."
            ;;
        2)
            echo -n "Enter existing file name (without .py): "
            read filename
            filepath="${filename}.py"

            if [ -f "$filepath" ]; then
                echo -e "${YELLOW}Running $filepath ...${RESET}"
                python "$filepath" || echo -e "${RED}Error: Your code crashed.${RESET}"
            else
                echo -e "${RED}File not found!${RESET}"
            fi
            read -p "Press Enter to return to menu..."
            ;;
        3)
            echo -e "${YELLOW}Installing Discord Bot requirements...${RESET}"
            pip install -U pip
            pip install -U discord.py
            echo -e "${GREEN}Installation complete!${RESET}"
            read -p "Press Enter to return to menu..."
            ;;
        4)
            echo -e "${GREEN}Exiting TIX HOSTING... Goodbye!${RESET}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice!${RESET}"
            sleep 1
            ;;
    esac
done