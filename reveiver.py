import argparse
import uuid
from pathlib import Path
from threading import Event
from email import policy
from email.parser import BytesParser

from aiosmtpd.controller import Controller


class SMTPHandler:
    async def handle_DATA(self, server, session, envelope):
       
        folder = Path("received_emails")
        folder.mkdir(exist_ok=True)

        filepath = folder / f"{uuid.uuid4().hex}.eml"

        try:
            filepath.write_bytes(envelope.original_content)
        except OSError as error:
            print(f"Could not save email: {error}", flush=True)
            return "451 Could not save email"

        message = BytesParser(
            policy=policy.default
        ).parsebytes(envelope.original_content)

        body = message.get_body(preferencelist=("plain",))
        print("\n========== NEW EMAIL ==========")
        print("From:", envelope.mail_from)
        print("To:", ", ".join(envelope.rcpt_tos))
        print("Subject:", message.get("Subject", ""))
        print("\nMessage:")

        if body is not None:
            print(body.get_content())
        else:
            print("[No plain-text body]")

        print("Saved:", filepath.resolve())
        print("===============================\n", flush=True)

        return "250 Message accepted"


def main():
    parser = argparse.ArgumentParser(
        description="Receive emails and display them in the terminal."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Local IP address to listen on; defaults to localhost",
    )
    parser.add_argument("--port", type=int, default=1025)
    args = parser.parse_args()

    controller = Controller(
        SMTPHandler(),
        hostname=args.host,
        port=args.port,
        data_size_limit=1024 * 1024,
    )

    controller.start()

    print(f"SMTP server listening on {args.host}:{args.port}")
    print("Waiting for emails... Press Ctrl+C to stop.", flush=True)

    try:
        Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        print("\nSMTP server stopped.")


if __name__ == "__main__":
    main()
