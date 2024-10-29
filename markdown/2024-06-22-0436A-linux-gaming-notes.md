---
title: some notes about gaming on linux
short: this is mostly so i don't forget
date: 2024-06-22 4:36 AM
updated: 2024-10-29 3:19 AM
---

I recently migrated to using Linux full time.
You need to not look far to find an ocean of reasons why Windows has been a bit miserable.

This post mainly serves as a logbook for fixes and workarounds for making games (and some applications) work on Linux.

[TOC]

## EAC "Failed to Intialize Dependencies" error

This is likely due to a `SDL_VIDEODRIVER` and/or `SDL_VIDEO_DRIVER` environment variable being present.

Try using the following launch arguments:

`env --unset=SDL_VIDEODRIVER --unset=SDL_VIDEO_DRIVER %command%`

or

`env SDL_VIDEODRIVER=windows SDL_VIDEO_DRIVER=windows %command%`

Alternatively, set the variable to an empty string in whatever launch manager you're using (Heroic, Lutris).

The EAC splash also sometimes fail to load if you are using the proprietary AMD drivers (i.e. `vk_radv %command%`.)

## Enabling DX12 Ray Tracing

If you have a ray tracing capable GPU (RTX 2000 or newer, RX 6800 or newer)
you might be able to tell Mesa and VKD3D that ray-tracing can be enabled by using the following launch arguments:

`env RADV_PERFTEST=rt VKD3D_CONFIG=dxr VKD3D_FEATURE_LEVEL=12_2 %command%`

If you have an older GPU you can try:

`env RADV_PERFTEST=emulate_rt VKD3D_CONFIG=dxr VKD3D_FEATURE_LEVEL=12_2 %command%`

This assumes you have a relatively recent VKD3D and Mesa installation,
and the game has to support ray tracing in any capacity (i.e. World of Warcraft, Ratchet and Clank: Rift Apart)

## Games not capturing mouse cursor

Some games don't play nice with mouse capture, an easy way to solve this is by changing the launch arguments to:

`gamescope --force-grab-cursor -f %command%`

You may swap -f with -b for borderless windowed instead of fullscreen.

## Gamescope exiting early due to short-lived launcher processes

Some games launch via third party launchers that cause gamescope to exit before the wine device.

This may be solved by forcing the SDL backend.

`gamescope --backend sdl %command%`

## Gamescope resolution being fixed to the first window size under SDL

Gamescope under SDL has a hard time adjusting to resolution changes (i.e. if you're using it for launcher processes.), to solve this you must force the window to be fullscreen.

`gamescope -w YOUR_RESOLUTION_HERE -h YOUR_RESOLUTION_HERE -r YOUR_REFRESH_RATE_HERE --backend sdl --force-windows-fullscreen -f %command%`

(Special thanks to [Hollyrious](https://twitch.tv/hollyrious) for helping me diagnose this!)

## Windows-only Third-Party Mod Tooling

You can add the mod tools as a non-steam game, given it has a GUI.

When you do, force it to use **the same compatability tools as the game** and set the launch arguments to:

`env STEAM_COMPAT_DATA_PATH="~/.steam/root/steamapps/compatdata/489830" %command%`

You may need to install more dependencies like .NET 4.8/6.0, etc via protontricks, select the game *not* the non-steam app when installing.

Change `~/.steam/root/steamapps` to the SteamLibrary steamapps folder if installed in a steam library folder.

Change 489830 to match the steam id of the mod tool the game is for, 489830 is Skyrim SE/AE.
It is the number after `/app/` in the Steam store link, alternatively look it up on SteamDB.

## SteamVR / Monado

SteamVR and VR in general on Linux is not good, however it is possible.
Your experience will be extremely improved if you have a Valve Index.
Any other headset is unsupported and SteamVR will assume it just to be an Index (or not detect it at all.)
To remedy this, you can use Monado.

If you run a system that does not have pkexec set up with a GUI (or at all,) you have to manually run setcap (as root)

`setcap CAP_SYS_NICE=eip ~/.steam/steam/steamapps/common/SteamVR/bin/linux64/vrcompositor-launcher`

If you plan on running monado as-is outside of SteamVR, you have to do the same for Monado.

`setcap CAP_SYS_NICE=eip /usr/bin/monado-service`

You may also have to use the vrmonitor directly in the command:

`~/.steam/steam/steamapps/common/SteamVR/bin/vrmonitor.sh %command%`

### AMDGPU

AMD does not ship the required Vulkan extensions that Monado needs in the FOSS driver present in the Linux kernel. You need to use the proprietary AMDGPU Radeon drivers and launch SteamVR as follows:

`vk_radv ~/.steam/steam/steamapps/common/SteamVR/bin/vrmonitor.sh %command%`

### WMR

Windows Mixed Reality is [deprecated by Microsoft, and support will be removed in November 2026](https://learn.microsoft.com/en-us/windows/whats-new/deprecated-features#deprecated-features).
This makes Monado on Linux the only way to still use

**However** getting it to work is non-trivial. WMR supports needs a hidden dependency, Basalt. [Specifically a fork of Basalt](https://gitlab.freedesktop.org/mateosss/basalt).

My command looks something like:

`env VIT_SYSTEM_LIBRARY_PATH=/usr/lib64/libbasalt-monado.so PRESSURE_VESSEL_FILESYSTEMS_RW=$XDG_RUNTIME_DIR/monado_comp_ipc SLAM_CONFIG=/usr/share/basalt/msdmo.toml SLAM_SUBMIT_FROM_START=1 SLAM_UI=0 XRT_COMPOSITOR_COMPUTE=1 XRT_DEBUG_GUI=0 AEG_USE_DYNAMIC_RANGE=0 WMR_AUTOEXPOSURE=0 STEAMVR_EMULATE_INDEX_CONTROLLER=0 ~/.steam/steam/steamapps/common/SteamVR/bin/vrmonitor.sh %command%`

Keep in mind you need to replace `%command%` with the AMDGPU section if applicable, and adjust the `VIT_SYSTEM_LIBRARY_PATH` and `SLAM_CONFIG` path.

- `VIT_SYSTEM_LIBRARY_PATH` is the path the modified basalt exists.
- `SLAM_CONFIG` tells monado where the Basalt SLAM config is. `msdmo` is the one I found to work the best for the HMD Odyssey+, however `msdmi` and `msdmg` also exist.
- `PRESSURE_VESSEL_FILESYSTEMS_RW` instructs the steam pressure vessel to allow access to the monado IPC socket.
- `SLAM_SUBMIT_FROM_START` submits tracking info from initialization.
- `SLAM_UI` controls whether or not to show the debug SLAM ui.
- `XRT_COMPOSITOR_COMPUTE` setting this to true resolves stuttering if framerate is below the native refresh rate.
- `XRT_DEBUG_GUI` controls whether or not to show the debug OpenXR ui.
- `AEG_USE_DYNAMIC_RANGE` and `WMR_AUTOEXPOSURE` control auto exposure, you should keep this disabled.
- `STEAMVR_EMULATE_INDEX_CONTROLLER` tells monado if it should emulate a Valve Index controller.

### "Headset Off" when calibrating

Instruct Monado to emulate the Index Controlller. This might magically fix it. It did for me.

Failing that follow the instructions laid out by the [Linux VR Adventures Wiki](https://lvra.gitlab.io/docs/steamvr/).

## Game-Specific Fixes

### Dauntless

If you randomly crash, it might be because of stack smashing due to a race condition.

I have managed to reduce the frequency of crashes by limiting how many resources the game can use.

`env DXVK_CONFIG="dxvk.numCompilerThreads=1" WINE_CPU_TOPOLOGY="4:0,2,4,6" %command%`

If there is too much lag, you might want to redefine the CPU topology, i.e. `WINE_CPU_TOPOLOGY="8:0,1,2,3,4,5,6,7"`

## Changelog

*Update: 2024-09-22 - Added gamescope-related workarounds.*
*Update: 2024-10-29 - Added Monado/SteamVR.*
*Update: 2024-10-29 - Added note about proprietary drivers and EAC.*
