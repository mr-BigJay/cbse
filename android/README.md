# ARDM Android Agent

Kotlin + Jetpack Compose companion app for self-hosted ARDM.

## Build

1. Open `android/` in Android Studio Ladybug or newer.
2. Sync Gradle and build **Build → Build Bundle(s) / APK(s) → APK**.
3. Install on a device you own or have enrolled with consent.

## Enrollment

1. Enter HTTPS server URL (same as Caddy `DOMAIN`).
2. Enter one-time enrollment code from the admin dashboard.
3. Wait for administrator approval, then allow requested permissions.

## Device Admin (Standard lock)

Use **Enable lock (Device Admin)** before `LOCK` commands succeed.

## Managed Device Owner

For full policy control, provision as Device Owner via Android Enterprise QR during setup (factory reset usually required). Set `mode` to `managed` during registration (future UI toggle).

## Firebase Cloud Messaging (optional)

1. Add `com.google.gms.google-services` plugin and `firebase-messaging` dependency.
2. Implement `ArdmFirebaseMessagingService` to call `CommandProcessor.processPending()` on wake.
3. Never put command payloads in the FCM notification body.

## SMS fallback

Configure authorized sender numbers in the app. Commands:

`ARDM v1:STATUS:1730000000:nonce:hexhmac`

HMAC-SHA256 key is the `sms_secret` shown once at enrollment.

## Tests

```bash
./gradlew test connectedAndroidTest
```
