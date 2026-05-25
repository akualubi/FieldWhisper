"""
穗安 AI 邮件转发服务
启动: python email_server.py
监听: http://127.0.0.1:5001
前端通过 POST /send-email 触发预警邮件
"""
from __future__ import annotations

from flask import Flask, request, jsonify
from flask_cors import CORS

import send_test_email as mail

app = Flask(__name__)
CORS(app)

settings = mail.load_settings()


@app.route("/send-email", methods=["POST"])
def send():
    data = request.get_json(force=True)
    to = data.get("to", settings.smtp_user)
    subject = data.get("subject", "【穗安】预警提示")
    body = data.get("body", "")
    try:
        mail.send_email(settings=settings, to_email=to, subject=subject, body=body)
        print(f"[穗安邮件] 已发送 → {to} | {subject}")
        return jsonify({"ok": True})
    except Exception as exc:
        print(f"[穗安邮件] 发送失败: {exc}")
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    print("穗安邮件服务启动 → http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)
