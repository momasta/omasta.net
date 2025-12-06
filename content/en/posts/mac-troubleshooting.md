---
date: 2025-12-03T21:36:09+01:00
lastmod: 2025-12-06T13:39:46+01:00
title: "Mac Troubleshooting"
draft: false
description: ""
summary: ""
keywords: 
  - guide
  - tutorial
  - tips
  - macOS
  - MacBook
  - terminal commands
  - how to fix
main_content_id: "app-isnt-responding"
slug: ""
tags:
  - tips
translationKey: ""
type: posts
---

Since I got my first Mac in May 2023, I've been taking notes of every solution that's helped me fix issues.

Usually, it's just the matter of killing a&nbsp;process.  
They kick back in by themselves, as&nbsp;needed.   
No need to restart the whole system most of the time.

If you prefer, instead of running "killall" commands in Terminal,  
you can find and select the process in Activity Monitor, and hit the Stop button.

* **⎋** = Escape key
* **⌃-click** = right click or a two-finger click on your Trackpad

{{< TableOfContents >}}

## App Isn't Responding
* **⌥⌘⎋:** [Force Quit](https://support.apple.com/en-us/102586 'How to force an app to quit on Mac - Apple Support')  
* Select the app
* Click Force Quit

More details: [How to force an app to quit on Mac - Apple Support](https://support.apple.com/en-us/102586 'How to force an app to quit on Mac - Apple Support')

## App Store not showing updates
* Press **⌘R** to reload

## Apple Music: Clean Cache
```
rm -rf ~/Library/Caches/com.apple.iTunes/CommerceRequestCache/*

```

## Everything’s Frozen
* **⌥⌘⎋:** [Force Quit](https://support.apple.com/en-us/102586 'How to force an app to quit on Mac - Apple Support')  
* Run over SSH from another device:
* Sort processes by CPU usage:
  ```
  top -u
  ```
* Kill the most power-hungry process.  
* If that doesn't help:
  ```
  killall WindowManager
  
  ```
* Alternatively:
  ```
  sudo killall -HUP WindowServer
  
  ```
* Press and hold the **Power&nbsp;Button**
* Press and hold **⌃⌘–Power&nbsp;Button**

## External drive won't show up in Disk Utility
HDD, SSD, USB thumb drive

When the "Allow accessory to connect?" prompt flashes briefly,  
not allowing you to press anything:

* Open [Privacy & Security](x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension "Open System Settings – Privacy & Security")
  * Scroll down to Security
  * Click Accessories
  * Select "Automatically allow when unlocked"

⚠️ **Warning:**
* Make sure to **revert this setting** to its original value afterwards.
* Only allow devices you trust, such as your own drives.

## Find processes that are using an external drive
To find out which app or process is preventing you from ejecting a drive:
```
sudo lsof | grep /Volumes/HDD

```

Your drive is likely gonna have a path than mine, /Volumes/HDD.  
To find out its path:
* Open Finder
* **⌃-click** the drive in the sidebar
* Click Get Info

## Finder
### iCloud Drive Sync Stuck
```
sudo killall bird

```

### iPhone Sync Stuck
```
killall AMPDevicesAgent && killall MDCrashReportTool

```

### File Verification Stuck
```
killall CoreServicesUIAgent

```

### Finder Won’t Find Multiple Keywords
* Wrap with quotes

### Finder Won’t Remember Window Position and Size
* Position and resize the window
* **⌥⌘⎋:** [Force Quit](https://support.apple.com/en-us/102586 'How to force an app to quit on Mac - Apple Support')  
* Select Finder  
* Click Relaunch  

### Force App to Open Any File
* Hold **⌥⌘** while dragging the file

## Fix Audio
```
sudo killall coreaudiod

```

## Fix Encoding of Accented Letters in Filenames
Unicode, convert NFD to NFC
* Requires Homebrew
  * Follow their [installation instructions](https://brew.sh 'Homebrew — The Missing Package Manager for macOS (or Linux)')
  * Don't overlook post-install instructions printed in Terminal.
    ```
    brew install convmv
    
    ```
  * convmv is also available on [MacPorts](https://ports.macports.org/port/convmv/ 'Install convmv on macOS with  MacPorts') if that's your thing.

To fix filenames of every file in the current directory, run:
```
convmv -r -f utf8 -t utf8 --nfc --notest .

```

## Notes: Edited Links not Matching Their Titles
* Font → Remove Style
* Select all
* **⌃-click**, Substitutions, Add Links (not available in the Menu Bar)

## Reset Dock to Default Size
```
defaults write com.apple.dock "tilesize" -int "64" && killall Dock

```  
## Restart macOS UI Elements
### Restart Dock
```
launchctl stop com.apple.Dock.agent && launchctl start com.apple.Dock.agent

```

### Restart Menu Bar Icons
Stuck Shortcuts Icon
```
killall ControlCenter

```

### Restart Quick Look
```
qlmanage -r

```

### Restart Spotlight
```
sudo killall -KILL&nbsp;Spotlight&nbsp;spotlightd mds

```
* **⌥⌘⎋:** [Force Quit](https://support.apple.com/en-us/102586 'How to force an app to quit on Mac - Apple Support')  
* Select Finder  
* Click Relaunch    
### Stuck Alarm/Timer Sound
Clock app, countdown, ringtone.
```
killall NotificationCenter

```

### Other UI Elements
```
killall -KILL SystemUIServer

```
* **⌥⌘⎋:** [Force Quit](https://support.apple.com/en-us/102586 'How to force an app to quit on Mac - Apple Support')  
* Select Finder  
* Click Relaunch  

## Safari: iCloud Tabs Won’t Sync or Close
Stuck ghost/zombie/phantom tabs from other devices.

* Quit Safari
```
rm ~/Library/Containers/com.apple.Safari/Data/Library/Safari/CloudTabs.db*

```

## Spotlight: List Excluded Folders
The list under [Spotlight Settings](x-apple.systempreferences:com.apple.Spotlight-Settings.extension "Open System Settings – Spotlight") / Search Privacy only shows folder names.  
That can be confusing with many arbitrary short names in a row.

To see full paths, you'd have to hover the mouse over each of them.  
Cumbersome.

Instead, you can get a list of full paths with the following command:
```
sudo /usr/libexec/PlistBuddy -c "Print :Exclusions" /System/Volumes/Data/.Spotlight-V100/VolumeConfiguration.plist

```

## Spotlight: Reindex
Rebuild Indexes, indexing, mdfind

If certain files or items won't show up in Spotlight or Finder search results, simply restart your Mac.

No matter how many processes you kill or how hard you try,  
Spotlight's just gonna sit there, refusing to reindex.

### Option 1
* Restart

### Option 2
* Open [Spotlight Settings](x-apple.systempreferences:com.apple.Spotlight-Settings.extension "Open System Settings – Spotlight")
* Scroll to the bottom
* Click Search Privacy…
* Add the location
* Remove the location
* Restart

### Option 3
```
sudo mdutil -a -i off
sudo rm -rf /.Spotlight*
sudo mdutil -a -i on
sudo mdutil -E /

```
* Restart
* To check progress:  
* **⌘**⎵: Open Spotlight
* Type "." or any random term into it.  
* If it's reindexing, you should see a little progress bar right under the search field.  
