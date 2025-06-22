import os
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram import idle

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
bot_token = os.environ["BOT_TOKEN"]
session_name = "my_bot"

ADMIN_ID = 664193835  # معرف المدير @Doc_HEMA

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users_data = load_data()

async def send_scheduled_messages(app: Client):
    while True:
        for user_id, user_info in users_data.items():
            for group_id, group_info in user_info.get("groups", {}).items():
                if not group_info["messages"]:
                    continue
                msg = group_info["messages"][group_info["msg_index"] % len(group_info["messages"])]
                try:
                    await app.send_message(int(group_id), msg)
                except Exception as e:
                    print(f"Error sending to {group_id}: {e}")
                group_info["msg_index"] += 1
        save_data(users_data)
        await asyncio.sleep(10)

app = Client(session_name, api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("add_user") & filters.user(ADMIN_ID))
async def add_user_handler(client, message: Message):
    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
        if str(user_id) not in users_data:
            users_data[str(user_id)] = {"groups": {}}
            save_data(users_data)
            await message.reply(f"تمت إضافة المستخدم {user_id}.")
        else:
            await message.reply("المستخدم موجود بالفعل.")
    except Exception as e:
        await message.reply("الاستخدام: /add_user user_id\n" + str(e))

@app.on_message(filters.command("add_group"))
async def add_group_handler(client, message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        await message.reply("ليس لديك صلاحية استخدام البوت. اطلب من المدير إضافتك.")
        return
    try:
        _, group_id, interval = message.text.split()
        group_id = int(group_id)
        interval = int(interval)
        users_data[user_id]["groups"][str(group_id)] = {"messages": [], "interval": interval, "msg_index": 0}
        save_data(users_data)
        await message.reply(f"تمت إضافة المجموعة {group_id}.")
    except Exception as e:
        await message.reply("الاستخدام: /add_group group_id interval\n" + str(e))

@app.on_message(filters.command("add_msg"))
async def add_msg_handler(client, message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        await message.reply("ليس لديك صلاحية استخدام البوت.")
        return
    try:
        _, group_id, *msg = message.text.split()
        group_id = str(int(group_id))
        msg = " ".join(msg)
        users_data[user_id]["groups"][group_id]["messages"].append(msg)
        save_data(users_data)
        await message.reply(f"تمت إضافة الرسالة للمجموعة {group_id}.")
    except Exception as e:
        await message.reply("الاستخدام: /add_msg group_id الرسالة\n" + str(e))

@app.on_message(filters.command("list"))
async def list_handler(client, message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        await message.reply("ليس لديك صلاحية استخدام البوت.")
        return
    text = ""
    for group_id, group_info in users_data[user_id]["groups"].items():
        text += f"Group {group_id} (كل {group_info['interval']}ث):\n"
        for i, m in enumerate(group_info["messages"]):
            text += f"  {i+1}- {m}\n"
    await message.reply(text or "لا توجد مجموعات.")

async def main():
    await app.start()
    asyncio.create_task(send_scheduled_messages(app))
    print("Bot is running...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())