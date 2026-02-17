#!/usr/bin/env python3
"""frederick-matrix unified management CLI.

Usage:
    ./manage.py setup
    ./manage.py up
    ./manage.py down
    ./manage.py status [docker|localhost|tunnel|pages] [-q]
    ./manage.py tunnel restart
    ./manage.py tunnel url
    ./manage.py publish
    ./manage.py token create [--uses N] [--expires 7d]
    ./manage.py token list [--active]
    ./manage.py token revoke <token>
    ./manage.py token configure [--server URL] [--element URL] [--token TOKEN]
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # setup
    sub.add_parser("setup", help="Full first-time setup")

    # up
    sub.add_parser("up", help="Start services, publish tunnel URL, watch for changes")

    # down
    sub.add_parser("down", help="Stop all services")

    # status
    p_status = sub.add_parser("status", help="Check system health")
    p_status.add_argument(
        "section",
        nargs="?",
        choices=["docker", "localhost", "tunnel", "pages"],
        help="Section to check (default: all)",
    )
    p_status.add_argument("-q", "--quiet", action="store_true", help="Summary only")

    # tunnel
    p_tunnel = sub.add_parser("tunnel", help="Tunnel management")
    tunnel_sub = p_tunnel.add_subparsers(dest="tunnel_cmd", metavar="<subcommand>")
    tunnel_sub.add_parser("restart", help="Force-recreate cloudflared, wait, publish")
    tunnel_sub.add_parser("url", help="Print and check current tunnel URL")

    # publish
    sub.add_parser("publish", help="One-shot: publish current tunnel URL to GitHub Pages")

    # token
    p_token = sub.add_parser("token", help="Registration token management")
    token_sub = p_token.add_subparsers(dest="token_cmd", metavar="<subcommand>")

    p_create = token_sub.add_parser("create", help="Create a registration token")
    p_create.add_argument("--uses", type=int, help="Number of uses (0 = unlimited, default: 1)")
    p_create.add_argument("--expires", help="Expiry duration (e.g. 1h, 7d, 4w)")

    p_list = token_sub.add_parser("list", help="List registration tokens")
    p_list.add_argument("--active", action="store_true", help="Only show active tokens")

    p_revoke = token_sub.add_parser("revoke", help="Revoke a registration token")
    p_revoke.add_argument("token_value", metavar="token", help="Token to revoke")

    p_configure = token_sub.add_parser("configure", help="Set up admin credentials")
    p_configure.add_argument("--server", help="Synapse server URL")
    p_configure.add_argument("--element", help="Element Web URL")
    p_configure.add_argument("--token", dest="token_value", help="Admin access token")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "setup":
        from manage.setup import cmd_setup
        cmd_setup(args)

    elif args.command == "up":
        from manage.compose import cmd_up
        cmd_up(args)

    elif args.command == "down":
        from manage.compose import cmd_down
        cmd_down(args)

    elif args.command == "status":
        from manage.status import cmd_status
        cmd_status(args)

    elif args.command == "tunnel":
        if not args.tunnel_cmd:
            p_tunnel.print_help()
            sys.exit(1)
        from manage.tunnel import cmd_tunnel
        cmd_tunnel(args)

    elif args.command == "publish":
        from manage.tunnel import cmd_publish
        cmd_publish(args)

    elif args.command == "token":
        if not args.token_cmd:
            p_token.print_help()
            sys.exit(1)
        from manage.tokens import cmd_token
        cmd_token(args)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
