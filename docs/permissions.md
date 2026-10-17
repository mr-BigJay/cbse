# Android Permissions and Restrictions

## Standard Mode

| Permission / capability | Purpose | When requested |
|-------------------------|---------|----------------|
| `INTERNET` | API communication | Install |
| `ACCESS_FINE_LOCATION` / `COARSE` | Locate commands | After consent |
| `ACCESS_BACKGROUND_LOCATION` | Background locate | Separate disclosure (Android 10+) |
| `POST_NOTIFICATIONS` | FCM (Android 13+) | Runtime |
| `RECEIVE_BOOT_COMPLETED` | Reschedule WorkManager | Install |
| `FOREGROUND_SERVICE` + type `location` | Active locate session | When locating |
| `USE_BIOMETRIC` / credentials | Optional app lock for agent UI | Settings |
| `READ_PHONE_STATE` | Optional device identifiers (minimal) | If enabled |
| `RECEIVE_SMS` / `READ_SMS` | SMS command channel | User enables SMS fallback |
| Device Admin | Lock device | User accepts admin activation |

## Managed Device Owner

Provisioning via Android Enterprise (QR code from `docs/installation.md`). Requires factory reset or new device for fully managed mode on most OEMs.

Device Owner enables: `DevicePolicyManager.setPackagesSuspended`, lock task, password policies, some location policies. Does **not** grant unrestricted access to personal Google account credentials.

## Google Play

SMS receive permissions face Play policy scrutiny; self-hosted APK sideload is documented for administrators. Declare all permissions in Play Console if publishing.

## Package visibility (Android 11+)

Installed-app inventory uses `<queries>` for common patterns; full list requires Device Owner or user-granted usage access (not requested in MVP by default).
