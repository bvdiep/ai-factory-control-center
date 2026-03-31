import os
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from fasthtml.common import *
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.models import BridgeMessage, BridgeMessageFile, Project
from app.services.telegram_service import send_message, get_file_url, TELEGRAM_API_URL, TELEGRAM_BOT_TOKEN
from app.services.dify_service import send_chat_message
from app.services.llm_service import extract_image_description


async def download_and_save_file(file_id: str, file_type: str, original_name: str = None) -> str | None:
    """
    Download a file from Telegram and save it to MEDIA_UPLOAD_PATH.
    Returns the local file path, or None on failure.
    """
    try:
        # Get Telegram file path
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TELEGRAM_API_URL}/getFile",
                json={"file_id": file_id}
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                return None
            tg_file_path: str = data["result"]["file_path"]

        # Build download URL
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{tg_file_path}"

        # Determine local save path
        ext = Path(tg_file_path).suffix or ""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        save_dir = Path(settings.MEDIA_UPLOAD_PATH) / date_str
        save_dir.mkdir(parents=True, exist_ok=True)
        local_filename = f"{file_id}{ext}"
        local_path = save_dir / local_filename

        # Download and write file
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url)
            response.raise_for_status()
            local_path.write_bytes(response.content)

        return str(local_path)

    except Exception as e:
        print(f"[TelegramRouter] Error downloading file {file_id}: {e}")
        return None


async def process_telegram_message(message: dict):
    chat_id = message["chat"]["id"]

    with Session(engine) as session:
        project = session.exec(select(Project)).first()
        project_id = project.id if project else None

        # ─── Text message ────────────────────────────────────────────────
        if "text" in message:
            text = message["text"]

            db_msg = BridgeMessage(
                project_id=project_id,
                sender="telegram",
                message_type="text",
                content=text
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            dify_response = await send_chat_message(text, str(chat_id))
            if dify_response and "answer" in dify_response:
                answer = dify_response["answer"]
                dify_msg = BridgeMessage(
                    project_id=project_id,
                    sender="dify",
                    message_type="text",
                    content=answer
                )
                session.add(dify_msg)
                session.commit()
                await send_message(chat_id, answer)

        # ─── Photo message ───────────────────────────────────────────────
        elif "photo" in message:
            photo = message["photo"][-1]  # highest resolution
            file_id = photo["file_id"]
            caption = message.get("caption", "")

            db_msg = BridgeMessage(
                project_id=project_id,
                sender="telegram",
                message_type="image",
                content=caption or file_id,
                extracted_data=caption
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            # Download & save file
            local_path = await download_and_save_file(file_id, "image")
            if local_path:
                db_file = BridgeMessageFile(
                    message_id=db_msg.id,
                    file_type="image",
                    file_path=local_path,
                    telegram_file_id=file_id
                )
                session.add(db_file)
                session.commit()

            # Extract description using VLM
            file_url = await get_file_url(file_id)
            if file_url:
                description = await extract_image_description(file_url)
                if description:
                    db_msg.extracted_data = f"Caption: {caption}\nDescription: {description}"
                    session.add(db_msg)
                    session.commit()

                    query = f"I sent an image. Description: {description}"
                    if caption:
                        query += f"\nCaption: {caption}"

                    dify_response = await send_chat_message(query, str(chat_id))
                    if dify_response and "answer" in dify_response:
                        answer = dify_response["answer"]
                        dify_msg = BridgeMessage(
                            project_id=project_id,
                            sender="dify",
                            message_type="text",
                            content=answer
                        )
                        session.add(dify_msg)
                        session.commit()
                        await send_message(chat_id, answer)

        # ─── Document message ────────────────────────────────────────────
        elif "document" in message:
            doc = message["document"]
            file_id = doc["file_id"]
            original_name = doc.get("file_name")
            caption = message.get("caption", "")

            db_msg = BridgeMessage(
                project_id=project_id,
                sender="telegram",
                message_type="document",
                content=original_name or file_id,
                extracted_data=caption or None
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            local_path = await download_and_save_file(file_id, "document", original_name)
            if local_path:
                db_file = BridgeMessageFile(
                    message_id=db_msg.id,
                    file_type="document",
                    original_name=original_name,
                    file_path=local_path,
                    telegram_file_id=file_id
                )
                session.add(db_file)
                session.commit()

        # ─── Audio message ───────────────────────────────────────────────
        elif "audio" in message:
            audio = message["audio"]
            file_id = audio["file_id"]
            original_name = audio.get("file_name")

            db_msg = BridgeMessage(
                project_id=project_id,
                sender="telegram",
                message_type="audio",
                content=original_name or file_id
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            local_path = await download_and_save_file(file_id, "audio", original_name)
            if local_path:
                db_file = BridgeMessageFile(
                    message_id=db_msg.id,
                    file_type="audio",
                    original_name=original_name,
                    file_path=local_path,
                    telegram_file_id=file_id
                )
                session.add(db_file)
                session.commit()

        # ─── Voice message ───────────────────────────────────────────────
        elif "voice" in message:
            voice = message["voice"]
            file_id = voice["file_id"]

            db_msg = BridgeMessage(
                project_id=project_id,
                sender="telegram",
                message_type="audio",
                content=file_id
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            local_path = await download_and_save_file(file_id, "audio")
            if local_path:
                db_file = BridgeMessageFile(
                    message_id=db_msg.id,
                    file_type="audio",
                    file_path=local_path,
                    telegram_file_id=file_id
                )
                session.add(db_file)
                session.commit()

        # ─── Video message ───────────────────────────────────────────────
        elif "video" in message:
            video = message["video"]
            file_id = video["file_id"]
            original_name = video.get("file_name")

            db_msg = BridgeMessage(
                project_id=project_id,
                sender="telegram",
                message_type="video",
                content=original_name or file_id
            )
            session.add(db_msg)
            session.commit()
            session.refresh(db_msg)

            local_path = await download_and_save_file(file_id, "video", original_name)
            if local_path:
                db_file = BridgeMessageFile(
                    message_id=db_msg.id,
                    file_type="video",
                    original_name=original_name,
                    file_path=local_path,
                    telegram_file_id=file_id
                )
                session.add(db_file)
                session.commit()


async def poll_telegram_updates():
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not set. Telegram polling disabled.")
        return

    print("Starting Telegram polling...")
    offset = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                url = f"{TELEGRAM_API_URL}/getUpdates"
                response = await client.get(url, params={"offset": offset, "timeout": 30})
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        for update in data.get("result", []):
                            offset = update["update_id"] + 1
                            if "message" in update:
                                await process_telegram_message(update["message"])
            except Exception as e:
                print(f"Telegram polling error: {e}")

            await asyncio.sleep(1)


def setup_telegram_routes(rt):
    @rt('/webhook/telegram', methods=['POST'])
    async def telegram_webhook(request: Request):
        data = await request.json()

        if "message" in data:
            asyncio.create_task(process_telegram_message(data["message"]))

        return {"status": "ok"}
