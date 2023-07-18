#!/usr/bin/env python3

import os
import argparse
import pathlib
import tomllib
import asyncio
import subprocess
import shutil
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Configuration file (.launcher.toml) parameters:\n\n"
            + "\n\n".join(c.get_help() for c in COMPONENT_CLASSES)
        ),
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
        help="Use Apptainer with "
             f"\"{os.path.relpath(DEFAULT_CONTAINER, '.')}\" "
             "to run each component.",
    )
    parser.add_argument(
        '--nv',
        action='store_true',
        help="Use --nv option with all Apptainer commands. "
             "Note that this may cause issues of missing libraries.",
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

    if not args.no_tmux and not shutil.which("tmux"):
        sys.exit("Could not find an installation of `tmux`.")
    if args.container and not shutil.which("apptainer"):
        sys.exit("Could not find an installation of `apptainer`.")
    if not args.container:
        deps = [
            "omnetpp",
            "sumo",
            "poetry",
        ]
        for program in deps:
            if not shutil.which(program):
                sys.exit(
                    f"Could not find an installation of `{program}`. "
                    "Did you forget the --container option?"
                )

    with open(args.config, 'rb') as f:
        full_cfg = tomllib.load(f)

    launch_vce(
        full_cfg=full_cfg,
        workdir=args.config.parent.absolute(),
        use_tmux=not args.no_tmux,
        prepare_only=args.prepare_only,
        logs_dir=args.logs_dir,
        use_container=args.container,
        container_nvidia=args.nv,
    )


class Component:
    _cfg_section = None
    _cfg_mandatory_args = dict()
    _cfg_optional_args = dict(
        wait_for_ports=(
            "A list of ports. "
            "Launch this component only when all ports are open."
        )
    )

    @classmethod
    def check_config(cls, full_cfg: dict) -> bool:
        if cls._cfg_section not in full_cfg:
            print(
                f"No configuration for [{cls._cfg_section}] "
                "-> Not launching component"
            )
            return False
        component_cfg = full_cfg[cls._cfg_section]
        for mandatory_arg, description in cls._cfg_mandatory_args.items():
            if mandatory_arg not in component_cfg:
                sys.exit(
                    f"Launch configuration of '{cls._cfg_section}' is "
                    f"missing the mandatory '{mandatory_arg}' parameter.\n"
                    f"Parameter description: {description}"
                )
        return True

    def __init__(
            self,
            full_cfg: dict,
            env_cmd: 'Cmd',
            run_cmd: 'Cmd',
            full_cmd: 'Cmd | None' = None,
            prompt: str = "vce> ",
            greeting: str = "Press enter to launch the component.",
            container_img: pathlib.Path | None = None,
            container_nvidia=False,
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

        if ports := full_cfg[self._cfg_section].get('wait_for_ports'):
            self.run_cmd = Cmd(
                QuotedCmd(VCE_ROOT / "scripts" / "wait-for-component.py"),
                " --port-open "
                + " ".join([str(port) for port in ports])
                + " && ",
                self.run_cmd,
            )

        self.container_img = container_img
        self._container_enabled = False  # only enable once
        self.container_nvidia = container_nvidia
        if container_img:
            self.enable_container()

    @property
    def is_enabled(self):
        return self._enabled

    def enable_container(self):
        if self._container_enabled:
            print("Container was already enabled for this component.")
            return

        def build_container_cmd(cmd_in: Cmd | str):
            return Cmd(
                f"apptainer exec {'--nv' if self.container_nvidia else ''} ",
                QuotedCmd(self.container_img),
                " bash --init-file <(echo ",
                QuotedCmd(cmd_in),
                ")",
            )
        self.env_cmd = build_container_cmd(self.env_cmd)
        # TODO: skip using --init-file for full_cmd
        self.full_cmd = build_container_cmd(self.full_cmd)
        self._container_enabled = True

    @classmethod
    def get_help(cls) -> str:
        key_max_len = max([
            len(k) for k in
            list(cls._cfg_mandatory_args.keys())
            + list(cls._cfg_optional_args.keys())
        ])
        return (
            f"[{cls._cfg_section}]"
            + (
                "\nRequired arguments:\n"
                + "\n".join(
                    f"  {arg+':':{key_max_len + 3}}{desc}"
                    for arg, desc in cls._cfg_mandatory_args.items()
                )
                if len(cls._cfg_mandatory_args) > 0 else ""
            )
            + (
                "\nOptional arguments:\n"
                + "\n".join(
                    f"  {arg+':':{key_max_len + 3}}{desc}"
                    for arg, desc in cls._cfg_optional_args.items()
                )
                if len(cls._cfg_optional_args) > 0 else ""
            )
        )


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
        full_cfg: dict,
        workdir: pathlib.Path,
        use_tmux: bool,
        use_container: bool,
        container_nvidia: bool,
        prepare_only: bool,
        logs_dir: pathlib.Path,
):
    container_img = DEFAULT_CONTAINER if use_container else None
    components: list[Component] = []
    for component_cls in COMPONENT_CLASSES:
        component = component_cls(
            full_cfg=full_cfg,
            workdir=workdir,
            container_img=container_img,
            container_nvidia=container_nvidia,
        )
        if component.is_enabled:
            components.append(component)

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


class EVIComponent(Component):
    _cfg_section = 'evi'
    _cfg_mandatory_args = dict(
        config_file="Path to an existing *.evi.ini file",
        **Component._cfg_mandatory_args,
    )
    _cfg_optional_args = dict(
        args="Additional arguments for evi/scripts/evid.py",
        **Component._cfg_optional_args,
    )

    def __init__(
            self,
            full_cfg: dict,
            workdir: pathlib.Path,
            **kwargs,
    ):
        self._enabled = self.check_config(full_cfg)
        if not self._enabled:
            return
        evi_root = VCE_ROOT / "evi"
        super().__init__(
            full_cfg=full_cfg,
            env_cmd=Cmd(
                "cd ",
                QuotedCmd(f"{evi_root}"),
            ),
            run_cmd=Cmd(
                "poetry run ",
                QuotedCmd("scripts/evid.py"),
                " --config-file ",
                QuotedCmd(f"{workdir / full_cfg['evi']['config_file']}"),
                " " + full_cfg['evi'].get('args', ''),
            ),
            full_cmd=None,  # use default
            prompt="evi> ",
            greeting=(
                "--- EGO VEHICLE INTERFACE ---\n"
                "\n"
                "Press enter to launch this component.\n"
            ),
            **kwargs
        )


class VeinsEVIComponent(Component):
    _cfg_section = 'veins-evi'
    _cfg_mandatory_args = dict(
        scenario="Path to the scenario folder (should contain a ./run script)",
        **Component._cfg_mandatory_args,
    )
    _cfg_optional_args = dict(
        args="Additional arguments for ./run and opp_run",
        **Component._cfg_optional_args,
    )

    def __init__(
        self,
        full_cfg: dict,
        workdir: pathlib.Path,
        **kwargs,
    ):
        self._enabled = self.check_config(full_cfg)
        if not self._enabled:
            return
        veins_evi_scenario_dir = workdir / full_cfg['veins-evi']['scenario']
        super().__init__(
            full_cfg=full_cfg,
            env_cmd=Cmd(
                "cd ",
                QuotedCmd(f"{veins_evi_scenario_dir}"),
            ),
            run_cmd=Cmd(
                f"./run {full_cfg['veins-evi'].get('args', '')}"
            ),
            full_cmd=None,  # use default
            prompt="veins-evi> ",
            greeting=(
                "--- VEINS-EVI ---\n"
                "This component is responsible for V2X simulation. "
                "\n\n"
                "Press enter to launch this component.\n"
            ),
            **kwargs,
        )


class BikeInterfaceComponent(Component):
    _cfg_section = 'bike-interface'
    _cfg_mandatory_args = dict(**Component._cfg_mandatory_args)
    _cfg_optional_args = dict(
        args="Additional arguments to pass to "
             "bike-interface/bicycle-model/bikeToEvi/main.py",
        **Component._cfg_optional_args,
    )

    def __init__(
        self,
        full_cfg: dict,
        workdir: pathlib.Path,
        **kwargs,
    ):
        self._enabled = self.check_config(full_cfg)
        if not self._enabled:
            return
        bike_interface_root = (
            VCE_ROOT / "bike-interface" / "bicycle-model" / "bikeToEvi"
        )
        super().__init__(
            full_cfg=full_cfg,
            env_cmd=Cmd(
                "cd ",
                QuotedCmd(f"{bike_interface_root}"),
            ),
            run_cmd=Cmd(
                "poetry run python ./main.py "
                f"{full_cfg['bike-interface'].get('args', '')}"
            ),
            full_cmd=None,  # use default
            prompt="bike-interface> ",
            greeting=(
                "--- BICYCLE INTERFACE ---\n"
                "This is the bicycle interface, "
                "responsible for processing sensor "
                "data from the input bicycle. "
                "If this is launched before the 3D environment, be careful "
                "not to move the bicycle. "
                "Otherwise, you may end up in unexpected places when the "
                "3D environment starts. "
                "If this happens, simply restart this component."
                "\n\n"
                "Press enter to launch this component.\n"
            ),
            **kwargs,
        )


class MultiplayerInterfaceComponent(Component):
    _cfg_section = 'multiplayer-interface'
    _cfg_mandatory_args = dict(
        env3d_port="Port for the 3D Environment to connect to",
        evi_port="Port on which the EVI is listening",
        connections="Number of multiplayer connections",
        **Component._cfg_mandatory_args,
    )
    _cfg_optional_args = dict(**Component._cfg_optional_args)

    def __init__(
        self,
        full_cfg: dict,
        workdir: pathlib.Path,
        **kwargs,
    ):
        self._enabled = self.check_config(full_cfg)
        if not self._enabled:
            return
        mp_cfg = full_cfg[self._cfg_section]
        evi_root = VCE_ROOT / "evi"
        super().__init__(
            full_cfg=full_cfg,
            env_cmd=Cmd(
                "cd ",
                QuotedCmd(f"{evi_root}"),
            ),
            # `poetry shell` doesn't work with our --prepare-only,
            # so use `poetry run` in run_cmd instead:
            run_cmd=Cmd(
                "poetry run ",
                QuotedCmd("scripts/multiplayer-interface/interface.py"),
                f" --env3d-port {mp_cfg['env3d_port']}",
                f" --evi-port {mp_cfg['evi_port']}",
                f" --connections {mp_cfg['connections']}",
            ),
            full_cmd=None,  # use default
            prompt="multiplayer (evi)> ",
            greeting=(
                "--- MULTIPLAYER INTERFACE ---\n"
                "\n\n"
                "Press enter to launch this component.\n"
            ),
            **kwargs,
        )


class Env3DComponent(Component):
    _cfg_section = 'env3d'
    _cfg_mandatory_args = dict(
        scenario="Path to a SUMO .net.xml",
        evi_address="Address to EVI or Multiplayer Interface",
        evi_port="Port for EVI or Multiplayer Interface",
        **Component._cfg_mandatory_args,
    )
    _cfg_optional_args = dict(
        scenario_seed="Seed for procedural buildings etc.",
        vehicle_type="(BICYCLE | BICYCLE_WITH_MINIMAP | "
                     "BICYCLE_INTERFACE | CAR)",
        evi_connect_on_launch="(true|false) If true, connect immediately",
        skip_menu="(true|false) If true, skip menu screen on launch",
        executable_path="Default: 3denv/build/3denv.x86_64",
        allow_container="(true|false) If false, don't run in container "
                        "even if the launcher is running with --container.",
        **Component._cfg_optional_args,
    )

    def __init__(
        self,
        full_cfg: dict,
        workdir: pathlib.Path,
        **kwargs,
    ):
        self._enabled = self.check_config(full_cfg)
        if not self._enabled:
            return
        env3d_cfg = full_cfg[self._cfg_section]
        kwargs['container_img'] = (
            kwargs.get('container_img')
            if env3d_cfg.get('allow_container')
            else None
        )
        # TODO: check if executable exists
        #  (although, this check should exist for all components…)
        super().__init__(
            full_cfg=full_cfg,
            env_cmd=Cmd(),
            run_cmd=Cmd(
                QuotedCmd(env3d_cfg.get(
                    'executable_path',
                    VCE_ROOT / "3denv" / "build" / "3denv.x86_64"
                )),
                " --scenario=",
                QuotedCmd(workdir / env3d_cfg['scenario']),
                f" --evi-address={env3d_cfg['evi_address']}",
                f" --evi-port={env3d_cfg['evi_port']}",
                (
                    f" --scenario-seed={env3d_cfg['scenario_seed']}"
                    if 'scenario_seed' in env3d_cfg else ""
                ),
                (
                    " --evi-connect-on-launch=True"
                    if env3d_cfg.get('evi_connect_on_launch', False) else ""
                ),
                " --skip-menu=True"
                if env3d_cfg.get('skip_menu', False)
                else "",
                (
                    f" --vehicle-type={env3d_cfg['vehicle_type']}"
                    if 'vehicle_type' in env3d_cfg else ""
                ),
            ),
            full_cmd=None,  # use default
            prompt="3denv> ",
            greeting=(
                "--- 3D ENVIRONMENT ---\n"
                "\n"
                "Press enter to launch this component.\n"
            ),
            **kwargs,
        )


COMPONENT_CLASSES = (
    EVIComponent,
    VeinsEVIComponent,
    BikeInterfaceComponent,
    MultiplayerInterfaceComponent,
    Env3DComponent,
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
        "-n 'vce-run' \\; "  # window: vce-run
    ]
    tmux_cmd.append(Cmd(
        # For showing a title above each tmux pane
        "set pane-border-status top \\; "
        "set pane-border-format ",
        QuotedCmd("#{pane_index} #{@vce_pane_title}"),
        " \\; "
    ))
    for i, component in enumerate(components):
        # Prefixing each cmd with `bash -c` for compatibility
        # in case fish is configured as the default shell in tmux.
        container_info = Cmd(" && echo ", QuotedCmd(
            "Running in container image ",
            QuotedCmd(component.container_img)
        )) if component.container_img else ""
        tmux_cmd.extend([
            # Enter component environment:
            "send-keys ",
            QuotedCmd(
                "bash",
                Cmd(
                    " -c ",
                    QuotedCmd(component.env_cmd),
                ) if str(component.env_cmd).strip() != "" else ""
                # Still enter a new bash shell even if there's
                # no env command, because we'll need it for
                # compatibility with `PS1=…` below, which doesn't work
                # in fish shell, for example.
            ),
            " C-m \\; ",
            # Set Tmux pane title:
            "set -p @vce_pane_title ",
            QuotedCmd(component.prompt),
            " \\; "
            # Output some information about the component:
            "send-keys ",
            QuotedCmd(
                # Set bash prompt:
                "PS1=",
                QuotedCmd(component.prompt),
                # Hide previously entered commands from user:
                " && clear",
                # If we're in a container, print its path:
                container_info,
                # Print the current directory:
                " && echo -n ", QuotedCmd("CWD: "),
                " && pwd && echo ",
                # Print some info/greeting for this VCE component:
                QuotedCmd("\n" + component.greeting),
            ),
            # Run (or prepare) the component command:
            " C-m \\; send-keys ",
            QuotedCmd(component.run_cmd),
            f" {'' if prepare_only else 'C-m'} \\; ",
        ])
        # does not work with `poetry shell`
        #  b/c it discards everything typed while it is starting up…
        #  -> use `poetry run` instead

        if i < len(components) - 1:
            tmux_cmd.append(" split-window -h \\; ")

    tmux_cmd.append(" select-layout tiled \\; ")
    # print(repr(QuotedCmd(*tmux_cmd)))
    tmux_cmd = str(Cmd(*tmux_cmd))
    # print()
    # print(tmux_cmd)
    subprocess.run(tmux_cmd, shell=True, check=True)


if __name__ == '__main__':
    main()
