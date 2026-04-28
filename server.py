import csv
import io
import json
import mimetypes
import os
import secrets
from datetime import datetime
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from openpyxl import Workbook


APP_DIR = Path(__file__).resolve().parent
STORAGE_ROOT = Path(os.environ.get("TRADE_JOURNAL_HOME", APP_DIR)).resolve()
PUBLIC_DIR = APP_DIR / "public"
DATA_DIR = STORAGE_ROOT / "data"
DATA_FILE = DATA_DIR / "trades.json"
UPLOAD_DIR = STORAGE_ROOT / "uploads"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "3000"))
MAX_REQUEST_BYTES = 12 * 1024 * 1024
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

EXPORT_COLUMNS = [
    ("id", "ID"),
    ("tradeDate", "Trade Date"),
    ("createdAt", "Saved At"),
    ("instrument", "Instrument"),
    ("account", "Account"),
    ("direction", "Direction"),
    ("setupType", "Setup Type"),
    ("timeframe", "Timeframe"),
    ("entryPrice", "Entry Price"),
    ("stopLoss", "Stop Loss"),
    ("takeProfit", "Take Profit"),
    ("contracts", "Contracts"),
    ("result", "Result"),
    ("outcome", "Outcome"),
    ("rrRatio", "RR Ratio"),
    ("emotion", "Emotion"),
    ("mistakeCategory", "Mistake Category"),
    ("screenshotFilename", "Screenshot File"),
    ("screenshotPath", "Screenshot Path"),
    ("notes", "Notes"),
]


def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def read_trades():
    ensure_storage()
    try:
        content = DATA_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def write_trades(trades):
    ensure_storage()
    DATA_FILE.write_text(json.dumps(trades, indent=2), encoding="utf-8")


def clean_value(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return value


def get_screenshot_path(trade):
    return clean_value(trade.get("screenshotPath")) or clean_value(trade.get("screenshotLink"))


def get_screenshot_filename(trade):
    return clean_value(trade.get("screenshotFilename"))


def normalize_trade(payload, screenshot_info=None):
    now = datetime.utcnow()
    created_at = now.isoformat(timespec="seconds") + "Z"
    trade_date = clean_value(payload.get("tradeDate")) or now.strftime("%Y-%m-%d")
    screenshot_path = screenshot_info["path"] if screenshot_info else clean_value(payload.get("screenshotPath"))
    screenshot_name = screenshot_info["filename"] if screenshot_info else clean_value(payload.get("screenshotFilename"))

    return {
        "id": f"trade_{int(now.timestamp() * 1000)}_{secrets.token_hex(3)}",
        "tradeDate": trade_date,
        "createdAt": created_at,
        "instrument": clean_value(payload.get("instrument")),
        "account": clean_value(payload.get("account")),
        "direction": clean_value(payload.get("direction")),
        "setupType": clean_value(payload.get("setupType")),
        "timeframe": clean_value(payload.get("timeframe")),
        "entryPrice": clean_value(payload.get("entryPrice")),
        "stopLoss": clean_value(payload.get("stopLoss")),
        "takeProfit": clean_value(payload.get("takeProfit")),
        "contracts": clean_value(payload.get("contracts")),
        "result": clean_value(payload.get("result")),
        "outcome": clean_value(payload.get("outcome")),
        "rrRatio": clean_value(payload.get("rrRatio")),
        "emotion": clean_value(payload.get("emotion")),
        "mistakeCategory": clean_value(payload.get("mistakeCategory")),
        "screenshotFilename": screenshot_name,
        "screenshotPath": screenshot_path,
        "notes": clean_value(payload.get("notes")),
    }


def sort_trades(trades):
    return sorted(trades, key=lambda trade: trade.get("createdAt", ""), reverse=True)


def export_rows(trades):
    rows = []
    for trade in trades:
        row = {}
        for key, label in EXPORT_COLUMNS:
            if key == "screenshotPath":
                row[label] = get_screenshot_path(trade)
            elif key == "screenshotFilename":
                row[label] = get_screenshot_filename(trade)
            else:
                row[label] = trade.get(key, "")
        rows.append(row)
    return rows


def extension_for_upload(content_type, filename):
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return suffix

    guesses = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    guessed = guesses.get(content_type, "")
    if guessed in ALLOWED_EXTENSIONS:
        return guessed
    return ""


def save_uploaded_image(upload):
    content_type = clean_value(upload.get("content_type"))
    filename = clean_value(upload.get("filename"))
    data = upload.get("data") or b""

    if not content_type.startswith("image/"):
        raise ValueError("Only image uploads are allowed.")

    extension = extension_for_upload(content_type, filename)
    if not extension:
        raise ValueError("Unsupported image format.")

    stored_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(6)}{extension}"
    target = UPLOAD_DIR / stored_name
    target.write_bytes(data)

    return {
        "filename": Path(filename).name or stored_name,
        "path": f"/uploads/{stored_name}",
    }


def delete_uploaded_image(trade):
    screenshot_path = get_screenshot_path(trade)
    if not screenshot_path.startswith("/uploads/"):
        return

    target = (UPLOAD_DIR / Path(screenshot_path).name).resolve()
    try:
        target.relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        return

    if target.exists():
        try:
            target.unlink()
        except OSError:
            return


def parse_multipart_form(body, content_type):
    header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
    message = BytesParser(policy=default).parsebytes(header + body)
    fields = {}
    upload = None

    if not message.is_multipart():
        return fields, upload

    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue

        name = part.get_param("name", header="content-disposition")
        if not name:
            continue

        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""

        if filename:
            if name == "screenshotFile" and payload:
                upload = {
                    "filename": filename,
                    "content_type": part.get_content_type(),
                    "data": payload,
                }
            continue

        charset = part.get_content_charset() or "utf-8"
        fields[name] = payload.decode(charset, errors="ignore")

    return fields, upload


def parse_body(body, content_type):
    normalized = clean_value(content_type).lower()

    if normalized.startswith("application/json"):
        payload = json.loads(body.decode("utf-8") or "{}")
        return payload, None

    if normalized.startswith("multipart/form-data"):
        return parse_multipart_form(body, content_type)

    if normalized.startswith("application/x-www-form-urlencoded"):
        parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
        return {key: values[-1] if values else "" for key, values in parsed.items()}, None

    raise ValueError("Unsupported content type.")


class TradeJournalHandler(BaseHTTPRequestHandler):
    server_version = "TradeJournal/2.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/trades":
            self.handle_get_trades()
            return
        if path == "/api/export.csv":
            self.handle_export_csv()
            return
        if path == "/api/export.xlsx":
            self.handle_export_xlsx()
            return
        if path.startswith("/uploads/"):
            self.serve_file(path, UPLOAD_DIR)
            return

        self.serve_file(path, PUBLIC_DIR, default_file="index.html")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/trades":
            self.handle_create_trade()
            return
        self.send_json({"message": "Not found."}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        prefix = "/api/trades/"
        if parsed.path.startswith(prefix):
            trade_id = unquote(parsed.path[len(prefix):])
            self.handle_delete_trade(trade_id)
            return
        self.send_json({"message": "Not found."}, HTTPStatus.NOT_FOUND)

    def handle_get_trades(self):
        trades = sort_trades(read_trades())
        self.send_json(trades)

    def handle_create_trade(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0

        if content_length > MAX_REQUEST_BYTES:
            self.send_json({"message": "Upload is too large."}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return

        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        try:
            payload, upload = parse_body(body, content_type)
        except json.JSONDecodeError:
            self.send_json({"message": "Invalid JSON."}, HTTPStatus.BAD_REQUEST)
            return
        except ValueError as error:
            self.send_json({"message": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        screenshot_info = None
        if upload:
            try:
                screenshot_info = save_uploaded_image(upload)
            except ValueError as error:
                self.send_json({"message": str(error)}, HTTPStatus.BAD_REQUEST)
                return

        trade = normalize_trade(payload, screenshot_info)
        trades = read_trades()
        trades.insert(0, trade)
        write_trades(trades)
        self.send_json(trade, HTTPStatus.CREATED)

    def handle_delete_trade(self, trade_id):
        trades = read_trades()
        removed_trade = next((trade for trade in trades if trade.get("id") == trade_id), None)

        if not removed_trade:
            self.send_json({"message": "Trade not found."}, HTTPStatus.NOT_FOUND)
            return

        next_trades = [trade for trade in trades if trade.get("id") != trade_id]
        delete_uploaded_image(removed_trade)
        write_trades(next_trades)
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def handle_export_csv(self):
        rows = export_rows(sort_trades(read_trades()))
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[label for _, label in EXPORT_COLUMNS])
        writer.writeheader()
        writer.writerows(rows)

        content = output.getvalue().encode("utf-8")
        filename = f'trade-journal-{datetime.utcnow().strftime("%Y-%m-%d")}.csv'
        self.send_bytes(content, "text/csv; charset=utf-8", filename)

    def handle_export_xlsx(self):
        rows = export_rows(sort_trades(read_trades()))
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Trades"
        worksheet.append([label for _, label in EXPORT_COLUMNS])

        for row in rows:
            worksheet.append([row.get(label, "") for _, label in EXPORT_COLUMNS])

        buffer = io.BytesIO()
        workbook.save(buffer)
        filename = f'trade-journal-{datetime.utcnow().strftime("%Y-%m-%d")}.xlsx'
        self.send_bytes(
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename,
        )

    def serve_file(self, path, root_dir, default_file=None):
        relative = default_file if path in ("", "/") and default_file else path.lstrip("/")
        target = (root_dir / relative).resolve()

        try:
            target.relative_to(root_dir.resolve())
        except ValueError:
            self.send_json({"message": "Not found."}, HTTPStatus.NOT_FOUND)
            return

        if not target.exists() or not target.is_file():
            self.send_json({"message": "Not found."}, HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(target))
        self.send_bytes(target.read_bytes(), content_type or "application/octet-stream")

    def send_json(self, payload, status=HTTPStatus.OK):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_bytes(self, content, content_type, filename=None):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        return


if __name__ == "__main__":
    ensure_storage()
    server = ThreadingHTTPServer((HOST, PORT), TradeJournalHandler)
    print(f"Trade journal running at http://{HOST}:{PORT}")
    print(f"Storage root: {STORAGE_ROOT}")
    server.serve_forever()
