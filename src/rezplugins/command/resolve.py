"""Resolve the production environment."""

from rez.command import Command
from rez.resolved_context import ResolvedContext

command_behavior = {
    "hidden": False,  # optional: bool
    "arg_mode": None,  # optional: None, "passthrough", "grouped"
}


def setup_parser(parser, completions=False):
    parser.add_argument(
        "context",
        nargs="*",
        type=str,
        metavar="context",
        help="Production context, defaults to 'studio'.",
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
        "-stg",
        "--staging",
        action="store_true",
        default=False,
    )


def command(opts, parser=None, extra_arg_groups=None):
    from .production_resolver_lib import (
        ProductionResolverDatabase,
    )

    is_production_database = not opts.staging

    with ProductionResolverDatabase(load_production=is_production_database) as db:
        if not db.exists():
            print("Error: Database not found.")

        contexts = db.sanitize_context(*opts.context)
        display_contexts = ["studio"]
        display_contexts.extend(contexts)
        print(
            f"Current contexts: {', '.join([str(context) for context in display_contexts if context])} [step: {opts.step}] (software: {opts.software})"
        )

        package_list = db.get_package_list(
            contexts[0],
            contexts[1],
            contexts[2],
            step=opts.step,
            software=opts.software,
        )
        print("Installed packages:", ", ".join(package_list))

        rez_context = ResolvedContext(package_list)

        if not opts.software:
            rez_context.execute_shell()
            return

        rez_context.execute_command([opts.software])


class ResolveProductionCommand(Command):
    # This is where you declare the settings the plugin accepts.

    @classmethod
    def name(cls):
        return "resolve"


def register_plugin():
    return ResolveProductionCommand
