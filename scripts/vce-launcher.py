#!/usr/bin/env python3

import os
import argparse
import pathlib
import tomllib
import asyncio
import subprocess
import sys


VCE_ROOT = pathlib.Path(__file__).parent.parent.absolute()
"""
Path to the root folder of the VCE, assuming that this script
is located in `<VCE root>/scripts/`.
"""
DEFAULT_CONTAINER = VCE_ROOT / "vce-container.sif"


def main():
    # test_quoted_cmds()

    parser = argparse.ArgumentParser(
        description=(
            "Launch VCE components with a single command. "
            "Unless --no-tmux is used, "
            "tmux must be installed on the host system."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'config',
        type=pathlib.Path,
        help="VCE Launcher config file",
    )
    parser.add_argument(
        '--prepare-only',
        action='store_true',
        help="Don't start each component immediately. "
             "Instead, enter the appropriate environment for each "
             "component and prepare the configured launch command. "
             "To launch each respective component, enter its "
             "tmux window and press enter. "
             "(Does not work with --no-tmux.)",
    )
    parser.add_argument(
        '--no-tmux',
        action='store_true',
        help="NOT IMPLEMENTED YET. "
             "Do not start a tmux session and instead run each component "
             "silently.",
    )
    parser.add_argument(
        '--container',
        action='store_true',
        help=f"Use Apptainer with "
             f"\"{os.path.relpath(DEFAULT_CONTAINER, '.')}\" "
             "to run each component.",
    )
    parser.add_argument(
        '--logs-dir',
        type=pathlib.Path,
        help="NOT IMPLEMENTED YET. "
             "If running with --no-tmux, the standard output of each "
             "component will be written to a <component>.log file "
             "in the specified logs directory. "
             "Note that this may impact performance.",
        default=".",
    )
    args = parser.parse_args()

    with open(args.config, 'rb') as f:
        cfg = tomllib.load(f)

    launch_vce(
        cfg=cfg,
        workdir=args.config.parent.absolute(),
        use_tmux=not args.no_tmux,
        prepare_only=args.prepare_only,
        logs_dir=args.logs_dir,
        use_container=args.container,
    )


class Component:
    def __init__(
            self,
            env_cmd: 'Cmd',
            run_cmd: 'Cmd',
            full_cmd: 'Cmd | None' = None,
            prompt: str = "vce> ",
            greeting: str = "Press enter to launch the component.",
            container_img: pathlib.Path | None = None,
    ):
        self.env_cmd = env_cmd
        """
        Command for entering the appropriate environment for the
        respective component and configuration.
        E.g., `cd my-component/ && source ./setenv`
        """
        self.run_cmd = run_cmd
        """
        Command that will launch the component assuming the user
        is already in the appropriate environment.
        E.g., `./run.sh --myarg`
        """
        self.full_cmd = (
            full_cmd if full_cmd else
            Cmd.concat(env_cmd, Cmd(" && "), run_cmd)
        )
        self.prompt = prompt
        """Override bash or Apptainer prompt"""
        self.greeting = greeting

        self.container_img = container_img
        self._container_enabled = False  # only enable once
        if container_img:
            self.enable_container()

    def enable_container(self):
        if self._container_enabled:
            print("Container was already enabled for this component.")
            return

        def build_container_cmd(cmd_in: Cmd | str):
            return Cmd(
                "apptainer exec ",
                QuotedCmd(self.container_img),
                " bash --init-file <(echo ",
                QuotedCmd(cmd_in),
                ")",
            )
        self.env_cmd = build_container_cmd(self.env_cmd)
        # TODO: skip using --init-file for full_cmd
        self.full_cmd = build_container_cmd(self.full_cmd)
        self._container_enabled = True


class Cmd:
    """
    A class that, in conjunction with QuotedCmd, makes it possible
    to dynamically assemble shell commands with nested subcommands
    in quotation marks.
    Depending on the level of nesting, quotation marks will be
    escaped the appropriate number of times.

    Example: Cmd("bash -c ", QuotedCmd("echo ", QuotedCmd("hi")))
    Output: `bash -c "echo \"hi\""`
    # TODO: does this example output render correctly in generated
    #  docs?
    """

    def __init__(self, *parts: 'list[str | Cmd]'):
        self._parts = list(parts)

    def __str__(self):
        return "".join([
            str(part)
            for part in self._parts
        ])

    def __repr__(self):
        return (
            "Cmd([\n  "
            + ',\n  '.join([
                repr(part).replace('\n', '\n  ')
                for part in self._parts
            ])
            + "\n])"
        )

    @staticmethod
    def concat(*cmds: 'list[Cmd]'):
        result = Cmd()
        for cmd in cmds:
            result._parts.extend(cmd._parts)
        return result

    def append(self, cmd: 'Cmd'):
        self._parts.extend(cmd._parts)


class QuotedCmd(Cmd):
    def __init__(self, *parts: 'list[str | QuotedCmd]'):
        super().__init__(*parts)

    def __str__(self):
        return '"' + "".join([
            str(part)
            .replace('\\', '\\\\')
            .replace('"', r'\"')
            # .replace('$', r'\$')  # doesn't work…
            # might not work with Windows, but thwi
            if isinstance(part, Cmd)
            else str(part)
            for part in self._parts
        ]) + '"'

    def __repr__(self):
        return "Quoted" + super().__repr__()


def launch_vce(
        cfg: dict,
        workdir: pathlib.Path,
        use_tmux: bool,
        use_container: bool,
        prepare_only: bool,
        logs_dir: pathlib.Path,
):
    container_img = DEFAULT_CONTAINER if use_container else None
    components: list[Component] = []
    if evi_component := get_evi_component(cfg, workdir, container_img):
        components.append(evi_component)
    if veins_evi_component := get_veins_evi_component(
            cfg, workdir, container_img):
        components.append(veins_evi_component)
    if (
            bike_interface_component
            := get_bike_interface_component(cfg, workdir, container_img)
    ):
        components.append(bike_interface_component)

    if use_tmux:
        launch_tmux(components, prepare_only=prepare_only)
    else:
        sys.exit("Launching without tmux not implemented yet")
        # subprocess.run(
        #     evi_launch_cmd,
        #     stdout=f,  # TODO
        #     stderr=subprocess.STDOUT,
        #     check=True,  # may raise CalledProcessError
        # )


async def launch_component(
        cmd: str,
        log_file: pathlib.Path | None,
):
    proc = await asyncio.subprocess.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # TODO


def get_evi_component(
        cfg: dict,
        workdir: pathlib.Path,
        container_img: pathlib.Path,
) -> Component | None:
    if not cfg.get('evi'):
        print("No configuration for [evi] -> "
              "not launching component")
        return None
    if 'config_file' not in cfg['evi']:
        sys.exit(
            "Launch configuration of 'evi' is missing "
            "the 'config_file' parameter, which should be "
            "a path to an existing *.evi.ini file."
        )
    evi_root = VCE_ROOT / "evi"
    return Component(
        env_cmd=Cmd(
            "cd ",
            QuotedCmd(f"{evi_root}"),
        ),
        # `poetry shell` doesn't work with our --prepare-only,
        # so use `poetry run` in run_cmd instead:
        run_cmd=Cmd(
            "poetry run ",
            QuotedCmd("scripts/evid.py"),
            " --config-file ",
            QuotedCmd(f"{workdir / cfg['evi']['config_file']}"),
            " " + cfg['evi'].get('args', ''),
        ),
        full_cmd=None,  # use default
        container_img=container_img,
        prompt="evi> ",
        greeting=(
            "--- EGO VEHICLE INTERFACE ---\n"
            "Launch this before starting the 3D environment."
            "\n\n"
            "Press enter to launch this component.\n"
        )
    )


def get_veins_evi_component(
        cfg: dict,
        workdir: pathlib.Path,
        container_img: pathlib.Path,
) -> Component | None:
    if not cfg.get('veins-evi'):
        print("No configuration for [veins-evi] -> "
              "not launching component")
        return None
    if 'scenario' not in cfg['veins-evi']:
        sys.exit(
            "Launch configuration of 'veins-evi' is missing "
            "the 'scenario' parameter, which should be a path "
            "to the scenario folder."
        )
    veins_evi_scenario_dir = workdir / cfg['veins-evi']['scenario']
    return Component(
        env_cmd=Cmd(
            "cd ",
            QuotedCmd(f"{veins_evi_scenario_dir}"),
        ),
        run_cmd=Cmd(
            f"./run {cfg['veins-evi'].get('args', '')}"
        ),
        full_cmd=None,  # use default
        container_img=container_img,
        prompt="veins-evi> ",
        greeting=(
            "--- VEINS-EVI ---\n"
            "This component is responsible for V2X simulation. "
            "EVI and Veins-EVI should be able to wait for each other. "
            "Launch this before the 3D environment."
            "\n\n"
            "Press enter to launch this component.\n"
        )
    )


def get_bike_interface_component(
        cfg: dict,
        workdir: pathlib.Path,
        container_img: pathlib.Path,
) -> Component | None:
    if not cfg.get('bike-interface'):
        print("No configuration for [bike-interface] -> "
              "not launching component")
        return None
    bike_interface_root = (
        VCE_ROOT / "bike-interface" / "bicycle-model" / "bikeToEvi"
    )
    return Component(
        env_cmd=Cmd(
            "cd ",
            QuotedCmd(f"{bike_interface_root}"),
        ),
        run_cmd=Cmd(
            "poetry run python ./main.py "
            f"{cfg['bike-interface'].get('args', '')}"
        ),
        full_cmd=None,  # use default
        container_img=container_img,
        prompt="bike-interface> ",
        greeting=(
            "--- BICYCLE INTERFACE ---\n"
            "This is the bicycle interface, responsible for processing sensor "
            "data from the input bicycle. "
            "If this is launched before the 3D environment, be careful "
            "not to move the bicycle. "
            "Otherwise, you may end up in unexpected places when the "
            "3D environment starts. "
            "If this happens, simply restart this component."
            "\n\n"
            "Press enter to launch this component.\n"
        )
    )


def test_quoted_cmds():
    def cmd(cls, msg):
        return str(cls("bash -c ", QuotedCmd("bash -c ", QuotedCmd(
            "echo ",
            QuotedCmd(msg))
        )))
    subprocess.run(
        cmd(Cmd, "This should print without any visible quotes!"),
        shell=True,
        check=True,
    )
    print("\n")
    subprocess.run(
        cmd(
            Cmd,
            "This should print with single double-quotes "
            "around the following word: \\\"hi\\\"!"),
        shell=True,
        check=True,
    )
    print("\n")
    subprocess.run(
        str(QuotedCmd(
            "level0 ",
            QuotedCmd(
                "quoted lvl1"
            ),
            " level0 ",
            Cmd(
                "unquoted nested ",
            ),
            Cmd(
                # Should get the same number of escaped quotes as
                # the other "quoted lvl1":
                QuotedCmd("nested quoted lvl1"),
            ),
        )),
        shell=True,
        check=False,
    )
    print("\n")
    # subprocess.run(
    #     cmd(
    #         QuotedCmd,
    #         "This should fail "
    #         "and show all escaped characters in the error message"
    #     ),
    #     shell=True,
    #     check=True,
    # )
    cmd = str(QuotedCmd(
        "<tmux> ",
        QuotedCmd(
            "<bash> ",
            QuotedCmd(
                "<apptainer-bash> ",
                QuotedCmd("<cd…>"),
            ),
        ),
        "<tmux end>",
    ))
    print(cmd)
    subprocess.run(
        cmd,
        shell=True,
        check=True,
    )


def launch_tmux(components: list[Component], prepare_only: bool):
    # Considerations on levels of nested quotes:
    # Some levels are not used depending on launcher args
    #  -> need to find number of escaped backslashes and quotes dynamically
    #
    # Commands will have the following structure:
    # ```
    # tmux … send-keys "
    #    bash -c '  # -> double quotes! Can't nest single-quotes!
    #       apptainer exec img.sif bash --init-file <(echo '  #  -> double quotes
    #           cd "some/path/"
    #           && PS1="…"
    #       ')
    #    '
    # "
    # ```

    if 'TMUX' in os.environ:
        # If we don't exit in this case, Tmux will.
        sys.exit(
            "Please run vce-launcher.py from outside any active "
            "Tmux sessions."
        )
    if 'APPTAINER_CONTAINER' in os.environ:
        sys.exit(
            "Please run vce-launcher.py from outside any Apptainer "
            "containers. Otherwise, tmux may launch shells in the "
            "host environment.\n"
            f"Current container: {os.environ['APPTAINER_CONTAINER']}"
        )

    # TODO: check if tmux session already exists

    tmux_cmd = [
        "tmux new-session -s 'VCE' "  # session: VCE
        "-n 'vce-run' \; "  # window: vce-run
    ]
    for i, component in enumerate(components):
        # Prefixing each cmd with `bash -c` for compatibility
        # in case fish is configured as the default shell in tmux.
        if prepare_only:
            container_info = Cmd(" && echo ", QuotedCmd(
                "Running in container image ",
                QuotedCmd(component.container_img)
            )) if component.container_img else ""
            tmux_cmd.extend([
                "send-keys ",
                QuotedCmd(
                    "bash -c ",
                    QuotedCmd(component.env_cmd),
                ),
                " C-m \; send-keys ",
                QuotedCmd(
                    "PS1=",
                    QuotedCmd(component.prompt),
                    " && clear",
                    container_info,
                    " && echo -n ", QuotedCmd("CWD: "),
                    " && pwd && echo ",
                    QuotedCmd("\n" + component.greeting),
                ),
                " C-m \; send-keys ",
                QuotedCmd(component.run_cmd),
                " \; ",  # without `C-m`
            ])
            # does not work with `poetry shell`
            #  b/c it discards everything typed while it is starting up…
            #  -> use `poetry run` instead
        else:
            tmux_cmd.append("send-keys ")
            tmux_cmd.append(QuotedCmd(
                "bash -c ",
                QuotedCmd(component.full_cmd),
            ))
            tmux_cmd.append(" C-m \; ")

        if i == len(components) - 1:
            # Don't split the window if this was the last cmd
            break
        # Let's make only at most one vertical split and
        # otherwise split windows horizontally:
        split = '-v' if i == len(components) // 2 else '-h'
        tmux_cmd.append(f" split-window {split} \; ")
    # print(repr(QuotedCmd(*tmux_cmd)))
    tmux_cmd = str(Cmd(*tmux_cmd))
    # print()
    # print(tmux_cmd)
    subprocess.run(tmux_cmd, shell=True, check=True)


if __name__ == '__main__':
    main()
