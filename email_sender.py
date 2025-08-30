"""
title: Email Sender
author: Sandmeyer <sandm_x@outlook.com>
description: This tool provides your LLM with the ability to send emails
version: 0.1.0
licence: MIT
"""
from pydantic import BaseModel, Field
from typing import List, Callable, Any
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib


async def confirm(
        sender: str,
        subject: str, 
        content: str, 
        recipient: str,
        event_emitter: Callable[[dict], Any] = lambda x: None,
        event_call: Callable[[dict], Any] = lambda x: False
    ) -> bool:
    """
    Ask the user to confirm the action before sending the email.

    Note: 
        This is a private function, do not directly call it. It should be called by `send_imail` function.

    Args:
        __event_emitter__ (Callable[[dict], Any]): Function to emit events.
        __event_call__ (Callable[[dict], Any]): Function to call events.

    Returns:
        bool: Confirmation status.
    """
    # 最多只展示前30个字的内容
    show_content = content[:30] + "..."
    confirm = await event_call({
        "type": "confirmation",
        "data": {
            "title": f"Confirm Email Sender Operation",
            "message": f"Do you confirm to send this email?\nSubject: {subject}\nTo {recipient},\n{show_content}\n{sender}"
        }
    })

    if not confirm:
        await event_emitter({
            "type": "notification",
            "data": {"type": "warning", "content": "User cancelled."}
        })
            
        return False
        
    await event_emitter({
        "type": "notification",
        "data": {"type": "success", "content": "User confirmed operation."}
    })

    return True

class Tools:
    class Valves(BaseModel):
        sender: str = Field(
            default="robot@mail.com",
            description="The email address of the sender",
        )
        sender_key: str = Field(
            default="xxxxxxxx",
            description="The email authorization code of the sender",
        )
        recipient: str = Field(
            default="sandm@nice.guy",
            description="The email address of the recipient",
        )
        pass

    def __init__(self):
        self.valves = self.Valves()

    async def send_email(self, subject: str, content: str, recipient: str | None = None,
                        __event_emitter__: Callable[[dict], Any] = lambda x: None,
                        __event_call__: Callable[[dict], Any] = lambda x: False
                        ) -> str:
        """
        Send an email with automated user confirmation
        Trigger this function whenever an email needs to be sent.  

        Args:
            subject (str): The subject of the email.
            content (str): The content of the email.
            recipient (str, optional): The email address of the recipient. If not provided, uses the default value.

        Returns:
            str: Status of the email sending operation.
        """
        if recipient:
            self.valves.recipient = recipient

        # Confirm with the user before sending the email
        confirm_status = await confirm(
            sender=self.valves.sender,
            recipient=self.valves.recipient,
            content=content,
            subject=subject,
            event_emitter=__event_emitter__,
            event_call=__event_call__,
        )

        if not confirm_status:
            return "Email sending cancelled by user, operation aborted"
        
        try:
            msg = MIMEText(content, 'plain', 'utf-8')  
            msg['From'] = formataddr(("Sender", self.valves.sender)) 
            msg['To'] = formataddr(("Recipient", self.valves.recipient))  
            msg['Subject'] = subject  

            server = smtplib.SMTP_SSL("smtp.qq.com", 465)  
            server.login(self.valves.sender, self.valves.sender_key)  # 括号中对应的是发件人邮箱账号、邮箱授权码
            server.sendmail(self.valves.sender, [self.valves.recipient, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.quit() 
        except Exception as e: 
            return "Failed to send email, error: {}".format(e)

        return "Email sent successfully"
