import os
import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup
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
                    # تنبيه المدير
                    try:
                        await app.send_message(ADMIN_ID, f"خطأ في الإرسال للمجموعة {group_id}: {e}")
                    except:
                        pass
                group_info["msg_index"] += 1
        save_data(users_data)
        await asyncio.sleep(10)

app = Client(session_name, api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("add_user"))
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
    text = ""
    for group_id, group_info in users_data.get(user_id, {}).get("groups", {}).items():
        text += f"Group {group_id} (كل {group_info['interval']}ث):\n"
        for i, m in enumerate(group_info["messages"]):
            text += f"  {i+1}- {m}\n"
    await message.reply(text or "لا توجد مجموعات.")

@app.on_message(filters.command("help"))
async def help_handler(client, message: Message):
    help_text = (
        "\n".join([
            "\u2022 /add_user user_id — إضافة مستخدم جديد.",
            "/remove_user user_id — حذف مستخدم من الصلاحيات.",
            "/add_group group_id interval — إضافة مجموعة مع فترة الإرسال بالثواني.",
            "/remove_group group_id — حذف مجموعة من المستخدم.",
            "/add_msg group_id الرسالة — إضافة رسالة لمجموعة.",
            "/remove_msg group_id رقم_الرسالة — حذف رسالة من مجموعة.",
            "/list — عرض المجموعات والرسائل.",
            "/help — عرض هذه الرسالة."
        ])
    )
    keyboard = ReplyKeyboardMarkup([
        ["/add_user", "/remove_user"],
        ["/add_group", "/remove_group"],
        ["/add_msg", "/remove_msg"],
        ["/list", "/help"]
    ], resize_keyboard=True)
    await message.reply(help_text, reply_markup=keyboard)

@app.on_message(filters.command("remove_user"))
async def remove_user_handler(client, message: Message):
    try:
        _, user_id = message.text.split()
        user_id = str(int(user_id))
        if user_id in users_data:
            del users_data[user_id]
            save_data(users_data)
            await message.reply(f"تم حذف المستخدم {user_id} من الصلاحيات.")
        else:
            await message.reply("المستخدم غير موجود.")
    except Exception as e:
        await message.reply("الاستخدام: /remove_user user_id\n" + str(e))

@app.on_message(filters.command("remove_group"))
async def remove_group_handler(client, message: Message):
    user_id = str(message.from_user.id)
    try:
        _, group_id = message.text.split()
        group_id = str(int(group_id))
        if group_id in users_data.get(user_id, {}).get("groups", {}):
            del users_data[user_id]["groups"][group_id]
            save_data(users_data)
            await message.reply(f"تم حذف المجموعة {group_id}.")
        else:
            await message.reply("المجموعة غير موجودة.")
    except Exception as e:
        await message.reply("الاستخدام: /remove_group group_id\n" + str(e))

@app.on_message(filters.command("remove_msg"))
async def remove_msg_handler(client, message: Message):
    user_id = str(message.from_user.id)
    try:
        _, group_id, msg_index = message.text.split()
        group_id = str(int(group_id))
        msg_index = int(msg_index) - 1
        if group_id in users_data.get(user_id, {}).get("groups", {}):
            messages = users_data[user_id]["groups"][group_id]["messages"]
            if 0 <= msg_index < len(messages):
                removed = messages.pop(msg_index)
                save_data(users_data)
                await message.reply(f"تم حذف الرسالة: {removed}")
            else:
                await message.reply("رقم الرسالة غير صحيح.")
        else:
            await message.reply("المجموعة غير موجودة.")
    except Exception as e:
        await message.reply("الاستخدام: /remove_msg group_id رقم_الرسالة\n" + str(e))

async def main():
    await app.start()
    asyncio.create_task(send_scheduled_messages(app))
    print("Bot is running...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())