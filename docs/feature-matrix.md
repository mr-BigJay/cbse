# Feature Matrix — Standard vs Managed Device Owner

| Feature | Standard Mode | Managed (Device Owner) | UI capability state |
|---------|---------------|------------------------|------------------------|
| Device status / battery | Supported | Supported | Supported and ready |
| Periodic heartbeat | Supported (WorkManager) | Supported | Supported and ready |
| Location (foreground) | Requires permission + consent | Policy-dependent | Requires permission / Requires user confirmation |
| Location (background) | Requires background location permission | Device Owner may enable via policy | Requires permission |
| Find-device alarm | Supported (visible alarm) | Supported | Supported and ready |
| Device lock | Device Admin or user confirmation where API allows | DevicePolicyManager lock | Requires permission / Requires Device Owner |
| Installed app inventory | Package visibility limits | Broader on DO | Requires permission |
| App suspend / hide | Not available | Device Owner | Requires Device Owner |
| App uninstall (managed) | User-confirmed intent | Managed workflows | Requires user confirmation |
| Account sync status | Settings navigation only | Limited API surface | Unsupported / Requires user confirmation |
| Account management | Open system settings | User-approved flows | Requires user confirmation |
| SMS STATUS/LOCATE/ALARM/LOCK | Same permission gates as HTTPS | Same | Supported with SMS config |
| Factory reset / wipe | Not in MVP | Policy-only, not via SMS | Unsupported in v1 |
| Remote camera / mic | Not supported | Not supported | Unsupported |

Dashboard never marks an action successful until the agent reports `completed` with matching command id.
