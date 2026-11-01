# Android deployment (Google Play)

This guide covers every step from a fresh Mac to a published game on Google Play: tools, testing on a phone, signing,
store listing and updates.

## How it works

The game is still one HTML file. [Capacitor](https://capacitorjs.com/) wraps it in a small Android app: the app is a
full-screen WebView that loads `www/index.html` from inside the APK, so it works offline and needs no server.
Scores, coins and ships stay in the WebView's `localStorage`, on the phone.

| File | Role |
|---|---|
| `www/index.html` | The game. Edit this one. |
| `index.html` (root) | Copy for GitHub Pages during the transition (`mise run site:copy`). Don't edit it. |
| `mise.toml` | Tools (Node, JDK, Android SDK) and the build tasks. |
| `package.json` | Capacitor npm packages. |
| `capacitor.config.json` | App id `com.ebuildy.substrike`, app name, `webDir: www`. |
| `android/` | The Android Studio / Gradle project. |
| `android/app/src/main/java/com/ebuildy/substrike/MainActivity.java` | Full screen and the Back button. |
| `android/app/src/main/AndroidManifest.xml` | Landscape lock (`sensorLandscape`). |
| `android/app/build.gradle` | `versionCode` / `versionName` and release signing. |
| `android/keystore.properties` | Upload key settings. **Not in git.** |

What the app adds to the web game:

- **Landscape only.** On large tablets Android 16 may ignore the lock; the game's own "rotate" screen still covers it.
- **Immersive full screen.** The status and navigation bars are hidden; a swipe from the edge shows them for a moment.
- **Back button:** pauses during a mission, resumes from the pause screen, leaves the armory. On any other screen the
  app goes to the background (it does not quit, so progress is kept).
- The touch controls are the game's own mobile mode (`MOBILE`): the WebView reports a touch screen.

## Step 1. Install the tools (once per Mac)

1. Install [mise](https://mise.jdx.dev/) if needed: `brew install mise`, then follow its shell activation
   instructions.
2. From the repo root:

   ```sh
   mise trust            # allow this repo's mise.toml
   mise install          # Node 24, Java (Temurin 21), Android command-line tools
   mise run android:sdk  # Android SDK: platform-tools, Android 16 (API 36), build-tools 36
   npm install           # Capacitor packages
   ```

3. Check:

   ```sh
   mise exec -- node -v                 # v24.x
   mise exec -- java -version           # 21.x
   ls ~/Library/Android/sdk/platforms   # android-36
   ```

The SDK lives in `~/Library/Android/sdk` (`ANDROID_HOME`, set by `mise.toml`). Android Studio is optional; if you
install it, it uses the same SDK.

> `sdkmanager` prints a deprecation warning pointing to the new `android sdk` command. It still works.

## Step 2. Build and try it on a phone

### Prepare the phone (once)

1. On the phone: **Settings > About phone**, tap **Build number** 7 times. Developer options are now on.
2. **Settings > System > Developer options**, turn on **USB debugging**.
3. Plug it in with a USB cable and accept the "Allow USB debugging?" prompt on the phone.
4. Check that it is seen:

   ```sh
   ~/Library/Android/sdk/platform-tools/adb devices   # one line ending with "device"
   ```

### Run the game on it

```sh
mise run android:run
```

This copies `www/` into the app (`android:sync`), builds a debug version, installs it and starts it. Pick the phone
if several devices are listed.

### Or install the APK by hand

```sh
mise run android:apk
# -> android/app/build/outputs/apk/debug/app-debug.apk
~/Library/Android/sdk/platform-tools/adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

You can also send `app-debug.apk` to a phone (mail, Drive) and open it there; Android asks to allow installs from
that app.

### Without a phone: emulator (optional)

The easiest way is Android Studio: `npx cap open android`, then **Device Manager > Create device**, pick a phone with
an Android 16 image, and start it. `mise run android:run` then lists the emulator as a target.

### Debug the game inside the app

Debug builds let Chrome inspect the WebView: with the phone plugged in and the game running, open
`chrome://inspect` in Chrome on the Mac and click **inspect** under the game. You get the console and DevTools,
like for the web version.

### What to test on the phone

- [ ] It opens in landscape, full screen, no status bar.
- [ ] Sound plays after the first tap.
- [ ] Stick and buttons (FIRE, H-BOMB, DECOY, BUBBLE, pause).
- [ ] Back during a mission pauses; Back again resumes; Back in the armory returns; Back on the title screen sends
      the app to the background.
- [ ] Leaving the app (home button) during a mission pauses it.
- [ ] Progress survives: pass mission 1, close the app (swipe it away), reopen: it starts at mission 2.

## Step 3. Day-to-day changes

1. Edit `www/index.html` and test it in a browser as usual (`open www/index.html`).
2. `mise run site:copy` to refresh the root `index.html` that GitHub Pages serves. **Do it before every commit.**
3. `mise run android:run` to see it on the phone (it runs `site:copy` and the sync itself).

## Step 4. Create the upload key (once)

Google Play needs every upload to be signed with your **upload key**.

```sh
mise run android:keystore
```

It asks for a password (6 characters or more), then creates:

- `~/.android-keys/substrike-upload.jks`, the key itself, outside the repo;
- `android/keystore.properties`, the settings Gradle reads (path, alias `upload`, password). Ignored by git.

**Back up both** (password manager, encrypted drive). Never commit them.

With **Play App Signing** (on by default for new apps), Google keeps the real app signing key and your upload key
only proves that an upload comes from you. If the upload key is lost or leaked, you can ask Google to reset it from
Play Console (**Test and release > Setup > App signing**). That takes a few days, so keep the backup.

## Step 5. Set the version

In `android/app/build.gradle`:

```gradle
versionCode 1        // whole number, must go up for EVERY upload to Play (1, 2, 3...)
versionName "1.0"    // shown to players (1.0, 1.1, 2.0...)
```

Play refuses an upload whose `versionCode` was already used, even on a test track.

## Step 6. Build the release bundle

```sh
mise run android:bundle
# -> android/app/build/outputs/bundle/release/app-release.aab
```

Play only accepts `.aab` (Android App Bundle), not APK. The task stops if there is no upload key (step 4).

To check the signature:

```sh
mise exec -- jarsigner -verify -verbose:summary android/app/build/outputs/bundle/release/app-release.aab | tail -3
```

## Step 7. Create the Google Play developer account (once)

1. Go to <https://play.google.com/console> and sign in with the Google account that will own the game.
2. Pick an account type:
   - **Personal:** for an individual. Cheaper and faster to set up, but see the testing rule in step 10.
   - **Organization:** for a company. Needs a [D-U-N-S number](https://www.dnb.com/duns.html) (free, can take
     days to weeks), and skips the 12-tester rule.
3. Pay the one-time **US$25** registration fee.
4. Verify your identity (ID document, address, phone). Google also checks the developer contact email and may ask
   you to verify that you have a real Android device (Play Console app). Verification can take a few days.

## Step 8. Create the app in Play Console

**Home > Create app**:

| Field | Value |
|---|---|
| App name | Battle Beneath the Sea (30 characters max) |
| Default language | English (United States) |
| App or game | Game |
| Free or paid | Free (a free app can never become paid later) |
| Declarations | Accept the Developer Program Policies and US export laws |

Then the **Dashboard** lists the tasks to finish. They are below.

## Step 9. Fill in the app content and store listing

### 9.1 Privacy policy (required)

Play needs a public URL: `https://ebuildy.github.io/sub-strike/privacy.html` (`www/privacy.html`, copied to the
root by `mise run site:copy`). It says the only data collected is the player name and score posted to the online
leaderboard, plus the mission reached and the date. Its contact is the GitHub issues page (no email, to avoid spam). If the leaderboard changes (more fields, a login), update the page and the Data safety form.

Enter it under **Policy and programs > App content > Privacy policy**.

### 9.2 App content declarations

All under **Policy and programs > App content**:

| Section | Answer for this game |
|---|---|
| App access | All functionality is available without special access (no login). |
| Ads | No, the app does not contain ads. |
| Content rating | Fill in the IARC questionnaire: category Game, answer the violence questions honestly (military vehicles and creatures destroyed, explosions, no blood). Expect about PEGI 7 to 12 / ESRB E10+ to T. |
| Target audience | 13 and over (or 18 and over). Do **not** include ages under 13: that triggers the Families policy and its extra rules. |
| Data safety | See 9.2.1 below. |
| Government app | No. |
| Financial features | None. |
| Health | None. |
| News app | No. |

#### 9.2.1 Data safety form (online leaderboard)

It must match `privacy.html` and what the app really sends:

| Question | Answer |
|---|---|
| Does your app collect or share any of the required user data types? | Yes |
| Is all of the user data encrypted in transit? | Yes (HTTPS) |
| Do you provide a way for users to request that their data is deleted? | Yes: a GitHub issue (the privacy policy's contact) |
| Data types | **Personal info > Name** (the player name), and **App activity > Other user-generated content** (the score) |
| For each: collected / shared | Collected. Not shared (a processor that stores data for you does not count as sharing) |
| Processed ephemerally? | No |
| Required or optional? | Optional: players can play without posting a score |
| Purpose | App functionality (the leaderboard) |

The `INTERNET` permission in the manifest (added by Capacitor) is what the leaderboard needs.

### 9.3 Store listing

**Grow users > Store presence > Main store listing**:

| Item | Spec |
|---|---|
| App name | 30 characters max |
| Short description | 80 characters max, e.g. "Command a French attack sub. Torpedoes, laser, CIWS. Mines, drones, bosses." |
| Full description | 4000 characters max: missions, weapons (one key per action), threats, bosses, no ads |
| App icon | 512 x 512 PNG (32-bit, alpha allowed), up to 1 MB |
| Feature graphic | 1024 x 500 JPG or 24-bit PNG (no transparency) |
| Phone screenshots | 2 to 8, PNG or JPG, 16:9 landscape works well (e.g. 1920 x 1080) |
| Tablet screenshots | Optional, but needed to be featured on tablets (7" and 10") |
| Category | Game > Action (or Arcade) |
| Contact email | Required by Play and shown on the store page. To avoid spam on your main address, use a separate one (e.g. a new Gmail or an alias) only for the game. A website (the GitHub repo) can be added too. |

Screenshots: take them on the phone (power + volume down) during a mission, or from the browser version with the
canvas at 1600 x 900. The existing `docs/game1.png` and `docs/game2.png` are a start.

### 9.4 Launcher icon (in the app)

The app still has Capacitor's default icon. To replace it:

1. Make a 1024 x 1024 PNG of the icon (no text, the sub on a dark sea background) as `assets/icon-only.png`.
   Optionally, also add `assets/icon-foreground.png` and `assets/icon-background.png` (adaptive icon layers), and
   `assets/splash.png` (2732 x 2732).
2. Generate every Android size:

   ```sh
   npx @capacitor/assets generate --android
   ```

3. Rebuild and check it on the phone's home screen.

Android Studio can do the same: right-click `android/app/src/main/res` > **New > Image Asset**.

## Step 10. Test tracks, then production

Play has 3 test tracks before production: **internal testing** (up to 100 testers, no review, live in minutes),
**closed testing** (invited testers, reviewed) and **open testing** (anyone can join).

### 10.1 Internal test (recommended first)

1. **Test and release > Testing > Internal testing > Testers:** create an email list (yourself and a few friends).
2. **Create new release**, upload `app-release.aab`, add release notes ("First build"), **Save**, **Review
   release**, **Start rollout**.
3. Copy the **join link**, open it on the phone with a tester account, accept, then install from the Play Store.

### 10.2 Closed test (required for personal accounts)

New **personal** developer accounts must run a closed test with **at least 12 testers who stay opted in for 14 days
in a row** before they can apply for production. Organization accounts skip this.

1. **Testing > Closed testing > Create track** (or use the default "Alpha"), add a testers email list or a Google
   Group with at least 12 people.
2. Upload a release (new `versionCode`), send the join link to the testers.
3. Each tester must accept the invitation **and install the game**, and stay in for 14 days. Ask them to play it
   and send feedback: Google asks about the test when you apply.
4. After 14 days, **Dashboard > Apply for production** and answer the questions about the test (how many testers,
   what feedback, what you changed). Google answers in about 7 days.

### 10.3 Production

1. **Test and release > Production > Countries/regions:** pick where the game is available (or all).
2. **Create new release**, upload the `.aab` (or promote the tested release), release notes, **Start rollout**.
3. The first review usually takes a few days (up to about 7). You get an email when the game is live.

You can start with a **staged rollout** (for example 20% of users) and raise it once there are no crashes.

## Step 11. Publish an update

1. Change and test the game (step 3).
2. Bump `versionCode` (+1) and, if you like, `versionName` in `android/app/build.gradle` (step 5).
3. `mise run android:bundle`.
4. Play Console: **Production** (or a test track first) > **Create new release**, upload, release notes, rollout.
5. Commit the change (`www/index.html`, root `index.html`, `build.gradle`).

Players get it through Play Store updates, usually within a day.

## Step 12. Keep the app accepted

- **Target API level:** Google raises the minimum target SDK every year (usually by the end of August). Play Console
  warns months before. To follow it: install the new platform (`sdkmanager "platforms;android-NN"
  "build-tools;NN.0.0"`, and update the `android:sdk` task), update Capacitor (`npm install @capacitor/core@latest
  @capacitor/cli@latest @capacitor/android@latest`, then `npx cap sync android`), raise `compileSdkVersion` and
  `targetSdkVersion` in `android/variables.gradle`, rebuild and test.
- **Policy emails:** Play sends warnings to the account email; answer them before the deadline or the app can be
  removed.
- **Android vitals** (Play Console > Monitor and improve) shows crashes and ANRs from players' phones.

## Troubleshooting

| Problem | Fix |
|---|---|
| `SDK location not found` | Run the build through mise (`mise run ...`) so `ANDROID_HOME` is set, or create `android/local.properties` with `sdk.dir=/Users/<you>/Library/Android/sdk`. |
| `Unsupported class file major version` / Gradle wants another JDK | Use mise's JDK 21: `mise exec -- java -version`. Run Gradle through `mise run`. |
| `adb devices` shows `unauthorized` | Unlock the phone and accept the USB debugging prompt; or revoke authorizations in Developer options and replug. |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | A build signed with another key is installed (for example the Play version). Uninstall it from the phone first. |
| Old game version in the app | Run `mise run android:sync` (the tasks do it); then rebuild. |
| No sound | Tap the screen once: Web Audio starts only after a user gesture. Check the phone is not in silent mode for media. |
| Play: "Version code 1 has already been used" | Bump `versionCode` (step 5). |
| Play: "You uploaded an APK or Android App Bundle that was signed in debug mode" | Build with `mise run android:bundle`, not `android:apk`, and check `android/keystore.properties` exists. |
| Play: target API level too low | See step 12. |

## Checklist

- [ ] Tools installed (`mise install`, `mise run android:sdk`, `npm install`)
- [ ] Tested on a real phone (step 2 list)
- [ ] Launcher icon replaced
- [ ] Upload key created and backed up
- [ ] `versionCode` bumped
- [ ] `app-release.aab` built
- [ ] Play developer account verified
- [ ] Privacy policy page online (leaderboard live)
- [ ] App content declarations done
- [ ] Store listing: icon, feature graphic, screenshots, descriptions
- [ ] Internal test installed from the Play Store
- [ ] Closed test: 12 testers for 14 days (personal account)
- [ ] Production release rolled out
