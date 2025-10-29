"""Manage the production environment. Install, remove and push package to production."""

from rez.command import Command


command_behavior = {
    "hidden": False,  # optional: bool
    "arg_mode": None,  # optional: None, "passthrough", "grouped"
}


def _confirm_action(action: str, packages: list[str], force_flag: bool = False) -> bool:
    """Prompts the user for confirmation before performing an action on specified packages, unless the force flag is set. Returns a boolean indicating approval status.

    Args:
        action (str): The action to confirm (e.g., install, remove).
        packages (list[str]): List of package names involved in the action.
        force_flag (bool): If True, skips confirmation and approves the action automatically. Defaults to False.

    Returns:
        bool: True if the action is approved, False if cancelled by user.
    """
    if not force_flag:
        confirm = input(
            f"Are you sure you want to {action} the following packages: {packages}? [y/N]: "
        )
        if confirm.upper() not in ["Y", "N"] or confirm.upper() == "N":
            print("Operation cancelled by user.")
            return False

    print(f"{action.capitalize()} operation approved.")
    return True


def setup_parser(parser, completions=False):
    parser.add_argument(
        "context",
        nargs="*",
        type=str,
        metavar="context",
        help="Production context, defaults to 'studio'.",
        default=[None, None, None],
    )
    parser.add_argument(
        "-sw", "--software", type=str, default=None, help="Name of the software."
    )
    parser.add_argument(
        "-s",
        "--step",
        type=str,
        default=None,
        help="Pipeline step. Defaults to 'all'.",
    )
    parser.add_argument(
        "-i",
        "--install",
        type=str,
        nargs="+",
        metavar="package",
        help="Install a rez package to the current context.",
    )
    parser.add_argument(
        "-init",
        "--initialize",
        action="store_true",
        help="Initialize the staging database.",
    )
    parser.add_argument(
        "-ui",
        "--uninstall",
        type=str,
        nargs="+",
        metavar="package",
        help="Uninstall a rez package to the current context, this operation is always performed before installations.",
    )
    parser.add_argument(
        "-ls",
        "--list",
        action="store_true",
        help="List all installed packages in the current context.",
        dest="list_packages",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy the staging configuration to production.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force the config update.",
        default=False,
    )


def command(opts, parser=None, extra_arg_groups=None):
    from .production_resolver_lib import (
        ProductionResolverDatabase,
    )

    force_actions = opts.force

    with ProductionResolverDatabase(load_production=False) as db:
        if opts.initialize:
            confirm = input(
                "Do you want to generate a new staging database (existing value could be lost)? [y/N]: "
            )
            if confirm.upper() not in ["Y", "N"] or confirm.upper() == "N":
                print("Database initialization aborted by user.")
                return

            db.initialize()
            print("Database initialized successfully!")
            return

        contexts = db.sanitize_context(*opts.context)
        display_contexts = ["studio"]
        display_contexts.extend(contexts)
        print(
            f"Current contexts: {', '.join([str(context) for context in display_contexts if context])} [step: {opts.step}] (software: {opts.software})"
        )

        if not db.get_context_row_id(*contexts):
            _ = db.insert_context(*contexts)

        if opts.list_packages:
            package_list = db.get_package_list(
                contexts[0],
                contexts[1],
                contexts[2],
                step=opts.step,
                software=opts.software,
            )
            print("Installed packages:", ", ".join(package_list))
            return

        if opts.uninstall and len(opts.uninstall):
            if not _confirm_action("uninstall", opts.uninstall, opts.force):
                return

            for package in opts.uninstall:
                try:
                    db.remove_package(
                        contexts,
                        package,
                        step=opts.step,
                        software=opts.software,
                        validate=not force_actions,
                    )
                except ValueError as error_message:
                    print(error_message)
                    return

        if opts.install and len(opts.install):
            if not _confirm_action("install", opts.install, opts.force):
                return

            for package in opts.install:
                try:
                    db.add_package(
                        contexts,
                        package,
                        step=opts.step,
                        software=opts.software,
                        validate=not force_actions,
                    )
                except ValueError as error_message:
                    print(error_message)
                    return

        db.save()

        if opts.deploy:
            if not force_actions:
                confirm = input(
                    "Do you want to move the staging configuration to production? [y/N]: "
                )
                if confirm.upper() not in ["Y", "N"] or confirm.upper() == "N":
                    print("Deployment aborted by user.")
                    return

            db.deploy()
            print("Production configuration updated successfully!")


class ManageProductionCommand(Command):
    # This is where you declare the settings the plugin accepts.

    @classmethod
    def name(cls):
        return "manage"


def register_plugin():
    return ManageProductionCommand
