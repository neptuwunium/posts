---
title: some notes about gaming on linux
short: this is mostly so i don't forget
date: 2024-06-22 4:36 AM
updated: 2025-06-08 1:02 AM
---

I recently migrated to using Linux full time.
You need to not look far to find an ocean of reasons why Windows has been a bit miserable.

This post mainly serves as a logbook for fixes and workarounds for making games (and some applications) work on Linux.

**Note:** This document has a lot of terminal commands and may be unsuitable for screen readers.

[TOC]

## Extreme stuttering after 30-60 minutes on Steam

**Note:** This is apparently fixed in the Steam Client Beta as of June 2nd.

This is apparently due to the recent Steam Game Overlay update which added Game Recording.

You can disable it by prefixing `LD_PRELOAD=""` to your launch arguments:

`LD_PRELOAD="" %command%`

More info on the following issue reports:

- [doitsujin/dxvk#4436](https://github.com/doitsujin/dxvk/issues/4436#issuecomment-2466646597)
- [ValveSoftware/steam-for-linux#11446](https://github.com/ValveSoftware/steam-for-linux/issues/11446)

If you want to load vulkan layers you must add `VK_LOADER_LAYERS_ENABLE` to your launch arguments:

`VK_LOADER_LAYERS_ENABLE="LAYER NAMES" %command%`

Replace `LAYER NAMES` with the layers you wish to load, separated with a comma.

Known Vulkan layer names:

- MangoHud: `VK_LAYER_MANGOHUD_overlay_x86_64`
- OBS VkCapture: `VK_LAYER_OBS_vkcapture_64`
- RenderDoc: `VK_LAYER_RENDERDOC_Capture`

You can view layers present on your system by running `vulkaninfo --summary` (present in the `vulkan-tools` package available in every distro worth using.)

### Alternate Solution

According to [this comment](https://github.com/ValveSoftware/steam-for-linux/issues/11446#issuecomment-2558605371) on [ValveSoftware/steam-for-linux#11446](https://github.com/ValveSoftware/steam-for-linux/issues/11446), disabling GPU acceleration for web views may also help performance related issues.

You disable GPU Web View Acceleration in the Steam settings.

- Navigate to to "Interface" tab
- Uncheck "Enable GPU accelerated rendering in Web Views"
- Restart Steam

## SDL "Failed to Intialize Dependencies" error

(Also applies to EAC, since that uses SDL.)

This is likely due to a `SDL_VIDEODRIVER` and/or `SDL_VIDEO_DRIVER` environment variable being present.

Try using the following launch arguments:

`env --unset=SDL_VIDEODRIVER --unset=SDL_VIDEO_DRIVER %command%`

or

`env SDL_VIDEODRIVER=windows SDL_VIDEO_DRIVER=windows %command%`

Alternatively, set the variable to an empty string in whatever launch manager you're using (Heroic, Lutris).

The EAC splash also sometimes fails to load if you are using the proprietary AMD drivers (i.e. `vk_pro %command%`.)

## Enabling EAC on Wine outside of Proton

***CAVEAT EMPTOR: I do not know if this works long term or if EAC will inevitably cause bans, if possible always prefer to do it via Proton and Steam. This is mostly intended as a guide to help prevent double purchases.***

Here be dragons.

This is assuming the game uses EAC v2 (not v1, if there is an EasyAntiCheat.dll in the game install folder then it's using v1.)

Proton has a few workarounds to load the correct EAC libraries for it to work ([this is what the `PROTON_EAC_RUNTIME` environment variable is for](https://github.com/ValveSoftware/wine/blob/c8391877a485307cb67fecf963af6b855ed39b4b/dlls/ntdll/unix/loader.c#L374)).

You will need to download the Proton EasyAntiCheat Runtime from Steam. I do not know if these libraries depend on Steam or not.

Assuming the Proton runtime exists at: `/home/user/.steam/steam/steamapps/common/Proton EasyAntiCheat Runtime`, and the program you are trying to start is called `nya.exe`:

- For ProtonGE and wine with Proton patches (i.e. wine-tkg), you can simply set the `PROTON_EAC_RUNTIME` environment variable (ProtonGE has a helper that does this automatically.)

`env PROTON_EAC_RUNTIME="/home/user/.steam/steam/steamapps/common/Proton EasyAntiCheat Runtime" proton nya.exe`

- For regular vanilla/staging Wine you can replicate the same behavior as that loader workaround:

```sh
export PROTON_EAC_RUNTIME="/home/user/.steam/steam/steamapps/common/Proton EasyAntiCheat Runtime"
export WINEDLLPATH="${PROTON_EAC_RUNTIME}/v2/lib32/:${PROTON_EAC_RUNTIME}/v2/lib64/"
wine nya.exe
```

**Note:** The client certificate for EAC (`EasyAntiCheat/Certificates/client.bin`) probably needs to accept linux. I do not know the specifics behind this besides that when games enable Linux support this file tends to update so I assume it is related. If the Steam version works on Linux with EAC enabled, but not outside of Steam, then the client certificate likely mismatches and you should ask (somehow, big task) the developers to keep the client certificates in line between Steam and the off-Steam platform.

## Deleting Shader Cache Files

Delete the mesa cache directories, preferrably when mesa isn't running, i.e. terminal session rather than desktop session. **Be careful you do not delete a directory you're not supposed to!**

- `$XDG_CACHE_HOME/mesa_shader_cache`
- `$XDG_CACHE_HOME/mesa_shader_cache_db`
- `$XDG_CACHE_HOME/mesa_shader_cache_sf`

Note: XDG_CACHE_HOME defaults to `$HOME/.cache` on most systems.

You can control where the shader cache is with the `MESA_SHADER_CACHE_DIR` environment variable.

Note: Proton adds `steamapps/shadercache` to the cache path, relative to the library directory. If shader pre-caching is enabled this will always be populated, but may have directories for games that are no longer installed. Check if a related appmanifest_{id}.acf file is present in the upper directory.

You may also need to delete one or two files that reside in the same location as the executable. Some or none may exist.

- `vkd3d-proton.{ExecutableName}.cache`
- `vkd3d-proton.{ExecutableName}.cache.write`
- `{ExecutableName}.dxvk-cache`

You can control where the cache files are saved with the `DXVK_STATE_CACHE_PATH` and `VKD3D_SHADER_CACHE_PATH` environment variables, i.e. I have the following in my dotfiles.

```sh
export VKD3D_SHADER_CACHE_PATH="$HOME/.cache/vkd3d"
export DXVK_STATE_CACHE_PATH="$HOME/.cache/dxvk"
```

Note: I personally use these environment variables, as steam will not delete these cache files which may slowly rot your storage medium with leftover cache files. Where these distinct directories can easily be cleaned.

## Checking if EAC is linux-enabled

Most EAC games ship with a Settings.json file, this tells the EAC runtime what deployment and product to use.
This information is all logged in AppData, but the settings file exists in the game installation. 
This is usually next to the installer (`EasyAntiCheat/Settings.json`, or next to the game executable but usually in the `EasyAntiCheat` directory inside of the game directory)

We can use this to find out if EAC is enabled for a particular game.

```sh
jq -r \
	'@uri "https://modules-cdn.eac-prod.on.epicgames.com/modules/\(.productid)/\(.deploymentid)/linux64"' \
	Settings.json
```

This will print out a URL. If the url yields HTTP 403, EAC Linux is disabled. If it returns HTTP 200, it is enabled.

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

`gamescope --force-grab-cursor -f -- %command%`

You may swap -f with -b for borderless windowed instead of fullscreen.

## Windows-only Third-Party Mod Tooling on Steam

You can add the mod tools as a non-steam game, given it has a GUI.

When you do, force it to use **the same compatability tools as the game** and set the launch arguments to:

`env STEAM_COMPAT_DATA_PATH="~/.steam/root/steamapps/compatdata/489830" %command%`

You may need to install more dependencies like .NET 4.8/6.0, etc via protontricks, select the game *not* the non-steam app when installing.

Change `~/.steam/root/steamapps` to the SteamLibrary steamapps directory if installed in a steam library directory.

Change 489830 to match the steam id of the mod tool the game is for, 489830 is Skyrim SE/AE.
It is the number after `/app/` in the Steam store link, alternatively look it up on SteamDB.

## Gamescope

### Gamescope exiting early due to short-lived launcher processes

Some games launch via third party launchers that cause gamescope to exit before the wine device.

This may be solved by forcing the SDL backend.

`gamescope --backend sdl -- %command%`

### Gamescope resolution being fixed to the first window size under SDL

Gamescope under SDL has a hard time adjusting to resolution changes (i.e. if you're using it for launcher processes.), to solve this you must force the window to be fullscreen.

`gamescope -w YOUR_RESOLUTION_HERE -h YOUR_RESOLUTION_HERE -r YOUR_REFRESH_RATE_HERE --backend sdl --force-windows-fullscreen -f -- %command%`

(Special thanks to [Hollyrious](https://twitch.tv/hollyrious) for helping me diagnose this!)

### Gamescope and Steam

Gamescope might break steam ingration or just exit, in that case add ` -e ` to the end of your command. Also ensure that ` -- ` (with spaces) exists ***before*** `%command%`

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

`vk_pro ~/.steam/steam/steamapps/common/SteamVR/bin/vrmonitor.sh %command%`

### WMR

Windows Mixed Reality is [deprecated by Microsoft, and support will be removed in November 2026](https://learn.microsoft.com/en-us/windows/whats-new/deprecated-features#deprecated-features).
This makes Monado on Linux the only way to still use the device.

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

## AMDGPU-Pro

### Gamescope

AMD's proprietary drivers does not implement an extension that Gamescope relies on, which results in Gamescope crashing (See [this issue on GameScope's repository.](https://github.com/ValveSoftware/gamescope/issues/1465))

You can avoid this by moving the `amd_pro_icd64.json` file (`/usr/share/vulkan/icd.d/amd_pro_icd64.json`) to a different path (i.e. `/usr/share/vulkan/icd.disabled/amd_pro_icd64.json`)

And then modifying your `vk_pro` wrapper script to point to the new path. When needed, prefix `vk_pro` to whatever command needs proprietary AMD drivers.

You can find [vk_pro](https://gitweb.gentoo.org/repo/gentoo.git/tree/media-libs/amdgpu-pro-vulkan/files/vk_pro) and [vk_radv](https://gitweb.gentoo.org/repo/gentoo.git/tree/media-libs/amdgpu-pro-vulkan/files/vk_radv) wrapper scripts provided by Gentoo, but they likely are also provided by other distros.

Gamescope seems to ignore the `VK_DRIVER_FILES`, `VK_ICD_FILENAMES`, `VK_LOADER_DRIVERS_DISABLE`, and `VK_LOADER_DRIVERS_SELECT` environment variables.

## Battle.net

### BLZBNTBNA00000005 / Sleeping Battle.net Agent

Also applies to if Battle.net spams the "broken installation please restart" popup.

This is due to a security change in Battle.net which verifies if the calling process is signed by Blizzard and trusted. 
Wine 9 and earlier seem to incorrectly implement the WinTrust/WinCrypt functions, however Wine 10 does exhibit proper behavior.

Try switching to Wine 10 or Proton 10 and restarting the process.

## Game-Specific Fixes

### Monster Hunter Wilds

#### Monster Hunter World Save Bonuses

If the game can't seem to locate the save bonuses for having a valid Monster Hunter World save, you need to copy the saves to the correct prefix.

The save files are stored on the steam cloud, if you have played the game on the machine before they will be in `~/.steam/steam/userdata/[YOUR STEAM ID]/582010/`.
If this directory does not exist ensure that steam cloud saves are enabled on Monster Hunter World, download it and lauch it completely once. Steam should have downloaded the save files.
You must copy **that entire directory** to the prefix-appropriate userdata directory. This is located in the same storage medium as the game.

The related path is: `/path/to/installed/SteamLibrary/steamapps/compatdata/2246340/pfx/drive_c/Program Files (x86)/Steam/userdata/[YOUR STEAM ID]`

So for example, if your Steam ID is 1024, and you have installed it to a partition that is mounted on /mnt/games/ you would do the following in a command prompt:

```sh
cp -rfvn "~/.steam/steam/userdata/1024/582010" "/mnt/games/SteamLibrary/steamapps/compatdata/2246340/pfx/drive_c/Program Files (x86)/Steam/userdata/1024/"
```

The next time Monster Hunter Wilds launches, you should get a prompt for the Monster Hunter World incentives.

#### Shader compilation on every startup

It would appear that in some situations, the game will compile shaders every time it has been started.

The following environment variables are shown to remove or at least reduce the instances of this happening significantly:

`MESA_DISK_CACHE_SINGLE_FILE=0 __GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1`

### Dauntless

This game has quite a lot of issues with Wine and Proton.

#### If you randomly crash, it might be because of stack smashing due to a race condition.

I have managed to reduce the frequency of crashes by limiting how many resources the game can use.

`env DXVK_CONFIG="dxvk.numCompilerThreads=1" WINE_CPU_TOPOLOGY="4:0,2,4,6" %command%`

#### If there is too much lag from the above fix.

You might want to redefine the CPU topology, i.e. `WINE_CPU_TOPOLOGY="8:0,1,2,3,4,5,6,7"`

#### If you get a "Game Security Integrity Violation" error from EAC.

Set the SteamDeck environment variable:

`env SteamDeck=1 %command%`

#### If you get a "Hash Catalog Not found" error from EAC.

Copy `EasyAntiCheat` from the game's install directory to the `Archon/Binaries/Win64` sub-directory.

#### If you get what seems to be a [test card](https://en.wikipedia.org/wiki/Test_card) instead of the opening video

Try using Proton Experimental or a different version of Proton.

### Horizon Zero Dawn: Remastered

If you crash upon start, and have multiple displays it's likely due ot mismatched display resolutions.

This can be solved by using gamescope:

`gamescope -w YOUR_RESOLUTION_HERE -h YOUR_RESOLUTION_HERE -r YOUR_REFRESH_RATE_HERE --backend sdl --force-windows-fullscreen -f %command%`

If the game complains about "no internet connection" upon start: add

`%command% -showlinkingqr`

to the command options.

### Bloodborne (via shadPS4 with patches)

If you load in to the game and the world geometry is missing/textures are horrid, it's likely because the GPU drivers lack a certain extension set. In my experience running shadPS4 with AMD's proprietary drivers (i.e. `vk_pro shadps4`) resolves this.

If you start the game to a black screen follow the steps [outlined in this github issue](https://github.com/shadps4-emu/shadPS4/issues/1409#issuecomment-2423382148).

If you *still* get a black screen, delete the shadPS4 directory in .local/share/shadPS4 and **launch the Qt6 GUI and configure your settings and launch the game via the GUI**. (I have no idea why this works.)

### Marvel Rivals

As of Season 1 of Marvel Rivals (January 2024) the game skips the launcher and most modals if `SteamDeck=1` is passed as an launch argument. This may also resolve any startup crashes or weirdness.

### AFK Journey

Some games display a terms of service or login web view modal on the first launch, however the input window may be detatched from the renderer frame.

If you use a tiled window manager and see a black square, this is the input frame.

If you do not see a black square but the web view is not accepting inputs, the black square is likely beneath this window.

Locate both frames and approximate the button locations using the render frame on the black frame.

## Changelog

- *Update: 2025-06-08 - Added EAC Outside of Proton*
- *Update: 2025-06-02 - Added Steam Input Lag Note*
- *Update: 2025-05-31 - Shader Cache*
- *Update: 2025-05-08 - Battle.net eepy agent*
- *Update: 2025-04-09 - Monster Hunter Wilds GPU Crash is fixed in dxvk*
- *Update: 2025-04-04 - Monster Hunter Wilds GPU Crash is real, unfortunately*
- *Update: 2025-03-31 - Added Monster Hunter Wilds GPU Crash pre-emptive workaround*
- *Update: 2025-03-03 - Added Monster Hunter Wilds Shader compilation workaround*
- *Update: 2025-03-03 - Added Monster Hunter Wilds/World incentives guide*
- *Update: 2024-12-12 - Added Steam Game Recording workaround*
- *Update: 2024-12-12 - Added Marvel Rivals / AFK Journey CEF frame note*
- *Update: 2024-12-06 - Added even more Dauntless workarounds*
- *Update: 2024-11-27 - Added method to verify if EAC is enabled*
- *Update: 2024-11-13 - Added double dashes to Gamescope commands*
- *Update: 2024-11-03 - Added Bloodborne emulation notes*
- *Update: 2024-11-03 - Added AMDGPU-Pro notes*
- *Update: 2024-10-31 - Added Horizon Zero Dawn: Remastered notes.*
- *Update: 2024-10-29 - Added note about proprietary drivers and EAC*
- *Update: 2024-10-29 - Added Monado/SteamVR*
- *Update: 2024-09-22 - Added gamescope-related workarounds*
